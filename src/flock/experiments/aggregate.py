"""Deterministically aggregate verified raw runs into first-paper inputs.

The compiler deliberately stops at family, lineage-pair, and MPHIQ-cell
aggregates.  Seeds, agents, pairs, steps, retries, and calls remain nested
observations and never become independent rows.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import pandas as pd

from flock.analysis import convergence
from flock.analysis.crossed import H4_COMPONENTS
from flock.core.config import ExperimentConfig
from flock.experiments.materialize import MaterializedStudy, RunAssignment
from flock.experiments.verify import verify_run

RAW_RUN_INPUTS = (
    "manifest.json",
    "decisions.jsonl",
    "fills.parquet",
    "portfolio.parquet",
    "market_events.jsonl",
)
AGGREGATION_ARTIFACTS = (
    "crossed_rows.parquet",
    "lineage_rows.parquet",
    "mphiq_rows.parquet",
)


@dataclass(frozen=True)
class AggregationResult:
    output_dir: Path
    study_id: str
    evidence_kind: Literal["mock", "real"]
    independent_blocks: int
    source_runs: int
    aggregation_hash: str


@dataclass(frozen=True)
class _VerifiedRun:
    assignment: RunAssignment
    run_dir: Path
    run_id: str
    manifest: dict[str, Any]
    decisions: pd.DataFrame
    portfolio: pd.DataFrame
    input_hashes: dict[str, str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _load_assignments(path: Path) -> MaterializedStudy:
    try:
        materialized = MaterializedStudy.model_validate_json(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f"invalid materialized assignment bundle: {path}") from error
    assignments = list(materialized.assignments)
    ids = [item.assignment_id for item in assignments]
    ordinals = [item.ordinal for item in assignments]
    if len(ids) != len(set(ids)):
        raise ValueError("materialized assignment bundle contains duplicate assignment IDs")
    if sorted(ordinals) != list(range(1, len(assignments) + 1)):
        raise ValueError("materialized assignment ordinals must be unique and contiguous")
    if materialized.exact_runs != len(assignments):
        raise ValueError("materialized exact_runs does not reconcile with assignments")
    totals = (
        sum(item.exact_counts.steps for item in assignments),
        sum(item.exact_counts.agent_steps for item in assignments),
        sum(item.exact_counts.calls for item in assignments),
        sum(item.execution_config is not None for item in assignments),
    )
    expected = (
        materialized.exact_steps,
        materialized.exact_agent_steps,
        materialized.exact_calls,
        materialized.executable_runs,
    )
    if totals != expected:
        raise ValueError("materialized assignment totals do not reconcile")
    plan_hashes = {item.plan_hash for item in assignments}
    study_ids = {item.study_id for item in assignments}
    if plan_hashes != {materialized.plan_hash} or study_ids != {materialized.study_id}:
        raise ValueError("assignment study or plan lineage does not match its bundle")
    payload = [item.model_dump(mode="json") for item in assignments]
    expected_hash = hashlib.sha256(_canonical(payload).encode()).hexdigest()
    if materialized.materialization_hash != expected_hash:
        raise ValueError("materialization hash does not match assignment content")
    return materialized


def _first_paper_assignments(
    materialized: MaterializedStudy,
) -> tuple[list[RunAssignment], list[RunAssignment], dict[str, tuple[str, str]]]:
    replay = sorted(
        (
            item
            for item in materialized.assignments
            if item.authorization_stage == "confirmatory" and item.design == "replay"
        ),
        key=lambda item: item.ordinal,
    )
    mphiq = sorted(
        (
            item
            for item in materialized.assignments
            if item.authorization_stage == "confirmatory" and item.design == "mphiq"
        ),
        key=lambda item: item.ordinal,
    )
    if not replay or not mphiq:
        raise ValueError("aggregation requires confirmatory replay and MPHIQ assignments")

    replay_blocks = {item.trajectory_id for item in replay}
    mphiq_blocks = {item.trajectory_id for item in mphiq}
    if replay_blocks != mphiq_blocks:
        raise ValueError(
            "confirmatory replay and MPHIQ must use exactly the same independent blocks: "
            f"replay_only={sorted(replay_blocks - mphiq_blocks)}, "
            f"mphiq_only={sorted(mphiq_blocks - replay_blocks)}"
        )
    if len(replay_blocks) < 2:
        raise ValueError("aggregation requires at least two independent blocks")
    unresolved = [item.assignment_id for item in (*replay, *mphiq) if item.execution_config is None]
    if unresolved:
        raise ValueError(
            f"{len(unresolved)} first-paper assignments are not executable; first={unresolved[0]}"
        )

    identities: dict[str, tuple[str, str]] = {}
    cluster_blocks: dict[str, str] = {}
    trajectory_blocks: dict[str, str] = {}
    for item in (*replay, *mphiq):
        block = item.trajectory_id
        identity = (item.dependence_cluster_id, item.trajectory_id)
        if block in identities and identities[block] != identity:
            raise ValueError(f"assignments disagree on lineage for block {block!r}")
        prior_cluster = cluster_blocks.get(item.dependence_cluster_id)
        prior_trajectory = trajectory_blocks.get(item.trajectory_id)
        if prior_cluster not in {None, block} or prior_trajectory not in {None, block}:
            raise ValueError(
                "a dependence cluster or trajectory cannot create multiple independent blocks"
            )
        identities[block] = identity
        cluster_blocks[item.dependence_cluster_id] = block
        trajectory_blocks[item.trajectory_id] = block

    replay_seeds = {
        block: {item.seed for item in replay if item.trajectory_id == block}
        for block in replay_blocks
    }
    if any(seeds != next(iter(replay_seeds.values())) for seeds in replay_seeds.values()):
        raise ValueError("confirmatory replay seed coverage differs across independent blocks")
    replay_cells = {
        (item.trajectory_id, item.seed, item.cell.cell_id) for item in replay
    }
    if len(replay_cells) != len(replay):
        raise ValueError("duplicate confirmatory replay block/seed/cell assignment")

    expected_codes = {f"{value:05b}" for value in range(32)}
    mphiq_keys = {
        (item.trajectory_id, item.seed, item.cell.mphiq_code) for item in mphiq
    }
    if len(mphiq_keys) != len(mphiq):
        raise ValueError("duplicate MPHIQ block/seed/code assignment")
    mphiq_seeds: dict[str, set[int]] = {}
    for block in mphiq_blocks:
        seeds = {item.seed for item in mphiq if item.trajectory_id == block}
        mphiq_seeds[block] = seeds
        for seed in seeds:
            codes = {
                item.cell.mphiq_code
                for item in mphiq
                if item.trajectory_id == block and item.seed == seed
            }
            if codes != expected_codes:
                raise ValueError(
                    f"MPHIQ block {block!r} seed {seed} does not contain all 32 schemes"
                )
    if any(seeds != next(iter(mphiq_seeds.values())) for seeds in mphiq_seeds.values()):
        raise ValueError("MPHIQ seed coverage differs across independent blocks")
    return replay, mphiq, identities


def _load_verified_runs(
    assignments: list[RunAssignment], results_root: Path
) -> tuple[list[_VerifiedRun], Literal["mock", "real"]]:
    expected = {item.assignment_id: item for item in assignments}
    candidates: dict[str, list[tuple[Path, dict[str, Any]]]] = {
        assignment_id: [] for assignment_id in expected
    }
    if not results_root.is_dir():
        raise ValueError(f"results root does not exist: {results_root}")
    for run_dir in sorted(results_root.iterdir()):
        manifest_path = run_dir / "manifest.json"
        if not run_dir.is_dir() or not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid completed run manifest: {manifest_path}") from error
        if not isinstance(manifest, dict):
            raise ValueError(f"run manifest must contain one object: {manifest_path}")
        config = manifest.get("config")
        name = config.get("name") if isinstance(config, dict) else None
        if isinstance(name, str) and name in candidates:
            candidates[name].append((run_dir, cast(dict[str, Any], manifest)))

    loaded: list[_VerifiedRun] = []
    run_ids: set[str] = set()
    evidence_kinds: set[Literal["mock", "real"]] = set()
    for assignment_id in sorted(expected):
        matches = candidates[assignment_id]
        if not matches:
            raise ValueError(f"missing completed raw run for assignment {assignment_id}")
        if len(matches) != 1:
            raise ValueError(f"duplicate completed raw runs for assignment {assignment_id}")
        run_dir, manifest = matches[0]
        assignment = expected[assignment_id]
        if manifest.get("status") != "complete":
            raise ValueError(f"raw run is incomplete: {run_dir}")
        run_id = str(manifest.get("run_id", "")).strip()
        if not run_id or run_id in run_ids:
            raise ValueError(f"raw run IDs must be nonempty and unique: {run_id!r}")
        run_ids.add(run_id)

        assert assignment.execution_config is not None
        try:
            expected_config = ExperimentConfig.model_validate(assignment.execution_config)
            actual_config = ExperimentConfig.model_validate(manifest.get("config"))
        except ValueError as error:
            raise ValueError(f"run config schema violation: {run_dir}") from error
        if expected_config.model_dump(mode="json") != actual_config.model_dump(mode="json"):
            raise ValueError(f"run config does not match frozen assignment: {assignment_id}")
        if (
            actual_config.independent_block != assignment.trajectory_id
            or actual_config.trajectory_id != assignment.trajectory_id
            or actual_config.dependence_cluster != assignment.dependence_cluster_id
            or actual_config.seed != assignment.seed
        ):
            raise ValueError(f"run lineage does not match assignment: {assignment_id}")

        missing_files = [name for name in RAW_RUN_INPUTS if not (run_dir / name).is_file()]
        if missing_files:
            raise ValueError(f"raw run {run_id} is incomplete; missing={missing_files}")
        verification = verify_run(run_dir)
        if not verification.ok:
            raise ValueError(f"raw run failed verification: {run_id}: {verification.errors}")
        try:
            run = convergence.load_run(run_dir)
        except Exception as error:
            raise ValueError(f"raw run payload parse violation: {run_id}") from error
        decisions = cast(pd.DataFrame, run["decisions"])
        portfolio = cast(pd.DataFrame, run["portfolio"])
        required_decisions = {"agent_id", "step", "cohort", "parse_ok", "action"}
        required_portfolio = {"agent_id", "step", "cohort", "weights"}
        if missing := sorted(required_decisions - set(decisions.columns)):
            raise ValueError(f"raw run {run_id} decision schema missing {missing}")
        if missing := sorted(required_portfolio - set(portfolio.columns)):
            raise ValueError(f"raw run {run_id} portfolio schema missing {missing}")
        if decisions.empty or portfolio.empty:
            raise ValueError(f"raw run {run_id} has empty decision or portfolio payload")
        parse_status = cast(pd.Series, decisions["parse_ok"])
        if not pd.api.types.is_bool_dtype(parse_status.dtype) or bool(
            parse_status.isna().any()
        ):
            raise ValueError(f"raw run {run_id} has invalid parse status values")

        manifest_agents = manifest.get("agents")
        if not isinstance(manifest_agents, dict) or set(manifest_agents) != set(
            decisions["agent_id"].astype(str)
        ):
            raise ValueError(f"raw run {run_id} agent manifest does not match decisions")
        if set(portfolio["agent_id"].astype(str)) != set(manifest_agents):
            raise ValueError(f"raw run {run_id} agent manifest does not match portfolios")
        if assignment.design == "mphiq":
            code = assignment.cell.mphiq_code
            if code is None or "mphiq_treatment" not in decisions.columns:
                raise ValueError(f"MPHIQ run {run_id} lacks treatment rows")
            treatment_codes = {
                str(value.get("scheme_code", ""))
                for value in decisions["mphiq_treatment"]
                if isinstance(value, dict)
            }
            treatments = cast(pd.Series, decisions["mphiq_treatment"])
            if treatment_codes != {code} or bool(treatments.isna().any()):
                raise ValueError(f"MPHIQ run {run_id} treatment lineage does not match {code}")
            treatment_rows = cast(
                pd.DataFrame, decisions[["agent_id", "mphiq_treatment"]]
            )
            for record in treatment_rows.to_dict("records"):
                agent_id = str(record["agent_id"])
                expected_treatment = cast(dict[str, Any], manifest_agents[agent_id]).get(
                    "mphiq_treatment"
                )
                if record["mphiq_treatment"] != expected_treatment:
                    raise ValueError(
                        f"MPHIQ run {run_id} decision treatment differs from its manifest"
                    )

        llm_agents = [
            cast(dict[str, Any], meta)
            for meta in manifest_agents.values()
            if cast(dict[str, Any], meta).get("kind") == "llm"
        ]
        mock_model_detected = any(
            str(meta.get("model_id", meta.get("model", ""))).startswith("mock-")
            for meta in llm_agents
        )
        if actual_config.model_policy == "frontier_only" and mock_model_detected:
            raise ValueError(f"mock raw run was declared as real evidence: {run_id}")
        kind: Literal["mock", "real"] = (
            "mock" if actual_config.model_policy == "mock_only" else "real"
        )
        evidence_kinds.add(kind)
        loaded.append(
            _VerifiedRun(
                assignment=assignment,
                run_dir=run_dir,
                run_id=run_id,
                manifest=manifest,
                decisions=decisions,
                portfolio=portfolio,
                input_hashes={
                    name: _sha256(run_dir / name) for name in RAW_RUN_INPUTS
                },
            )
        )
    if len(evidence_kinds) != 1:
        raise ValueError("first-paper raw runs cannot mix mock and real evidence")
    return loaded, next(iter(evidence_kinds))


def _agent_family_map(
    run: _VerifiedRun, cohort_id: str
) -> tuple[dict[str, list[str]], dict[str, tuple[str, str]]]:
    source = next(
        (cohort for cohort in run.assignment.cohorts if cohort.cohort_id == cohort_id),
        None,
    )
    if source is None:
        raise ValueError(f"assignment lacks cohort contract {cohort_id!r}")
    manifest_agents = cast(dict[str, dict[str, Any]], run.manifest["agents"])
    agents = {
        agent_id: meta
        for agent_id, meta in manifest_agents.items()
        if str(meta.get("cohort", "")) == cohort_id
    }
    if not agents:
        raise ValueError(f"run {run.run_id} lacks agents for cohort {cohort_id!r}")
    allocation_by_model = {item.model_id: item for item in source.allocations}
    families: dict[str, list[str]] = {}
    lineage: dict[str, tuple[str, str]] = {}
    if source.technology == "llm":
        for agent_id, meta in agents.items():
            model_id = str(meta.get("model_id", ""))
            allocation = allocation_by_model.get(model_id)
            if allocation is None:
                raise ValueError(f"run {run.run_id} has an undeclared model {model_id!r}")
            families.setdefault(allocation.family, []).append(agent_id)
            lineage[agent_id] = (allocation.model_id, allocation.provider)
    else:
        config = cast(dict[str, Any], run.manifest["config"])
        config_cohort = next(
            cohort for cohort in cast(list[dict[str, Any]], config["cohorts"])
            if cohort["name"] == cohort_id
        )
        groups = cast(list[dict[str, Any]], config_cohort["agents"])
        if len(groups) != len(source.allocations):
            raise ValueError(f"run {run.run_id} baseline allocation schema drift")
        allocation_by_kind: dict[str, Any] = {}
        for group, allocation in zip(groups, source.allocations, strict=True):
            kind = str(group.get("kind", ""))
            if kind in allocation_by_kind:
                raise ValueError(f"ambiguous baseline kind {kind!r} in {cohort_id}")
            allocation_by_kind[kind] = allocation
        for agent_id, meta in agents.items():
            kind = str(meta.get("kind", ""))
            allocation = allocation_by_kind.get(kind)
            if allocation is None:
                raise ValueError(f"run {run.run_id} has an undeclared baseline {kind!r}")
            families.setdefault(allocation.family, []).append(agent_id)
    for family_agents in families.values():
        family_agents.sort()
        if len(family_agents) < 2:
            raise ValueError("family-level convergence requires at least two nested agents")
    return families, lineage


def _kappa(run: _VerifiedRun, agents: list[str]) -> float:
    value = convergence.mean_pairwise_kappa(
        convergence.action_matrix(run.decisions, sorted(agents))
    )
    if not np.isfinite(value):
        raise ValueError(f"run {run.run_id} produced a non-finite kappa aggregate")
    return float(value)


def _crossed_and_lineage_rows(
    runs: list[_VerifiedRun], identities: dict[str, tuple[str, str]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    family_values: dict[tuple[str, str, str, str], list[tuple[float, str]]] = {}
    pair_values: dict[tuple[str, str, str, str], list[tuple[float, str]]] = {}
    runs_by_block: dict[str, list[_VerifiedRun]] = {}
    for run in runs:
        block = run.assignment.trajectory_id
        runs_by_block.setdefault(block, []).append(run)
        llm_heterogeneous: list[tuple[str, dict[str, tuple[str, str]]]] = []
        for cohort in run.assignment.cohorts:
            if cohort.technology == "null":
                continue
            families, lineage = _agent_family_map(run, cohort.cohort_id)
            for family, agents in families.items():
                key = (block, cohort.technology, cohort.ecology, family)
                family_values.setdefault(key, []).append((_kappa(run, agents), run.run_id))
            if cohort.technology == "llm" and cohort.ecology == "heterogeneous":
                llm_heterogeneous.append((cohort.cohort_id, lineage))
        if len(llm_heterogeneous) != 1:
            raise ValueError(
                f"run {run.run_id} requires exactly one heterogeneous LLM cohort for H3"
            )
        cohort_id, lineage = llm_heterogeneous[0]
        agents = sorted(lineage)
        matrix = convergence.action_matrix(run.decisions, agents)
        for left, right in itertools.combinations(agents, 2):
            left_model, left_provider = lineage[left]
            right_model, right_provider = lineage[right]
            if left_model == right_model:
                relationship = "same_model"
                stratum = left_model
            elif left_provider == right_provider:
                relationship = "same_provider"
                stratum = left_provider
            else:
                relationship = "cross_provider"
                stratum = "--".join(sorted((left_provider, right_provider)))
            pair_id = "--".join(sorted((left, right)))
            value = convergence.cohen_kappa(
                cast(pd.Series, matrix[left]), cast(pd.Series, matrix[right])
            )
            pair_values.setdefault(
                (block, relationship, stratum, pair_id), []
            ).append((float(value), run.run_id))
        if not cohort_id:
            raise ValueError("heterogeneous LLM cohort identifier cannot be empty")

    crossed: list[dict[str, Any]] = []
    for key, values in sorted(family_values.items()):
        block, technology, ecology, family = key
        expected_runs = {run.run_id for run in runs_by_block[block]}
        observed_runs = {run_id for _, run_id in values}
        if observed_runs != expected_runs or len(values) != len(expected_runs):
            raise ValueError(f"incomplete family aggregate for {key}")
        cluster, trajectory = identities[block]
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
                "value": float(np.mean([value for value, _ in values])),
                "source_run_ids": sorted(observed_runs),
            }
        )

    lineage_rows: list[dict[str, Any]] = []
    relationships_by_block: dict[str, set[str]] = {}
    for key, values in sorted(pair_values.items()):
        block, relationship, stratum, pair_id = key
        expected_runs = {run.run_id for run in runs_by_block[block]}
        observed_runs = {run_id for _, run_id in values}
        if observed_runs != expected_runs or len(values) != len(expected_runs):
            raise ValueError(f"incomplete lineage-pair aggregate for {key}")
        relationships_by_block.setdefault(block, set()).add(relationship)
        cluster, trajectory = identities[block]
        lineage_rows.append(
            {
                "independent_block": block,
                "dependence_cluster": cluster,
                "trajectory_id": trajectory,
                "metric": "kappa",
                "relationship": relationship,
                "family_stratum": stratum,
                "pair_id": pair_id,
                "value": float(np.mean([value for value, _ in values])),
                "source_run_ids": sorted(observed_runs),
            }
        )
    expected_relationships = {"same_model", "same_provider", "cross_provider"}
    if any(
        relationships_by_block.get(block) != expected_relationships for block in identities
    ):
        raise ValueError("each independent block requires all three H3 relationship classes")
    return pd.DataFrame(crossed), pd.DataFrame(lineage_rows)


def _mphiq_rows(
    runs: list[_VerifiedRun], identities: dict[str, tuple[str, str]]
) -> pd.DataFrame:
    values: dict[tuple[str, str], list[tuple[float, str]]] = {}
    pair_specs: dict[str, tuple[str, str, str]] = {}
    for run in runs:
        code = run.assignment.cell.mphiq_code
        if code is None:
            raise ValueError(f"MPHIQ assignment {run.assignment.assignment_id} lacks a code")
        cohort_ids = {cohort.cohort_id for cohort in run.assignment.cohorts}
        if len(cohort_ids) != 1:
            raise ValueError("MPHIQ runs require exactly one cohort")
        cohort_id = next(iter(cohort_ids))
        agents = sorted(
            run.decisions.loc[
                run.decisions["cohort"] == cohort_id, "agent_id"
            ].astype(str).unique()
        )
        values.setdefault((run.assignment.trajectory_id, code), []).append(
            (_kappa(run, agents), run.run_id)
        )
        for pair in run.assignment.cell.mphiq_pairs:
            definition = (pair.factor, pair.same_code, pair.different_code)
            if pair.pair_id in pair_specs and pair_specs[pair.pair_id] != definition:
                raise ValueError(f"MPHIQ pair definition drift for {pair.pair_id}")
            pair_specs[pair.pair_id] = definition
    if {factor for factor, _, _ in pair_specs.values()} != set(H4_COMPONENTS):
        raise ValueError("MPHIQ pair definitions do not cover all five components")

    runs_by_block_code = {
        key: {run_id for _, run_id in nested} for key, nested in values.items()
    }
    rows: list[dict[str, Any]] = []
    for block in sorted(identities):
        cluster, trajectory = identities[block]
        for pair_id, (factor, same_code, different_code) in sorted(pair_specs.items()):
            same_key = (block, same_code)
            different_key = (block, different_code)
            if same_key not in values or different_key not in values:
                raise ValueError(f"MPHIQ block {block!r} is incomplete for pair {pair_id}")
            same_values = values[same_key]
            different_values = values[different_key]
            if len(same_values) != len(runs_by_block_code[same_key]) or len(
                different_values
            ) != len(runs_by_block_code[different_key]):
                raise ValueError(f"duplicate MPHIQ seed result for pair {pair_id}")
            rows.append(
                {
                    "independent_block": block,
                    "dependence_cluster": cluster,
                    "trajectory_id": trajectory,
                    "metric": "kappa",
                    "component": factor,
                    "pair_id": pair_id,
                    "code_same": same_code,
                    "code_different": different_code,
                    "value_same": float(np.mean([value for value, _ in same_values])),
                    "value_different": float(
                        np.mean([value for value, _ in different_values])
                    ),
                    "source_run_ids": sorted(
                        runs_by_block_code[same_key] | runs_by_block_code[different_key]
                    ),
                }
            )
    return pd.DataFrame(rows)


def _write_parquet(frame: pd.DataFrame, path: Path, sort_columns: list[str]) -> None:
    ordered = frame.sort_values(sort_columns).reset_index(drop=True)
    ordered.to_parquet(path, index=False, compression=None, engine="pyarrow")


def aggregate_study(
    assignments_path: Path,
    output_dir: Path,
    *,
    results_root: Path = Path("results"),
) -> AggregationResult:
    """Compile verified first-paper raw runs into content-addressed aggregates."""
    assignments_path = assignments_path.resolve()
    output_dir = output_dir.resolve()
    results_root = results_root.resolve()
    if output_dir.exists():
        raise ValueError(f"aggregation output must not already exist: {output_dir}")
    temporary = output_dir.with_name(output_dir.name + ".tmp")
    if temporary.exists():
        raise ValueError(f"stale aggregation temporary directory exists: {temporary}")

    materialized = _load_assignments(assignments_path)
    replay_assignments, mphiq_assignments, identities = _first_paper_assignments(
        materialized
    )
    replay_runs, replay_kind = _load_verified_runs(replay_assignments, results_root)
    mphiq_runs, mphiq_kind = _load_verified_runs(mphiq_assignments, results_root)
    if replay_kind != mphiq_kind:
        raise ValueError("replay and MPHIQ evidence kinds do not match")
    evidence_kind = replay_kind
    crossed, lineage = _crossed_and_lineage_rows(replay_runs, identities)
    mphiq = _mphiq_rows(mphiq_runs, identities)

    cited = {
        str(run_id)
        for frame in (crossed, lineage, mphiq)
        for source_ids in frame["source_run_ids"]
        for run_id in source_ids
    }
    all_runs = sorted((*replay_runs, *mphiq_runs), key=lambda run: run.run_id)
    expected_run_ids = {run.run_id for run in all_runs}
    if len(expected_run_ids) != len(all_runs):
        raise ValueError("verified raw run IDs must be unique across replay and MPHIQ")
    if cited != expected_run_ids:
        raise ValueError(
            "aggregate provenance does not exactly cover selected verified runs: "
            f"missing={sorted(expected_run_ids - cited)}, "
            f"unexpected={sorted(cited - expected_run_ids)}"
        )

    temporary.mkdir(parents=True)
    _write_parquet(
        crossed,
        temporary / "crossed_rows.parquet",
        ["independent_block", "metric", "technology", "ecology", "family"],
    )
    _write_parquet(
        lineage,
        temporary / "lineage_rows.parquet",
        ["independent_block", "metric", "relationship", "family_stratum", "pair_id"],
    )
    _write_parquet(
        mphiq,
        temporary / "mphiq_rows.parquet",
        ["independent_block", "metric", "component", "pair_id"],
    )
    artifact_hashes = {
        name: _sha256(temporary / name) for name in AGGREGATION_ARTIFACTS
    }
    source_hashes = {
        run.run_id: run.input_hashes for run in all_runs
    }
    aggregation_payload = {
        "schema_version": 1,
        "study_id": materialized.study_id,
        "plan_hash": materialized.plan_hash,
        "materialization_hash": materialized.materialization_hash,
        "assignments_sha256": _sha256(assignments_path),
        "status": "complete",
        "evidence_kind": evidence_kind,
        "independent_blocks": sorted(identities),
        "source_assignment_ids": sorted(run.assignment.assignment_id for run in all_runs),
        "source_run_ids": sorted(expected_run_ids),
        "source_run_sha256": source_hashes,
        "artifact_sha256": artifact_hashes,
        "nested_units_not_counted": [
            "seed",
            "agent",
            "pair",
            "step",
            "call",
            "retry",
            "prompt variant",
            "response seed",
        ],
    }
    aggregation_hash = hashlib.sha256(
        _canonical(aggregation_payload).encode()
    ).hexdigest()
    manifest = {**aggregation_payload, "aggregation_hash": aggregation_hash}
    (temporary / "aggregation-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    temporary.replace(output_dir)
    return AggregationResult(
        output_dir=output_dir,
        study_id=materialized.study_id,
        evidence_kind=evidence_kind,
        independent_blocks=len(identities),
        source_runs=len(all_runs),
        aggregation_hash=aggregation_hash,
    )
