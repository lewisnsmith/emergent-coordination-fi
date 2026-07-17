import json
from pathlib import Path

from typer.testing import CliRunner

from flock.cli import app
from flock.experiments.design import generate_mphiq_schemes
from flock.experiments.verify import verify_run


def test_design_cli_exports_all_cells(tmp_path):
    output = tmp_path / "design.json"
    result = CliRunner().invoke(app, ["design", "--output", str(output)])
    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text())
    assert len(payload["mphiq"]) == 32
    assert len(payload["prompt_pressure"]) == 24
    assert payload["mphiq"][0]["code"] == generate_mphiq_schemes()[0].code


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
    assert any("missing symbol universe" in error for error in result.errors)
