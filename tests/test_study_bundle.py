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
from flock.analysis.crossed import H1_CONTRASTS, H3_CONTRASTS, H4_COMPONENTS, H4_CONTRASTS
from flock.analysis.study import StudyInference
from flock.experiments.verify import RunVerification


def _manifest(
    block: str,
    trajectory: str,
    *,
    model: str = "dated-model",
    seed: int = 1,
    run_id: str | None = None,
):
    return {
        "run_id": run_id or f"run-{block}",
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
    first_paper_inputs: dict | None = None,
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
        block = manifest["config"]["independent_block"]
        if block not in blocks:
            blocks.append(block)
    payload = {
        "study_id": "paper-core",
        "status": status,
        "evidence_kind": evidence_kind,
        "expected_independent_blocks": blocks,
        "run_dirs": run_dirs,
        "preregistration": preregistration,
        "first_paper_inputs": first_paper_inputs,
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


def _first_paper_contract() -> dict:
    thresholds = {
        "sesoi": 0.08,
        "equivalence_lower": -0.04,
        "equivalence_upper": 0.04,
        "noninferiority_lower": -0.04,
    }
    return {
        "confirmatory_metrics": ["kappa"],
        "estimands": {
            f"{estimand_id}::kappa": thresholds
            for estimand_id in (*H1_CONTRASTS, *H3_CONTRASTS, *H4_CONTRASTS)
        },
        "alpha": 0.05,
    }


def _paper_inputs(
    root: Path, source_runs: dict[str, list[str]] | None = None
) -> dict:
    source_runs = source_runs or {
        "block-a": ["run-block-a"],
        "block-b": ["run-block-b"],
    }
    identities = [
        ("block-a", "cluster-block-a", "trajectory-a"),
        ("block-b", "cluster-block-b", "trajectory-b"),
    ]
    crossed = []
    for block_index, (block, cluster, trajectory) in enumerate(identities):
        for technology, families in (
            ("llm", ("model-a", "model-b")),
            ("classical", ("momentum", "value")),
        ):
            for ecology in ("homogeneous", "heterogeneous"):
                for family_index, family in enumerate(families):
                    crossed.append(
                        {
                            "independent_block": block,
                            "dependence_cluster": cluster,
                            "trajectory_id": trajectory,
                            "metric": "kappa",
                            "technology": technology,
                            "ecology": ecology,
                            "family": family,
                            "family_weight": 1.0,
                            "value": (
                                0.5
                                + block_index * 0.02
                                + family_index * 0.01
                                + (0.1 if technology == "llm" else 0.0)
                                + (0.03 if ecology == "heterogeneous" else 0.0)
                            ),
                            "source_run_ids": source_runs[block],
                        }
                    )
    lineage = []
    for block_index, (block, cluster, trajectory) in enumerate(identities):
        for relationship, value in (
            ("same_model", 0.6),
            ("same_provider", 0.5),
            ("cross_provider", 0.3),
        ):
            lineage.append(
                {
                    "independent_block": block,
                    "dependence_cluster": cluster,
                    "trajectory_id": trajectory,
                    "metric": "kappa",
                    "relationship": relationship,
                    "family_stratum": "balanced-provider-stratum",
                    "pair_id": f"{relationship}-{block_index}",
                    "value": value + block_index * 0.01,
                    "source_run_ids": source_runs[block],
                }
            )
    mphiq = []
    for block_index, (block, cluster, trajectory) in enumerate(identities):
        for component_index, component in enumerate(H4_COMPONENTS):
            different = list("11111")
            different[component_index] = "0"
            mphiq.append(
                {
                    "independent_block": block,
                    "dependence_cluster": cluster,
                    "trajectory_id": trajectory,
                    "metric": "kappa",
                    "component": component,
                    "pair_id": f"{component}-{block_index}",
                    "code_same": "11111",
                    "code_different": "".join(different),
                    "value_same": 0.5,
                    "value_different": 0.45 + component_index * 0.01,
                    "source_run_ids": source_runs[block],
                }
            )
    frames = {
        "crossed_rows": pd.DataFrame(crossed),
        "lineage_rows": pd.DataFrame(lineage),
        "mphiq_rows": pd.DataFrame(mphiq),
    }
    references = {}
    for name, frame in frames.items():
        path = root / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        references[name] = {
            "path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return references


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
    assert bool(missingness["verification_ok"].all())
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
                "first_paper_statistical_contract": _first_paper_contract(),
            }
        )
        + "\n"
    )
    digest = hashlib.sha256(prereg.read_bytes()).hexdigest()
    source_runs = {
        "block-a": ["run-block-a-llm", "run-block-a-classical"],
        "block-b": ["run-block-b-llm", "run-block-b-classical"],
    }
    source = _source(
        tmp_path,
        [
            _manifest(
                "block-a", "trajectory-a", run_id="run-block-a-llm", seed=1
            ),
            _manifest(
                "block-a", "trajectory-a", run_id="run-block-a-classical", seed=2
            ),
            _manifest(
                "block-b", "trajectory-b", run_id="run-block-b-llm", seed=1
            ),
            _manifest(
                "block-b", "trajectory-b", run_id="run-block-b-classical", seed=2
            ),
        ],
        preregistration={
            "path": prereg.name,
            "sha256": digest,
            "immutable_uri": "https://osf.io/example/registrations/1",
            "git_sha": "0123456789abcdef",
        },
        first_paper_inputs=_paper_inputs(tmp_path, source_runs),
    )
    monkeypatch.setattr("flock.analysis.bundle.verify_run", lambda _path: _verified())
    monkeypatch.setattr(
        "flock.analysis.bundle.analyze_h1_study", lambda _paths, seed=0: _inference()
    )

    with pytest.raises(ValueError, match="require --paper"):
        analyze_study_bundle(source)
    bundle = analyze_study_bundle(source, paper=True)
    assert verify_study_bundle(bundle, require_paper=True).paper_eligible
    units = pd.read_parquet(bundle / "independent_units.parquet")
    assert len(units) == 2
    assert set(units["nested_treatment_runs"]) == {2}
    registry = json.loads((bundle / "estimand_registry.json").read_text())
    assert len(registry["estimands"]) == 12
    assert {row["sesoi"] for row in registry["estimands"]} == {0.08}
    assert {row["margin_status"] for row in registry["estimands"]} == {
        "frozen-preregistered"
    }
    effects = pd.read_parquet(bundle / "effects.parquet")
    assert len(effects) == 12
    multiplicity = json.loads((bundle / "multiplicity.json").read_text())
    assert set(multiplicity["hypotheses"]) == set(_first_paper_contract()["estimands"])

    claims_path = bundle / "claims.json"
    claims = json.loads(claims_path.read_text())
    claims["claims"].pop()
    claims_path.write_text(json.dumps(claims, indent=2, sort_keys=True) + "\n")
    release_path = bundle / "release-manifest.json"
    release = json.loads(release_path.read_text())
    release["artifact_sha256"]["claims.json"] = hashlib.sha256(
        claims_path.read_bytes()
    ).hexdigest()
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    claim_tampering = verify_study_bundle(bundle, require_paper=True)
    assert not claim_tampering.ok
    assert (
        "paper claims do not exactly cover the frozen estimand family"
        in claim_tampering.errors
    )

    bundle = analyze_study_bundle(source, paper=True)

    release_path = bundle / "release-manifest.json"
    release = json.loads(release_path.read_text())
    first_key = next(iter(release["first_paper_statistical_contract"]["estimands"]))
    release["first_paper_statistical_contract"]["estimands"][first_key]["sesoi"] = 0.09
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
    contract_tampering = verify_study_bundle(bundle, require_paper=True)
    assert not contract_tampering.ok
    assert (
        "release first-paper statistical contract differs from preregistration"
        in contract_tampering.errors
    )

    release["first_paper_statistical_contract"]["estimands"][first_key]["sesoi"] = 0.08
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")

    effects = pd.read_parquet(bundle / "effects.parquet")
    effects.loc[0, "estimate"] = 99
    effects.to_parquet(bundle / "effects.parquet", index=False)
    result = verify_study_bundle(bundle, require_paper=True)
    assert not result.ok
    assert "artifact hash mismatch: effects.parquet" in result.errors

    crossed_path = tmp_path / "crossed_rows.parquet"
    crossed = pd.read_parquet(crossed_path)
    crossed.at[0, "source_run_ids"] = ["run-block-b-llm"]
    crossed.to_parquet(crossed_path, index=False)
    source_payload = json.loads(source.read_text())
    source_payload["first_paper_inputs"]["crossed_rows"]["sha256"] = hashlib.sha256(
        crossed_path.read_bytes()
    ).hexdigest()
    source.write_text(json.dumps(source_payload))
    with pytest.raises(ValueError, match="source run from another block lineage"):
        analyze_study_bundle(source, paper=True)


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

    with pytest.raises(
        ValueError, match="requires a preregistered first_paper_statistical_contract"
    ):
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
