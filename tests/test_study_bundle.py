import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from flock.analysis.bundle import (
    CORE_ARTIFACTS,
    analyze_study_bundle,
    reproduce_study_bundle,
    verify_study_bundle,
)
from flock.analysis.study import StudyInference
from flock.experiments.verify import RunVerification


def _manifest(block: str, trajectory: str, *, model: str = "dated-model", seed: int = 1):
    return {
        "run_id": f"run-{block}",
        "status": "complete",
        "config": {
            "independent_block": block,
            "dependence_cluster": f"cluster-{block}",
            "trajectory_id": trajectory,
            "seed": seed,
        },
        "dataset": {"sha256": "a" * 64},
        "agents": {"agent-1": {"kind": "llm", "model_id": model}},
    }


def _source(
    root: Path,
    manifests: list[dict],
    *,
    evidence_kind: str = "real",
    status: str = "complete",
    preregistration: dict | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    run_dirs = []
    blocks = []
    for index, manifest in enumerate(manifests):
        run_dir = root / f"run-{index}"
        run_dir.mkdir()
        (run_dir / "manifest.json").write_text(json.dumps(manifest))
        (run_dir / "decisions.jsonl").write_text("{}\n")
        (run_dir / "fills.parquet").write_bytes(b"test-fill-input")
        (run_dir / "portfolio.parquet").write_bytes(b"test-portfolio-input")
        (run_dir / "market_events.jsonl").write_text("{}\n")
        run_dirs.append(run_dir.name)
        blocks.append(manifest["config"]["independent_block"])
    payload = {
        "study_id": "paper-core",
        "status": status,
        "evidence_kind": evidence_kind,
        "expected_independent_blocks": blocks,
        "run_dirs": run_dirs,
        "preregistration": preregistration,
    }
    path = root / "study-source.json"
    path.write_text(json.dumps(payload))
    return path


def _verified() -> RunVerification:
    return RunVerification(
        ok=True,
        errors=[],
        warnings=[],
        decisions=20,
        fills=4,
        portfolio_rows=20,
    )


def _inference() -> StudyInference:
    return StudyInference(
        n_blocks=2,
        mean_effect=0.2,
        ci95=(0.1, 0.3),
        p_sign_flip=0.5,
        p_holm=0.5,
        reject=False,
        block_effects={"block-a": 0.1, "block-b": 0.3},
        dependence_clusters={"block-a": "cluster-block-a", "block-b": "cluster-block-b"},
    )


def _frozen_statistical_contract() -> dict:
    return {
        "estimand_id": "H1-kappa-technology-contrast",
        "sesoi": 0.08,
        "equivalence_lower": -0.04,
        "equivalence_upper": 0.04,
        "noninferiority_lower": -0.04,
        "alpha": 0.05,
    }


def test_bundle_emits_hash_locked_independent_unit_artifacts(tmp_path, monkeypatch):
    source = _source(
        tmp_path,
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())
    monkeypatch.setattr(
        "flock.analysis.bundle.analyze_h1_study", lambda _paths, seed=0: _inference()
    )

    bundle = analyze_study_bundle(source)

    assert all((bundle / artifact).is_file() for artifact in CORE_ARTIFACTS)
    assert (bundle / "figures/h1-block-effects.png").stat().st_size > 10_000
    assert (bundle / "figures/independent-unit-topology.png").stat().st_size > 10_000
    units = pd.read_parquet(bundle / "independent_units.parquet")
    assert len(units) == 2
    assert set(units["nested_model_seed"]) == {1}
    result = verify_study_bundle(bundle)
    assert result.ok
    assert result.independent_units == 2
    assert not result.paper_eligible

    missingness = pd.read_parquet(bundle / "missingness_failures.parquet")
    assert set(missingness["independent_block"]) == {"block-a", "block-b"}
    assert missingness["verification_ok"].all()
    sensitivities = pd.read_parquet(bundle / "sensitivity_results.parquet")
    assert set(sensitivities["specification_id"]) == {
        "primary-mean",
        "block-median",
        "leave-one-block-out:block-a",
        "leave-one-block-out:block-b",
    }
    equivalence = json.loads((bundle / "equivalence_noninferiority.json").read_text())
    assert equivalence["margin_status"] == "provisional-default"
    assert equivalence["margins_provisional"] is True
    assert equivalence["equivalence"]["equivalent"] is False
    assert equivalence["equivalence"]["paper_claim_allowed"] is False
    registry = json.loads((bundle / "estimand_registry.json").read_text())
    assert registry["estimands"][0]["sesoi"] == 0.10
    assert registry["estimands"][0]["margins_provisional"] is True


def test_release_reproduces_byte_identical_core_artifacts(tmp_path, monkeypatch):
    source = _source(
        tmp_path / "source",
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())
    monkeypatch.setattr(
        "flock.analysis.bundle.analyze_h1_study", lambda _paths, seed=0: _inference()
    )
    bundle = analyze_study_bundle(source, seed=739)

    reproduced = reproduce_study_bundle(
        bundle / "release-manifest.json", tmp_path / "clean-reproduction"
    )

    original_release = json.loads((bundle / "release-manifest.json").read_text())
    reproduced_release = json.loads((reproduced / "release-manifest.json").read_text())
    assert original_release["analysis_seed"] == 739
    assert reproduced_release["analysis_seed"] == 739
    assert original_release["artifact_sha256"] == reproduced_release["artifact_sha256"]
    verification = json.loads(
        (reproduced / "reproduction-verification.json").read_text()
    )
    assert verification["verified"] is True


def test_reproduction_rejects_nonempty_or_in_place_output(tmp_path, monkeypatch):
    source = _source(
        tmp_path / "source",
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())
    monkeypatch.setattr(
        "flock.analysis.bundle.analyze_h1_study", lambda _paths, seed=0: _inference()
    )
    bundle = analyze_study_bundle(source)
    release = bundle / "release-manifest.json"
    with pytest.raises(ValueError, match="must differ"):
        reproduce_study_bundle(release, bundle)
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("do not overwrite")
    with pytest.raises(ValueError, match="must be empty"):
        reproduce_study_bundle(release, occupied)


def test_bundle_rejects_repeated_trajectory_under_new_seed_and_label(tmp_path, monkeypatch):
    source = _source(
        tmp_path,
        [
            _manifest("block-a", "same-trajectory", seed=1),
            _manifest("block-b", "same-trajectory", seed=999),
        ],
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())

    with pytest.raises(ValueError, match="model seeds do not create independent evidence"):
        analyze_study_bundle(source)


def test_bundle_rejects_incomplete_or_unverified_runs(tmp_path, monkeypatch):
    source = _source(
        tmp_path,
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
        status="incomplete",
    )
    with pytest.raises(ValueError, match="study source is incomplete"):
        analyze_study_bundle(source)

    payload = json.loads(source.read_text())
    payload["status"] = "complete"
    source.write_text(json.dumps(payload))
    failed = _verified().model_copy(update={"ok": False, "errors": ["parse gate failed"]})
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: failed)
    with pytest.raises(ValueError, match="run failed verification"):
        analyze_study_bundle(source)


