#!/usr/bin/env python3
"""Print a read-only, secret-free snapshot for prompt-driven experiment control."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROADMAP_PHASES = (
    "audit_external_evidence",
    "benchmark_workstation",
    "freeze_scoring_key",
    "local_precision_and_fidelity_screen",
    "frontier_behavioral_bridge",
    "mechanistic_funnel",
    "local_replay_and_simulated_market_discovery",
    "real_market_transport",
    "prospective_paper_trading",
    "release",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _dirty_entries(repo: Path) -> list[dict[str, str]]:
    output = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    if output == "unavailable":
        return [{"code": "??", "path": "git status unavailable"}]
    return [
        {"code": line[:2], "path": line[3:]}
        for line in output.splitlines()
        if len(line) >= 4
    ]


def _yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        payload = yaml.safe_load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"expected mapping in {path}")
    return payload


def _match(text: str, pattern: str) -> str:
    matched = re.search(pattern, text, flags=re.MULTILINE)
    return matched.group(1).strip() if matched else "not recorded"


def _preregistration(repo: Path) -> dict[str, Any]:
    text = (repo / "docs/research/preregistration.md").read_text(encoding="utf-8")
    return {
        "status": _match(text, r"\*\*Status:\s*(.*?)\*\*"),
        "frozen_commit": _match(text, r"Frozen commit SHA:\s*\*\*(.*?)\*\*"),
        "osf_registration": _match(text, r"OSF registration DOI/URL:\s*\*\*(.*?)\*\*"),
        "prereg_v1_tag": _git(repo, "tag", "--list", "prereg-v1") == "prereg-v1",
    }


def _evidence(repo: Path) -> dict[str, Any]:
    research = repo / "docs/research"
    screening = _yaml(research / "literature-search-and-screening-log.yaml")
    matrix = _yaml(research / "external-evidence-matrix.yaml")
    artifacts = _yaml(research / "external-evidence-artifact-ledger.yaml")
    coverage = screening.get("coverage", {})
    reviews = artifacts.get("artifact_reviews", [])
    authorized = [
        review.get("id", "unnamed")
        for review in reviews
        if review.get("collection_reduction_authorized") is True
    ]
    return {
        "snapshot_id": screening.get("snapshot_id"),
        "cutoff": screening.get("snapshot_cutoff"),
        "status": screening.get("status"),
        "work_families": len(screening.get("work_families", [])),
        "claim_assessments": len(matrix.get("claim_assessments", [])),
        "artifact_reviews": len(reviews),
        "hypotheses_covered": len(coverage.get("hypotheses", [])),
        "experiments_covered": len(coverage.get("experiments", [])),
        "collection_reduction_authorized": authorized,
    }


def _costs(repo: Path, plan: Any) -> dict[str, Any]:
    from flock.experiments.costs import estimate_plan_costs, load_pricing

    pricing = load_pricing(repo / "configs/budgets/pricing.yaml")
    estimates: dict[str, Any] = {}
    for tier in ("canary", "pilot", "confirmatory"):
        estimate = estimate_plan_costs(plan, tier, pricing)
        estimates[tier] = {
            "calls": estimate.incremental.calls,
            "expected_usd": estimate.incremental.total_expected_usd,
            "high_usd": estimate.incremental.total_high_usd,
            "cumulative_high_usd": estimate.cumulative.total_high_usd,
            "hard_cap_usd": estimate.stage_hard_cap_usd,
            "within_hard_cap": estimate.within_stage_hard_cap,
            "pricing_version": estimate.incremental.pricing_version,
            "priced_on": estimate.incremental.priced_on,
        }
    return estimates


def build_status(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    source_root = str(repo / "src")
    if source_root not in sys.path:
        sys.path.insert(0, source_root)

    from flock.experiments.costs import load_pricing
    from flock.experiments.doctor import run_doctor
    from flock.experiments.study import compile_study, load_study_spec
    from flock.experiments.verify import verify_repository

    pricing = load_pricing(repo / "configs/budgets/pricing.yaml")
    plan = compile_study(
        load_study_spec(repo / "configs/studies/paper-core.yaml"), pricing=pricing
    )
    readiness = verify_repository(repo)
    doctor = run_doctor(repo, live=False)
    dirty = _dirty_entries(repo)
    control_paths = (
        Path("AGENTS.md"),
        Path(".agents/skills/run-flock-experiment/SKILL.md"),
        Path(".agents/skills/run-flock-experiment/agents/openai.yaml"),
        Path(".agents/skills/run-flock-experiment/references/control-contract.md"),
        Path(".agents/skills/run-flock-experiment/scripts/status.py"),
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "repository": {
            "root": str(repo),
            "branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
            "source_sha": _git(repo, "rev-parse", "HEAD"),
            "dirty": bool(dirty),
            "dirty_entries": dirty,
        },
        "control_plane": {
            "files": {
                str(path): _sha256(repo / path)
                for path in control_paths
            },
            "phase_state": {
                "roadmap_phases": list(ROADMAP_PHASES),
                "current_phase": None,
                "completed_phases": [],
                "next_phase": None,
                "reason": "no durable phase-completion ledger is implemented",
            },
        },
        "operator_policy": {
            "highest_implemented_execution_tier": "mock",
            "live_execution": "blocked_implementation",
            "missing_guards": [
                "authorization-bound real materialized executor",
                "persistent cumulative spend ledger and retry reconciliation",
                "provider capability and response-resolved provenance checks",
                "execution-fingerprint cache isolation",
            ],
        },
        "readiness": readiness.model_dump(mode="json"),
        "doctor": doctor.model_dump(mode="json"),
        "study": {
            "study_id": plan.study_id,
            "plan_hash": plan.plan_hash,
            "exact_runs": plan.exact_runs,
            "exact_calls": plan.exact_calls,
            "stages": [
                {
                    "stage_id": stage.stage_id,
                    "order": stage.order,
                    "tier": stage.authorization_stage,
                    "runs": stage.exact_counts.runs,
                    "calls": stage.exact_counts.calls,
                }
                for stage in plan.stages
            ],
            "costs": _costs(repo, plan),
        },
        "preregistration": _preregistration(repo),
        "external_evidence": _evidence(repo),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["state_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."), help="repository root")
    args = parser.parse_args()
    try:
        status = build_status(args.repo)
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
