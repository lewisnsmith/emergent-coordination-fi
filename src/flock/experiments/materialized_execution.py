"""Execute an explicitly mock-only materialized study with terminal accounting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from flock.core.config import ExperimentConfig, load_models
from flock.experiments.materialize import MaterializedStudy, RunAssignment
from flock.experiments.runner import make_run_id, resolved_config_hash, run_config

TERMINAL_STATUSES = {"completed", "reused", "blocked", "failed"}


def _canonical_assignments(bundle: MaterializedStudy) -> str:
    payload = [assignment.model_dump(mode="json") for assignment in bundle.assignments]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _load_and_verify_bundle(path: Path) -> MaterializedStudy:
    bundle = MaterializedStudy.model_validate_json(path.read_text())
    assignments = bundle.assignments
    if [assignment.ordinal for assignment in assignments] != list(
        range(1, len(assignments) + 1)
    ):
        raise ValueError("materialized assignment ordinals must be contiguous from one")
    identifiers = [assignment.assignment_id for assignment in assignments]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("materialized assignment identifiers must be unique")
    totals = (
        len(assignments),
        sum(item.exact_counts.steps for item in assignments),
        sum(item.exact_counts.agent_steps for item in assignments),
        sum(item.exact_counts.calls for item in assignments),
    )
    expected = (
        bundle.exact_runs,
        bundle.exact_steps,
        bundle.exact_agent_steps,
        bundle.exact_calls,
    )
    if totals != expected:
        raise ValueError("materialized bundle totals do not reconcile with assignments")
    actual_hash = hashlib.sha256(_canonical_assignments(bundle).encode()).hexdigest()
    if actual_hash != bundle.materialization_hash:
        raise ValueError("materialized bundle hash does not match assignment payload")
    if any(
        assignment.study_id != bundle.study_id or assignment.plan_hash != bundle.plan_hash
        for assignment in assignments
    ):
        raise ValueError("assignment study or plan provenance differs from bundle")
    return bundle


def _validate_mock_assignment(
    assignment: RunAssignment, models: dict[str, Any]
) -> ExperimentConfig | None:
    if assignment.evidence_kind != "mock":
        raise ValueError(
            f"{assignment.assignment_id}: execute-materialized only accepts evidence_kind=mock"
        )
    frozen_revisions = {
        allocation.model_id: allocation.revision
        for cohort in assignment.cohorts
        for allocation in cohort.allocations
    }
    if frozen_revisions != assignment.model_revisions:
        raise ValueError(f"{assignment.assignment_id}: frozen model revision provenance drift")
    source_api_models = {
        allocation.model_id
        for cohort in assignment.cohorts
        if cohort.technology == "llm"
        for allocation in cohort.allocations
        if allocation.provider != "mock"
    }
    missing_substitutions = source_api_models - assignment.model_registry_substitutions.keys()
    if missing_substitutions:
        raise ValueError(
            f"{assignment.assignment_id}: missing explicit mock substitutions for "
            f"{sorted(missing_substitutions)}"
        )
    if assignment.execution_config is None:
        if not assignment.execution_blockers:
            raise ValueError(
                f"{assignment.assignment_id}: unresolved assignment has no explicit blocker"
            )
        return None

    config = ExperimentConfig.model_validate(assignment.execution_config)
    if config.model_policy != "mock_only":
        raise ValueError(f"{assignment.assignment_id}: non-mock model_policy rejected")
    expected_fields = {
        "name": assignment.assignment_id,
        "seed": assignment.seed,
        "steps": assignment.steps,
        "trajectory_id": assignment.trajectory_id,
        "independent_block": assignment.trajectory_id,
        "dependence_cluster": assignment.dependence_cluster_id,
        "market_replica_id": assignment.market_replica_id,
    }
    drift = [
        field
        for field, expected in expected_fields.items()
        if getattr(config, field) != expected
    ]
    if drift:
        raise ValueError(
            f"{assignment.assignment_id}: execution config provenance drift: {', '.join(drift)}"
        )
    for group in (group for cohort in config.cohorts for group in cohort.agents):
        if group.kind != "llm":
            continue
        if group.model is None or group.model not in models:
            raise ValueError(f"{assignment.assignment_id}: unresolved mock model registry key")
        spec = models[group.model]
        if spec.provider != "mock" or spec.deployment != "mock":
            raise ValueError(
                f"{assignment.assignment_id}: model {group.model!r} is not local mock-only"
            )
    return config


def _manifest_error(path: Path, config: ExperimentConfig) -> str | None:
    try:
        manifest = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return f"cannot read completed manifest: {error}"
    expected_hash = resolved_config_hash(config)
    checks = {
        "run_id": (manifest.get("run_id"), make_run_id(config)),
        "resolved_config_hash": (manifest.get("resolved_config_hash"), expected_hash),
        "model_policy": (
            manifest.get("config", {}).get("model_policy"),
            "mock_only",
        ),
        "total_cost_usd": (manifest.get("total_cost_usd"), 0.0),
    }
    mismatches = [
        f"{field}={actual!r} (expected {expected!r})"
        for field, (actual, expected) in checks.items()
        if actual != expected
    ]
    return "; ".join(mismatches) if mismatches else None


def _summary(entries: list[dict[str, Any]]) -> dict[str, int]:
    return {
        status: sum(entry["status"] == status for entry in entries)
        for status in ("completed", "reused", "blocked", "failed", "pending")
    }


def _write_ledger(ledger: dict[str, Any], path: Path) -> None:
    ledger["summary"] = _summary(ledger["assignments"])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def execute_materialized(
    bundle_path: Path,
    results_root: Path,
    ledger_path: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Run every executable mock assignment and record a resumable terminal ledger.

    The complete bundle is validated before the first run. Any real/API model
    assignment rejects the whole operation, ensuring no paid provider can be
    reached through this command.
    """

    bundle = _load_and_verify_bundle(bundle_path)
    models = load_models()
    configs = {
        assignment.assignment_id: _validate_mock_assignment(assignment, models)
        for assignment in bundle.assignments
    }
    output = ledger_path or (
        results_root
        / f"{bundle.study_id}-{bundle.materialization_hash[:12]}-execution-ledger.json"
    )
    previous: dict[str, Any] = {}
    if output.exists():
        loaded = json.loads(output.read_text())
        identity = (
            loaded.get("study_id"),
            loaded.get("plan_hash"),
            loaded.get("materialization_hash"),
        )
        expected_identity = (bundle.study_id, bundle.plan_hash, bundle.materialization_hash)
        if identity != expected_identity:
            raise ValueError("existing execution ledger belongs to a different bundle")
        previous = {
            entry["assignment_id"]: entry for entry in loaded.get("assignments", [])
        }

    entries: list[dict[str, Any]] = []
    for assignment in bundle.assignments:
        config = configs[assignment.assignment_id]
        old = previous.get(assignment.assignment_id, {})
        if config is None:
            entry = {
                "assignment_id": assignment.assignment_id,
                "ordinal": assignment.ordinal,
                "stage_id": assignment.stage_id,
                "evidence_kind": "mock",
                "status": "blocked",
                "blockers": list(assignment.execution_blockers),
                "run_id": None,
                "run_dir": None,
                "error": None,
            }
        else:
            entry = {
                "assignment_id": assignment.assignment_id,
                "ordinal": assignment.ordinal,
                "stage_id": assignment.stage_id,
                "evidence_kind": "mock",
                "status": (
                    old.get("status")
                    if old.get("status") in TERMINAL_STATUSES
                    else "pending"
                ),
                "blockers": [],
                "run_id": old.get("run_id"),
                "run_dir": old.get("run_dir"),
                "error": old.get("error"),
            }
        entries.append(entry)

    ledger = {
        "schema_version": 1,
        "study_id": bundle.study_id,
        "plan_hash": bundle.plan_hash,
        "materialization_hash": bundle.materialization_hash,
        "evidence_kind": "mock",
        "paper_eligible": False,
        "assignments": entries,
        "summary": {},
    }
    _write_ledger(ledger, output)

    for assignment, entry in zip(bundle.assignments, entries, strict=True):
        config = configs[assignment.assignment_id]
        if config is None:
            continue
        run_id = make_run_id(config)
        run_dir = results_root / run_id
        manifest_path = run_dir / "manifest.json"
        entry.update({"run_id": run_id, "run_dir": str(run_dir), "error": None})
        if manifest_path.exists():
            error = _manifest_error(manifest_path, config)
            if error is None:
                entry["status"] = "reused"
            else:
                entry.update({"status": "failed", "error": error})
            _write_ledger(ledger, output)
            continue
        try:
            result = run_config(config, results_root=results_root)
            if result.run_id != run_id:
                raise ValueError("runner returned a run id different from the resolved config")
            error = _manifest_error(result.run_dir / "manifest.json", config)
            if error is not None:
                raise ValueError(error)
            entry.update(
                {
                    "status": "completed",
                    "run_id": result.run_id,
                    "run_dir": str(result.run_dir),
                }
            )
        except Exception as error:  # terminal ledger must account for later cells too
            entry.update(
                {
                    "status": "failed",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
        _write_ledger(ledger, output)

    if any(entry["status"] == "pending" for entry in entries):
        raise RuntimeError("execution ended with non-terminal assignments")
    return output, ledger
