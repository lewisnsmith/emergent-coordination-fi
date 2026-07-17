"""Repository and experiment preflight verification.

The verifier distinguishes a valid scaffold from execution readiness. Missing
external datasets, IRB approval, exposure data, or API keys are blockers, not
silent passes and not reasons to call the research program complete.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel

from flock.core.config import PersonaConfig, load_experiment, load_models
from flock.core.research import load_research_program, validate_research_program
from flock.data.registry import Registry, dataset_bundle_hash
from flock.experiments.design import validate_mphiq_catalog


class RepositoryReadiness(BaseModel):
    scaffold_ok: bool
    execution_ready: bool
    errors: list[str]
    blockers: list[str]
    warnings: list[str]
    acquired_datasets: list[str]
    missing_datasets: list[str]
    experiment_configs: int
    profiles: int
    frontier_models: int
    research_experiments: int


class RunVerification(BaseModel):
    ok: bool
    errors: list[str]
    warnings: list[str]
    decisions: int
    fills: int
    portfolio_rows: int


class DecisionRecord(TypedDict):
    agent_id: str
    step: int
    symbols: NotRequired[list[str]]
    orders_clipped: list[dict[str, Any]]
    prompt_hash: str | None
    raw_response_hash: str | None
    grounding_ok: bool
    parse_ok: bool
    usage: NotRequired[dict[str, Any] | None]


class FillRecord(TypedDict):
    agent_id: str
    step: int
    price: float
    quantity: float
    fee: float
    side: str


class PortfolioRecord(TypedDict):
    agent_id: str
    step: int
    cash: float


def _yaml(path: Path):
    with path.open() as stream:
        return yaml.safe_load(stream)


def verify_repository(repo_root: Path = Path(".")) -> RepositoryReadiness:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []

    program = load_research_program(repo_root / "configs/research-program.yaml")
    program_result = validate_research_program(program, repo_root)
    errors.extend(program_result.errors)
    warnings.extend(program_result.warnings)

    models = load_models(repo_root / "configs/models.yaml")
    frontier = {name for name, spec in models.items() if spec.frontier_eligible}
    for name in frontier:
        spec = models[name]
        if not spec.verified_on or not spec.pricing_key:
            errors.append(f"frontier model {name} lacks verification/pricing metadata")
    for name, spec in models.items():
        if spec.provider != "mock" and not spec.frontier_eligible:
            errors.append(f"non-mock model {name} is not frontier eligible")

    profile_paths = sorted((repo_root / "configs/personas").glob("*.yaml"))
    profile_paths = [path for path in profile_paths if path.name != "manifest.yaml"]
    for path in profile_paths:
        PersonaConfig.model_validate(_yaml(path))
    manifest = _yaml(repo_root / "configs/personas/manifest.yaml")
    declared_profiles = {
        name for group in manifest["profiles"].values() for name in group
    }
    actual_profiles = {path.stem for path in profile_paths}
    if declared_profiles != actual_profiles:
        errors.append("persona manifest membership does not match persona files")

    config_paths = sorted((repo_root / "configs/experiments").glob("*.yaml"))
    configs = []
    for path in config_paths:
        cfg = load_experiment(path)
        configs.append(cfg)
        for cohort in cfg.cohorts:
            for group in cohort.agents:
                if group.kind != "llm":
                    continue
                if group.model not in models:
                    errors.append(f"{path.name}: unknown model {group.model}")
                    continue
                spec = models[group.model]
                if cfg.model_policy == "frontier_only" and not spec.frontier_eligible:
                    errors.append(f"{path.name}: {group.model} violates frontier-only policy")
                if cfg.model_policy == "mock_only" and spec.provider != "mock":
                    errors.append(f"{path.name}: {group.model} violates mock-only policy")
                if group.persona not in actual_profiles:
                    errors.append(f"{path.name}: unknown persona {group.persona}")

    registry = Registry(repo_root / "datasets")
    entries = registry.entries()
    acquired = sorted({entry.name for entry in entries})
    required = sorted({cfg.dataset for cfg in configs})
    missing = sorted(set(required) - set(acquired))
    blockers.extend(f"dataset not acquired: {name}" for name in missing)
    for entry in entries:
        path = registry.dataset_dir(entry.name)
        if not path.exists():
            errors.append(f"registered dataset payload is missing: {entry.name} -> {path}")
            continue
        for error in registry.verify(entry):
            if entry.files is None:
                warnings.append(f"{entry.name}: {error}")
            else:
                errors.append(f"{entry.name}: {error}")

    mphiq = _yaml(repo_root / "configs/designs/mphiq.yaml")
    mphiq_entries = mphiq["schemes"]["entries"]
    errors.extend(validate_mphiq_catalog([entry["code"] for entry in mphiq_entries]))
    if mphiq["schemes"]["expected_count"] != len(mphiq_entries):
        errors.append("MPHIQ expected_count does not match entries")
    prompts = _yaml(repo_root / "configs/prompts/pressure-treatments.yaml")
    pressure_cells = prompts["core_cells"]["cells"]
    if len(pressure_cells) != 24 or prompts["core_cells"]["expected_count"] != 24:
        errors.append("prompt-pressure catalog must contain 24 core cells")

    for experiment_id, experiment in program.experiments.items():
        if experiment.status == "blocked_external":
            blockers.append(f"{experiment_id}: {', '.join(experiment.dependencies)}")

    return RepositoryReadiness(
        scaffold_ok=not errors,
        execution_ready=not errors and not blockers,
        errors=errors,
        blockers=blockers,
        warnings=warnings,
        acquired_datasets=acquired,
        missing_datasets=missing,
        experiment_configs=len(configs),
        profiles=len(profile_paths),
        frontier_models=len(frontier),
        research_experiments=len(program.experiments),
    )


def verify_run(run_dir: Path, tolerance: float = 1e-6) -> RunVerification:
    """Verify decision completeness, grounding gates, fees, cost, and cash ledger."""
    import json

    run_dir = run_dir.resolve()
    with (run_dir / "manifest.json").open() as stream:
        manifest = json.load(stream)
    decisions = pd.read_json(run_dir / "decisions.jsonl", lines=True)
    fills = pd.read_parquet(run_dir / "fills.parquet")
    portfolio = pd.read_parquet(run_dir / "portfolio.parquet")
    decision_records = cast(
        list[DecisionRecord], decisions.to_dict(orient="records")
    )
    fill_records = cast(list[FillRecord], fills.to_dict(orient="records"))
    portfolio_records = cast(
        list[PortfolioRecord], portfolio.to_dict(orient="records")
    )
    errors: list[str] = []
    warnings: list[str] = []

    try:
        registry = Registry()
        registered = registry.get(manifest["dataset"]["name"])
        actual_dataset_hash = dataset_bundle_hash(registry.dataset_dir(registered.name))
        if actual_dataset_hash != manifest["dataset"]["sha256"]:
            errors.append("run manifest dataset hash does not match current dataset bundle")
    except (KeyError, FileNotFoundError):
        errors.append("run dataset cannot be resolved from the registry")

    expected_decisions = manifest["n_agents"] * manifest["n_steps"]
    if len(decisions) != expected_decisions:
        errors.append(f"decision rows {len(decisions)} != expected {expected_decisions}")
    if decisions.duplicated(["agent_id", "step"]).any():
        errors.append("duplicate agent-step decisions")
    expected_portfolios = expected_decisions
    if len(portfolio) != expected_portfolios:
        errors.append(f"portfolio rows {len(portfolio)} != expected {expected_portfolios}")
    if portfolio.duplicated(["agent_id", "step"]).any():
        errors.append("duplicate agent-step portfolio rows")

    known_agents = set(manifest["agents"])
    known_decision_agents = set(decisions["agent_id"])
    if known_agents != known_decision_agents:
        errors.append("manifest and decision agent sets differ")
    if fill_records and not {record["agent_id"] for record in fill_records}.issubset(
        known_agents
    ):
        errors.append("fills contain an unknown agent")

    for record in decision_records:
        symbols = set(record.get("symbols", []))
        if not symbols:
            errors.append(
                f"{record['agent_id']} step {record['step']}: missing symbol universe"
            )
            continue
        for order in record["orders_clipped"]:
            if order["symbol"] not in symbols or float(order["quantity"]) <= 0:
                errors.append(
                    f"{record['agent_id']} step {record['step']}: invalid clipped order"
                )
        meta = manifest["agents"].get(record["agent_id"], {})
        if meta.get("kind") == "llm":
            if not record["prompt_hash"] or not record["raw_response_hash"]:
                errors.append(
                    f"{record['agent_id']} step {record['step']}: "
                    "missing prompt/response hash"
                )
            if meta.get("grounding_mode") == "strict" and not record["grounding_ok"]:
                errors.append(
                    f"{record['agent_id']} step {record['step']}: strict grounding failure"
                )

    usage_cost = sum(
        float((record.get("usage") or {}).get("cost_usd", 0.0))
        for record in decision_records
    )
    if not np.isclose(usage_cost, manifest["total_cost_usd"], atol=tolerance, rtol=0):
        errors.append("manifest total cost does not reconcile with decision usage")

    initial_cash = float(manifest["config"]["initial_cash"])
    fee_bps = float(manifest["config"]["market"]["fee_bps"])
    cash = dict.fromkeys(known_agents, initial_cash)
    fills_by_step: dict[int, list[FillRecord]] = {}
    for record in fill_records:
        fills_by_step.setdefault(record["step"], []).append(record)
    portfolios_by_step: dict[int, list[PortfolioRecord]] = {}
    for record in portfolio_records:
        portfolios_by_step.setdefault(record["step"], []).append(record)
    for step in range(manifest["n_steps"]):
        for fill in fills_by_step.get(step, []):
            expected_fee = abs(fill["price"] * fill["quantity"]) * fee_bps / 1e4
            if not np.isclose(fill["fee"], expected_fee, atol=tolerance, rtol=1e-9):
                errors.append(f"fill fee mismatch at step {step} for {fill['agent_id']}")
            gross = fill["price"] * fill["quantity"]
            net = gross - fill["fee"] if fill["side"] == "sell" else -gross - fill["fee"]
            cash[fill["agent_id"]] += net
        for record in portfolios_by_step.get(step, []):
            if not np.isclose(
                record["cash"], cash[record["agent_id"]], atol=tolerance, rtol=1e-9
            ):
                errors.append(
                    f"cash ledger mismatch at step {step} for {record['agent_id']}"
                )

    parse_results: dict[str, list[bool]] = {}
    for record in decision_records:
        parse_results.setdefault(record["agent_id"], []).append(record["parse_ok"])
    if any(
        1 - sum(results) / len(results) > 0.2
        for results in parse_results.values()
    ):
        errors.append("one or more agents exceed the preregistered 20% parse-failure gate")
    return RunVerification(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        decisions=len(decisions),
        fills=len(fills),
        portfolio_rows=len(portfolio),
    )
