import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from flock.cli import app
from flock.core.config import ExperimentConfig
from flock.experiments.materialize import (
    MaterializedStudy,
    load_execution_resolution,
    materialize_study,
    write_materialized_study,
)
from flock.experiments.materialized_execution import execute_materialized
from flock.experiments.runner import RunResult, make_run_id, resolved_config_hash
from flock.experiments.study import compile_study_file

PAPER_CORE = Path("configs/studies/paper-core.yaml")
MOCK_RESOLUTION = Path("configs/execution/paper-core-offline-mock.yaml")


def _subset_bundle(source: MaterializedStudy) -> MaterializedStudy:
    selected = [
        source.assignments[0],
        next(item for item in source.assignments if item.stage_id == "calibration-replay"),
        next(item for item in source.assignments if item.stage_id == "h5-capital-share"),
    ]
    assignments = tuple(
        assignment.model_copy(update={"ordinal": ordinal})
        for ordinal, assignment in enumerate(selected, start=1)
    )
    canonical = json.dumps(
        [item.model_dump(mode="json") for item in assignments],
        sort_keys=True,
        separators=(",", ":"),
    )
    return MaterializedStudy(
        schema_version=1,
        study_id=source.study_id,
        plan_hash=source.plan_hash,
        assignments=assignments,
        exact_runs=len(assignments),
        exact_steps=sum(item.exact_counts.steps for item in assignments),
        exact_agent_steps=sum(item.exact_counts.agent_steps for item in assignments),
        exact_calls=sum(item.exact_counts.calls for item in assignments),
        executable_runs=2,
        materialization_hash=hashlib.sha256(canonical.encode()).hexdigest(),
    )


def _write_mock_manifest(config: ExperimentConfig, results_root: Path) -> RunResult:
    run_id = make_run_id(config)
    run_dir = results_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "config": config.model_dump(mode="json"),
                "resolved_config_hash": resolved_config_hash(config),
                "n_steps": config.steps,
                "n_agents": sum(
                    group.count for cohort in config.cohorts for group in cohort.agents
                ),
                "total_cost_usd": 0.0,
            }
        )
    )
    return RunResult(
        run_id=run_id,
        run_dir=run_dir,
        n_steps=config.steps or 0,
        n_agents=sum(group.count for cohort in config.cohorts for group in cohort.agents),
    )


def test_paper_core_mock_resolution_is_explicit_deterministic_and_h5_gated(monkeypatch):
    monkeypatch.setattr("flock.data.registry.Registry.verify", lambda self, entry: [])
    plan = compile_study_file(PAPER_CORE)
    resolution = load_execution_resolution(MOCK_RESOLUTION)

    first = materialize_study(plan, resolution)
    second = materialize_study(plan, resolution)

    assert first.materialization_hash == second.materialization_hash
    assert first.exact_runs == 197
    assert first.executable_runs == 149
    assert {item.evidence_kind for item in first.assignments} == {"mock"}
    expected_substitutions = {
        "claude-opus-4-8": "mock-momentum",
        "claude-sonnet-5": "mock-momentum-noisy",
        "gpt-5.6-sol": "mock-contrarian",
        "gemini-3.1-pro-20260713": "mock-random",
    }
    replay = first.assignments[0]
    assert replay.model_registry_substitutions == expected_substitutions
    assert replay.model_revisions["claude-opus-4-8"] == "2026-07-13"
    assert any(
        allocation.provider == "anthropic"
        for cohort in replay.cohorts
        for allocation in cohort.allocations
    )
    replay_config = ExperimentConfig.model_validate(replay.execution_config)
    assert replay_config.model_policy == "mock_only"
    assert {
        group.model
        for cohort in replay_config.cohorts
        for group in cohort.agents
        if group.kind == "llm"
    } == set(expected_substitutions.values())

    mphiq = next(item for item in first.assignments if item.stage_id == "mphiq-factorial")
    mphiq_config = ExperimentConfig.model_validate(mphiq.execution_config)
    assert all(
        group.mphiq_treatment is not None
        and group.mphiq_treatment.model_registry_key in expected_substitutions.values()
        for group in mphiq_config.cohorts[0].agents
    )

    h5 = [item for item in first.assignments if item.stage_id == "h5-capital-share"]
    assert len(h5) == 48
    assert all(item.execution_config is None for item in h5)
    assert all(
        any("stage explicitly disabled" in blocker for blocker in item.execution_blockers)
        for item in h5
    )
    assert set(resolution.trajectory_datasets) == {
        trajectory.trajectory_id for trajectory in plan.source_spec.trajectories
    }


