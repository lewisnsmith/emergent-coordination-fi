import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from flock.cli import app
from flock.core.config import ExperimentConfig
from flock.experiments.design import generate_mphiq_schemes
from flock.experiments.doctor import run_doctor
from flock.experiments.verify import verify_run


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
    output = tmp_path / "readiness.json"
    result = CliRunner().invoke(
        app, ["validate", "--root", str(repo), "--output", str(output)]
    )
    # Missing real datasets are execution blockers, not scaffold validation errors.
    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text())
    assert payload["scaffold_ok"] is True
    assert payload["execution_ready"] is False
    assert payload["profiles"] == 24
    assert payload["frontier_models"] >= 5


def test_existing_smoke_run_passes_logical_verification():
    repo = Path(__file__).resolve().parents[1]
    candidates = sorted((repo / "results").glob("exp-000-smoke-*/manifest.json"))
    assert candidates
    result = verify_run(candidates[-1].parent)
    # Legacy committed logs predate full symbols/prompt hashes and must not be
    # silently certified under the new evidence contract.
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
