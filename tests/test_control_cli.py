"""Acceptance tests for the prompt-facing, non-executing control commands."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import flock.agents.providers.base as provider_base
from flock.cli import app
from flock.control.controller import build_preflight, build_status, canonical_output
from flock.control.models import canonical_sha256
from flock.control.program import AUTHORIZATION_TIERS, PHASE_DEFINITIONS, PROGRAM_PHASES
from flock.experiments.materialize import (
    MaterializedStudy,
    load_execution_resolution,
    materialize_study,
    write_materialized_study,
)
from flock.experiments.study import compile_study_file

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mock_materialization(tmp_path_factory: pytest.TempPathFactory) -> Path:
    plan = compile_study_file(REPO / "configs/studies/paper-core.yaml")
    complete = materialize_study(
        plan,
        load_execution_resolution(REPO / "configs/execution/paper-core-offline-mock.yaml"),
        root=REPO,
    )
    source = next(
        assignment
        for assignment in complete.assignments
        if assignment.execution_config is not None and assignment.authorization_stage == "canary"
    )
    assignment = source.model_copy(update={"ordinal": 1})
    assignment_payload = assignment.model_dump(mode="json")
    materialization_hash = hashlib.sha256(
        json.dumps([assignment_payload], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    subset = MaterializedStudy(
        schema_version=1,
        study_id=complete.study_id,
        plan_hash=complete.plan_hash,
        assignments=(assignment,),
        exact_runs=1,
        exact_steps=assignment.exact_counts.steps,
        exact_agent_steps=assignment.exact_counts.agent_steps,
        exact_calls=assignment.exact_counts.calls,
        executable_runs=1,
        materialization_hash=materialization_hash,
    )
    path = tmp_path_factory.mktemp("control") / "mock-materialization.json"
    write_materialized_study(subset, path)
    return path


def test_program_has_one_canonical_phase_and_tier_order() -> None:
    assert len(PROGRAM_PHASES) == len(set(PROGRAM_PHASES)) == 10
    assert tuple(item.phase for item in PHASE_DEFINITIONS) == PROGRAM_PHASES
    assert AUTHORIZATION_TIERS == (
        "plan",
        "mock",
        "canary",
        "pilot",
        "confirmatory",
        "release",
    )


def test_status_is_time_free_deterministic_and_exposes_blocker_evidence() -> None:
    first = build_status(REPO)
    second = build_status(REPO)

    assert canonical_output(first) == canonical_output(second)
    payload = first.model_dump(mode="json")
    declared_hash = payload.pop("state_sha256")
    assert declared_hash == canonical_sha256(payload)
    assert first.highest_safe_tier == "mock"
    assert first.signer_enrollment_count == 0
    assert len(first.blockers["evidence"]) == 6
    assert "no production public signer is enrolled" in first.blockers["provider"]
    assert set(first.hashes.model_dump()) == {
        "source_sha256",
        "tree_sha256",
        "lock_sha256",
        "control_sha256",
    }

    result = CliRunner().invoke(app, ["control", "status", "--json", "--root", str(REPO)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["state_sha256"] == first.state_sha256


def test_status_never_reads_or_emits_environment_file_values(tmp_path: Path) -> None:
    sentinel = "synthetic-secret-must-not-appear"
    (tmp_path / ".env").write_text(f"PROVIDER_TOKEN={sentinel}\n")

    rendered = canonical_output(build_status(tmp_path))

    assert sentinel not in rendered
    assert "PROVIDER_TOKEN" not in rendered


def test_ambiguous_control_invocations_construct_no_provider(
    mock_materialization: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        provider_base,
        "make_chat_model",
        lambda *_args, **_kwargs: calls.append("provider"),
    )
    runner = CliRunner()

    help_result = runner.invoke(app, ["control"])
    missing_tier = runner.invoke(
        app,
        [
            "control",
            "preflight",
            "--phase",
            "frontier-bridge",
            "--materialization",
            str(mock_materialization),
            "--out",
            str(mock_materialization.parent / "out"),
        ],
    )

    assert help_result.exit_code == 2
    assert missing_tier.exit_code == 2
    assert calls == []


def test_mock_preflight_is_local_canonical_and_ready(mock_materialization: Path) -> None:
    output_root = mock_materialization.parent / "mock-results"
    packet = build_preflight(
        repo_root=REPO,
        phase="local-precision-fidelity",
        tier="mock",
        materialization_path=mock_materialization,
        output_root=output_root,
    )

    assert packet.ready is True
    assert packet.blockers == ()
    assert packet.output_root == str(output_root.resolve())
    assert packet.selected_assignments == 1
    payload = packet.model_dump(mode="json")
    declared_hash = payload.pop("packet_sha256")
    assert declared_hash == canonical_sha256(payload)

    result = CliRunner().invoke(
        app,
        [
            "control",
            "preflight",
            "--phase",
            "local-precision-fidelity",
            "--tier",
            "mock",
            "--materialization",
            str(mock_materialization),
            "--out",
            str(output_root),
            "--root",
            str(REPO),
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["ready"] is True

    plan_packet = build_preflight(
        repo_root=REPO,
        phase="frontier-bridge",
        tier="plan",
        materialization_path=mock_materialization,
        output_root=output_root,
    )
    assert plan_packet.ready is True
    assert plan_packet.blockers == ()


def test_canary_preflight_blocks_before_provider_construction(
    mock_materialization: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        provider_base,
        "make_chat_model",
        lambda *_args, **_kwargs: calls.append("provider"),
    )

    result = CliRunner().invoke(
        app,
        [
            "control",
            "preflight",
            "--phase",
            "frontier-bridge",
            "--tier",
            "canary",
            "--materialization",
            str(mock_materialization),
            "--out",
            str(mock_materialization.parent / "canary-results"),
            "--root",
            str(REPO),
        ],
    )

    assert result.exit_code == 1, result.output
    packet = json.loads(result.stdout)
    assert packet["ready"] is False
    assert any("production public signer" in item for item in packet["blockers"])
    assert any("evidence_kind=real" in item for item in packet["blockers"])
    assert calls == []


def test_missing_or_hash_mismatched_materialization_fails_closed(
    mock_materialization: Path, tmp_path: Path
) -> None:
    runner = CliRunner()
    common = [
        "control",
        "preflight",
        "--phase",
        "local-precision-fidelity",
        "--tier",
        "mock",
        "--out",
        str(tmp_path / "out"),
        "--root",
        str(REPO),
    ]
    missing = runner.invoke(
        app,
        [*common, "--materialization", str(tmp_path / "missing.json")],
    )
    assert missing.exit_code == 1
    assert any("file is missing" in item for item in json.loads(missing.stdout)["blockers"])

    tampered_path = tmp_path / "tampered.json"
    tampered = json.loads(mock_materialization.read_text())
    tampered["materialization_hash"] = "0" * 64
    tampered_path.write_text(json.dumps(tampered))
    mismatched = runner.invoke(
        app,
        [*common, "--materialization", str(tampered_path)],
    )
    assert mismatched.exit_code == 1
    assert (
        "materialization hash does not match its assignments"
        in json.loads(mismatched.stdout)["blockers"]
    )