def test_execute_materialized_rejects_real_and_records_terminal_resume(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("flock.data.registry.Registry.verify", lambda self, entry: [])
    source = materialize_study(
        compile_study_file(PAPER_CORE),
        load_execution_resolution(MOCK_RESOLUTION),
    )
    bundle = _subset_bundle(source)
    bundle_path = tmp_path / "bundle.json"
    write_materialized_study(bundle, bundle_path)

    attempts: list[str] = []
    fail_calibration = True

    def fake_run(config, results_root, use_cache=True):
        attempts.append(config.name)
        if fail_calibration and "calibration-replay" in config.name:
            raise RuntimeError("deliberate offline test failure")
        return _write_mock_manifest(config, results_root)

    monkeypatch.setattr(
        "flock.experiments.materialized_execution.run_config",
        fake_run,
    )
    monkeypatch.setattr(
        "flock.experiments.materialized_execution.verify_run",
        lambda _run_dir: SimpleNamespace(ok=True, errors=[]),
    )
    results_root = tmp_path / "results"
    first = CliRunner().invoke(
        app,
        [
            "execute-materialized",
            str(bundle_path),
            "--results-root",
            str(results_root),
        ],
    )
    assert first.exit_code == 1
    ledger_path = next(results_root.glob("*-execution-ledger.json"))
    ledger = json.loads(ledger_path.read_text())
    assert ledger["evidence_kind"] == "mock"
    assert ledger["paper_eligible"] is False
    assert ledger["summary"] == {
        "blocked": 1,
        "completed": 1,
        "failed": 1,
        "pending": 0,
        "reused": 0,
    }
    assert {item["status"] for item in ledger["assignments"]} == {
        "blocked",
        "completed",
        "failed",
    }

    fail_calibration = False
    second = CliRunner().invoke(
        app,
        [
            "execute-materialized",
            str(bundle_path),
            "--results-root",
            str(results_root),
        ],
    )
    assert second.exit_code == 0, second.output
    resumed = json.loads(ledger_path.read_text())
    assert resumed["summary"] == {
        "blocked": 1,
        "completed": 1,
        "failed": 0,
        "pending": 0,
        "reused": 1,
    }
    assert len(attempts) == 3

    real_assignment = bundle.assignments[0].model_copy(update={"evidence_kind": "real"})
    canonical = json.dumps(
        [real_assignment.model_dump(mode="json")],
        sort_keys=True,
        separators=(",", ":"),
    )
    real_bundle = MaterializedStudy(
        schema_version=1,
        study_id=bundle.study_id,
        plan_hash=bundle.plan_hash,
        assignments=(real_assignment,),
        exact_runs=1,
        exact_steps=real_assignment.exact_counts.steps,
        exact_agent_steps=real_assignment.exact_counts.agent_steps,
        exact_calls=real_assignment.exact_counts.calls,
        executable_runs=1,
        materialization_hash=hashlib.sha256(canonical.encode()).hexdigest(),
    )
    real_path = tmp_path / "real-bundle.json"
    write_materialized_study(real_bundle, real_path)
    with pytest.raises(ValueError, match="only accepts evidence_kind=mock"):
        execute_materialized(real_path, tmp_path / "rejected")
    assert len(attempts) == 3

    tampered = bundle.assignments[0]
    tampered_config = ExperimentConfig.model_validate(
        tampered.execution_config
    ).model_dump(mode="json")
    first_llm = next(
        group
        for cohort in tampered_config["cohorts"]
        for group in cohort["agents"]
        if group["kind"] == "llm"
    )
    first_llm["model"] = "mock-hold"
    tampered = tampered.model_copy(update={"execution_config": tampered_config})
    tampered_payload = tampered.model_dump(mode="json")
    rejected_payload = {
        **bundle.model_dump(mode="json"),
        "assignments": [tampered_payload],
        "exact_runs": 1,
        "exact_steps": tampered.exact_counts.steps,
        "exact_agent_steps": tampered.exact_counts.agent_steps,
        "exact_calls": tampered.exact_counts.calls,
        "executable_runs": 1,
        "materialization_hash": hashlib.sha256(
            json.dumps(
                [tampered_payload], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest(),
    }
    rejected_path = tmp_path / "unmapped-mock-bundle.json"
    rejected_path.write_text(json.dumps(rejected_payload))
    with pytest.raises(ValueError, match="explicit frozen substitution"):
        execute_materialized(rejected_path, tmp_path / "unmapped")