def test_paper_gate_rejects_mock_and_missing_preregistration(tmp_path, monkeypatch):
    mock_source = _source(
        tmp_path / "mock",
        [
            _manifest("block-a", "trajectory-a", model="mock-momentum"),
            _manifest("block-b", "trajectory-b", model="mock-momentum"),
        ],
        evidence_kind="mock",
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())
    with pytest.raises(ValueError, match="paper export rejects mock evidence"):
        analyze_study_bundle(mock_source, paper=True)

    real_root = tmp_path / "real"
    real_source = _source(
        real_root,
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
    )
    with pytest.raises(ValueError, match="requires an immutable preregistration"):
        analyze_study_bundle(real_source, paper=True)


def test_paper_bundle_requires_frozen_preregistration_and_detects_tampering(
    tmp_path, monkeypatch
):
    prereg = tmp_path / "preregistration.json"
    prereg.write_text(
        json.dumps(
            {
                "frozen": True,
                "statistical_contract": _frozen_statistical_contract(),
            }
        )
        + "\n"
    )
    digest = hashlib.sha256(prereg.read_bytes()).hexdigest()
    source = _source(
        tmp_path,
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
        preregistration={
            "path": prereg.name,
            "sha256": digest,
            "immutable_uri": "https://osf.io/example/registrations/1",
            "git_sha": "0123456789abcdef",
        },
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())
    monkeypatch.setattr(
        "flock.analysis.bundle.analyze_h1_study", lambda _paths, seed=0: _inference()
    )

    bundle = analyze_study_bundle(source, paper=True)
    assert verify_study_bundle(bundle, require_paper=True).paper_eligible
    registry = json.loads((bundle / "estimand_registry.json").read_text())
    assert registry["estimands"][0]["sesoi"] == 0.08
    assert registry["estimands"][0]["margin_status"] == "frozen-preregistered"

    release_path = bundle / "release-manifest.json"
    release = json.loads(release_path.read_text())
    release["statistical_contract"]["sesoi"] = 0.09
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    contract_tampering = verify_study_bundle(bundle, require_paper=True)
    assert not contract_tampering.ok
    assert (
        "release statistical contract differs from preregistration"
        in contract_tampering.errors
    )

    release["statistical_contract"]["sesoi"] = 0.08
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")

    effects = pd.read_parquet(bundle / "effects.parquet")
    effects.loc[0, "estimate"] = 99
    effects.to_parquet(bundle / "effects.parquet", index=False)
    result = verify_study_bundle(bundle, require_paper=True)
    assert not result.ok
    assert "artifact hash mismatch: effects.parquet" in result.errors


