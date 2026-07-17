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
    units = pd.read_parquet(bundle / "independent_units.parquet")
    assert len(units) == 2
    assert set(units["nested_model_seed"]) == {1}
    result = verify_study_bundle(bundle)
    assert result.ok
    assert result.independent_units == 2
    assert not result.paper_eligible


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
    prereg.write_text('{"frozen": true}\n')
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

    effects = pd.read_parquet(bundle / "effects.parquet")
    effects.loc[0, "estimate"] = 99
    effects.to_parquet(bundle / "effects.parquet", index=False)
    result = verify_study_bundle(bundle, require_paper=True)
    assert not result.ok
    assert "artifact hash mismatch: effects.parquet" in result.errors
