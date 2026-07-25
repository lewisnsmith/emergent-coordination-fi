import json
import shutil
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from flock.cli import app
from flock.core.config import ExperimentConfig
from flock.experiments.design import generate_mphiq_schemes
from flock.experiments.doctor import run_doctor
from flock.experiments.verify import verify_repository, verify_run


def _copy_scaffold_without_datasets(repo: Path, destination: Path) -> None:
    shutil.copytree(repo / "configs", destination / "configs")
    datasets = destination / "datasets"
    datasets.mkdir()
    shutil.copy2(repo / "datasets/manifests.json", datasets / "manifests.json")


def test_design_cli_exports_all_cells(tmp_path):
    output = tmp_path / "design.json"
    result = CliRunner().invoke(app, ["design", "--output", str(output)])
    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text())
    assert len(payload["mphiq"]) == 32
    assert len(payload["prompt_pressure"]) == 24
    assert payload["mphiq"][0]["code"] == generate_mphiq_schemes()[0].code


def test_experiment_schema_rejects_unknown_fields_and_preserves_unit_lineage():
    payload = {
        "name": "lineage-check",
        "dataset": "example",
        "model_policy": "mock_only",
        "independent_block": "window-1",
        "dependence_cluster": "nonoverlap-1",
        "trajectory_id": "trajectory-1",
        "cohorts": [],
    }
    config = ExperimentConfig.model_validate(payload)
    assert config.model_dump()["dependence_cluster"] == "nonoverlap-1"
    assert config.model_dump()["trajectory_id"] == "trajectory-1"
    with pytest.raises(ValidationError, match="unknown_field"):
        ExperimentConfig.model_validate({**payload, "unknown_field": True})


def test_validate_cli_writes_machine_readable_report(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    clean_repo = tmp_path / "repo"
    _copy_scaffold_without_datasets(repo, clean_repo)
    output = tmp_path / "readiness.json"
    result = CliRunner().invoke(
        app, ["validate", "--root", str(clean_repo), "--output", str(output)]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text())
    assert payload["scaffold_ok"] is True
    assert payload["execution_ready"] is False
    assert payload["errors"] == []
    assert payload["acquired_datasets"] == []
    assert "synthetic-equities-v1" in payload["missing_datasets"]
    payload_blockers = [
        blocker
        for blocker in payload["blockers"]
        if blocker.startswith("dataset payload unavailable:")
    ]
    assert len(payload_blockers) == 1
    assert "synthetic-equities-v1 v2" in payload_blockers[0]
    assert payload["profiles"] == 24
    assert payload["frontier_models"] >= 5


def test_repository_validation_rejects_corrupt_present_dataset(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    clean_repo = tmp_path / "repo"
    _copy_scaffold_without_datasets(repo, clean_repo)
    dataset = clean_repo / "datasets/synthetic-equities-v1-v2"
    dataset.mkdir()
    (dataset / "meta.json").write_text('{"corrupt": true}')

    readiness = verify_repository(clean_repo)

    assert readiness.scaffold_ok is False
    assert readiness.acquired_datasets == ["synthetic-equities-v1"]
    assert any(
        error.startswith("synthetic-equities-v1: dataset file inventory")
        for error in readiness.errors
    )


def test_legacy_run_fails_logical_verification(tmp_path):
    run_dir = tmp_path / "legacy-run"
    run_dir.mkdir()
    manifest = {
        "config": {
            "initial_cash": 1_000.0,
            "market": {"kind": "replay", "fee_bps": 0.0},
        },
        "dataset": {"name": "missing-legacy-dataset", "sha256": "legacy"},
        "agents": {"baseline-0": {"kind": "baseline"}},
        "n_agents": 1,
        "n_steps": 1,
        "total_cost_usd": 0.0,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest))
    (run_dir / "decisions.jsonl").write_text(
        json.dumps(
            {
                "agent_id": "baseline-0",
                "step": 0,
                "orders_clipped": [],
                "prompt_hash": None,
                "raw_response_hash": None,
                "grounding_ok": True,
                "parse_ok": True,
                "usage": {"cost_usd": 0.0},
            }
        )
        + "\n"
    )
    pd.DataFrame(
        columns=["agent_id", "step", "price", "quantity", "fee", "side"]
    ).to_parquet(run_dir / "fills.parquet", index=False)
    pd.DataFrame(
        [{"agent_id": "baseline-0", "step": 0, "cash": 1_000.0}]
    ).to_parquet(run_dir / "portfolio.parquet", index=False)

    result = verify_run(run_dir)

    # Logs created before the evidence contract must not be silently certified.
    assert not result.ok
    assert any(
        "missing symbol universe" in error or "dataset hash" in error
        for error in result.errors
    )


def test_offline_doctor_never_exposes_credentials(monkeypatch):
    for name in (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    report = run_doctor(live=False)
    rendered = report.model_dump_json()
    assert "not present" in rendered
    assert "sk-" not in rendered
    assert all(not check.name.startswith("endpoint:") for check in report.checks)