def test_paper_gate_rejects_preregistration_without_frozen_margins(tmp_path, monkeypatch):
    prereg = tmp_path / "preregistration.json"
    prereg.write_text('{"frozen": true}\n')
    source = _source(
        tmp_path,
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
        preregistration={
            "path": prereg.name,
            "sha256": hashlib.sha256(prereg.read_bytes()).hexdigest(),
            "immutable_uri": "https://osf.io/example/registrations/1",
            "git_sha": "0123456789abcdef",
        },
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())

    with pytest.raises(ValueError, match="requires a preregistered statistical_contract"):
        analyze_study_bundle(source, paper=True)


def test_bundle_fails_closed_on_missing_or_false_equivalence_artifacts(tmp_path, monkeypatch):
    source = _source(
        tmp_path,
        [_manifest("block-a", "trajectory-a"), _manifest("block-b", "trajectory-b")],
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())
    monkeypatch.setattr(
        "flock.analysis.bundle.analyze_h1_study", lambda _paths, seed=0: _inference()
    )
    bundle = analyze_study_bundle(source)

    sensitivity_path = bundle / "sensitivity_results.parquet"
    sensitivity_path.unlink()
    missing = verify_study_bundle(bundle)
    assert not missing.ok
    assert "missing core artifact: sensitivity_results.parquet" in missing.errors

    bundle = analyze_study_bundle(source)
    equivalence_path = bundle / "equivalence_noninferiority.json"
    equivalence = json.loads(equivalence_path.read_text())
    equivalence["equivalence"]["p_lower"] = 0.001
    equivalence["equivalence"]["p_upper"] = 0.001
    equivalence["equivalence"]["equivalent"] = True
    equivalence_path.write_text(json.dumps(equivalence, indent=2, sort_keys=True) + "\n")
    release_path = bundle / "release-manifest.json"
    release = json.loads(release_path.read_text())
    release["artifact_sha256"]["equivalence_noninferiority.json"] = hashlib.sha256(
        equivalence_path.read_bytes()
    ).hexdigest()
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")

    false_equivalence = verify_study_bundle(bundle)
    assert not false_equivalence.ok
    assert (
        "equivalence result does not reproduce from block effects"
        in false_equivalence.errors
    )
