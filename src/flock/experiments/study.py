"""Deterministic compiler from a strict study specification to a frozen run plan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field

from flock.core.study import ExactCountsSpec, StageSpec, StrictFrozenModel, StudySpec
from flock.experiments.costs import PricingCatalog, load_pricing


class CompiledStage(StrictFrozenModel):
    stage_id: str
    order: int
    authorization_stage: str
    design: str
    trajectory_ids: tuple[str, ...]
    cohort_ids: tuple[str, ...]
    seeds: tuple[int, ...]
    design_cells: tuple[str, ...]
    exact_counts: ExactCountsSpec
    calls_by_pricing_key: dict[str, int]
    planned_cost_usd: float
    estimand_ids: tuple[str, ...]
    output_ids: tuple[str, ...]


class FrozenStudyPlan(StrictFrozenModel):
    schema_version: int
    study_id: str
    title: str
    source_spec: StudySpec
    stages: tuple[CompiledStage, ...]
    exact_runs: int = Field(gt=0)
    exact_steps: int = Field(gt=0)
    exact_agent_steps: int = Field(gt=0)
    exact_calls: int = Field(ge=0)
    planned_cost_usd: float = Field(ge=0, allow_inf_nan=False)
    plan_hash: str

    def to_jsonable(self) -> dict[str, Any]:
        """Return the frozen plan using only JSON-native values."""
        return self.model_dump(mode="json")


def _index_unique(items: list[Any], field: str, kind: str) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    for item in items:
        identifier = getattr(item, field)
        if identifier in indexed:
            raise ValueError(f"duplicate {kind} ID: {identifier}")
        indexed[identifier] = item
    return indexed


def _require_unique(values: list[Any], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} contains duplicates")


def _validate_real_window_independence(spec: StudySpec) -> None:
    real = sorted(
        (trajectory for trajectory in spec.trajectories if trajectory.source == "real"),
        key=lambda item: (item.market_id, item.start_date, item.end_date, item.trajectory_id),
    )
    for index, left in enumerate(real):
        for right in real[index + 1 :]:
            if right.market_id != left.market_id:
                continue
            overlaps = max(left.start_date, right.start_date) <= min(left.end_date, right.end_date)
            if overlaps and left.dependence_cluster_id != right.dependence_cluster_id:
                raise ValueError(
                    "overlapping real windows cannot be marked independent: "
                    f"{left.trajectory_id} and {right.trajectory_id}"
                )


def _design_cells(stage: StageSpec, pair_index: dict[str, Any]) -> tuple[str, ...]:
    if stage.design == "replay":
        return ("replay",)
    if stage.design == "capital_share":
        return tuple(sorted(stage.capital_share_level_ids))
    codes: set[str] = set()
    for pair_id in stage.mphiq_pair_ids:
        pair = pair_index[pair_id]
        codes.update((pair.different_code, pair.same_code))
    return tuple(sorted(codes))


def _compile_stage(
    stage: StageSpec,
    cohort_index: dict[str, Any],
    pair_index: dict[str, Any],
) -> CompiledStage:
    cohorts = [cohort_index[cohort_id] for cohort_id in stage.cohort_ids]
    agents_per_run = sum(cohort.total_agents for cohort in cohorts)
    llm_agents_per_run = sum(
        cohort.total_agents for cohort in cohorts if cohort.technology == "llm"
    )
    cells = _design_cells(stage, pair_index)
    runs = len(stage.trajectory_ids) * len(stage.seeds) * len(cells)
    steps = runs * stage.steps_per_run
    exact = ExactCountsSpec(
        runs=runs,
        steps=steps,
        agents_per_run=agents_per_run,
        agent_steps=steps * agents_per_run,
        calls=steps * llm_agents_per_run * stage.calls_per_llm_agent_step,
    )
    calls_by_pricing_key: dict[str, int] = {}
    for cohort in cohorts:
        if cohort.technology != "llm":
            continue
        for allocation in cohort.allocations:
            if allocation.pricing_key is None:
                raise ValueError(
                    f"{stage.stage_id}: LLM allocation {allocation.model_id} lacks pricing_key"
                )
            calls_by_pricing_key[allocation.pricing_key] = (
                calls_by_pricing_key.get(allocation.pricing_key, 0)
                + steps * allocation.count * stage.calls_per_llm_agent_step
            )
    if sum(calls_by_pricing_key.values()) != exact.calls:
        raise ValueError(f"{stage.stage_id}: model call allocation does not reconcile")
    if exact != stage.expected_counts:
        raise ValueError(
            f"{stage.stage_id}: declared exact counts do not match compiler counts; "
            f"declared={stage.expected_counts.model_dump()}, computed={exact.model_dump()}"
        )
    if exact.calls > stage.budget_cap.max_calls:
        raise ValueError(f"{stage.stage_id}: design exceeds stage call cap")
    if stage.planned_cost_usd > stage.budget_cap.max_cost_usd:
        raise ValueError(f"{stage.stage_id}: planned cost exceeds stage cost cap")
    return CompiledStage(
        stage_id=stage.stage_id,
        order=stage.order,
        authorization_stage=stage.authorization_stage,
        design=stage.design,
        trajectory_ids=tuple(sorted(stage.trajectory_ids)),
        cohort_ids=tuple(sorted(stage.cohort_ids)),
        seeds=tuple(sorted(stage.seeds)),
        design_cells=cells,
        exact_counts=exact,
        calls_by_pricing_key=calls_by_pricing_key,
        planned_cost_usd=stage.planned_cost_usd,
        estimand_ids=tuple(sorted(stage.estimand_ids)),
        output_ids=tuple(sorted(stage.output_ids)),
    )


def _validate_h1_matched_design(stage: StageSpec, cohort_index: dict[str, Any]) -> None:
    """Require family-rotated homogeneous controls matched to heterogeneous cells."""
    if "h1-kappa-contrast" not in stage.estimand_ids:
        return
    cohorts = [cohort_index[cohort_id] for cohort_id in stage.cohort_ids]
    research = [cohort for cohort in cohorts if cohort.technology in {"llm", "classical"}]
    expected_sizes = {cohort.total_agents for cohort in research}
    if len(expected_sizes) != 1:
        raise ValueError(f"{stage.stage_id}: H1 cohorts must have matched agent counts")
    for technology in ("llm", "classical"):
        homogeneous = [
            cohort
            for cohort in research
            if cohort.technology == technology and cohort.ecology == "homogeneous"
        ]
        heterogeneous = [
            cohort
            for cohort in research
            if cohort.technology == technology and cohort.ecology == "heterogeneous"
        ]
        if len(heterogeneous) != 1 or len(homogeneous) < 2:
            raise ValueError(
                f"{stage.stage_id}: {technology} H1 requires one heterogeneous cohort and "
                "at least two family-specific homogeneous cohorts"
            )
        homogeneous_families = {cohort.allocations[0].family for cohort in homogeneous}
        heterogeneous_families = {
            allocation.family for allocation in heterogeneous[0].allocations
        }
        if homogeneous_families != heterogeneous_families:
            raise ValueError(
                f"{stage.stage_id}: {technology} homogeneous family rotation must exactly "
                "match heterogeneous families"
            )


def load_study_spec(path: Path = Path("configs/studies/paper-core.yaml")) -> StudySpec:
    """Load and strictly validate a study YAML contract."""
    with path.open() as file:
        raw = yaml.safe_load(file)
    if not isinstance(raw, dict):
        raise ValueError("study YAML must contain one mapping")
    return StudySpec.model_validate(raw)


def compile_study(
    spec: StudySpec, pricing: PricingCatalog | None = None
) -> FrozenStudyPlan:
    """Validate cross-references and deterministically freeze exact execution counts."""
    if len(spec.stages) > spec.max_stages:
        raise ValueError(
            f"design has {len(spec.stages)} stages, exceeding stage cap {spec.max_stages}"
        )

    cluster_index = _index_unique(spec.dependence_clusters, "cluster_id", "cluster")
    trajectory_index = _index_unique(spec.trajectories, "trajectory_id", "trajectory")
    cohort_index = _index_unique(spec.cohorts, "cohort_id", "cohort")
    pair_index = _index_unique(spec.mphiq_pairs, "pair_id", "MPHIQ pair")
    capital_index = _index_unique(spec.capital_share_levels, "level_id", "capital-share level")
    estimand_index = _index_unique(spec.estimands, "estimand_id", "estimand")
    output_index = _index_unique(spec.required_outputs, "output_id", "output")
    stage_index = _index_unique(spec.stages, "stage_id", "stage")

    if len(stage_index) != len(spec.stages):  # defensive; _index_unique already raises
        raise ValueError("stage IDs must be unique")
    orders = [stage.order for stage in spec.stages]
    if sorted(orders) != list(range(1, len(spec.stages) + 1)):
        raise ValueError("stage order must be unique and contiguous from one")
    authorization_order = {"canary": 0, "pilot": 1, "confirmatory": 2}
    authorizations = [authorization_order[stage.authorization_stage] for stage in spec.stages]
    if authorizations != sorted(authorizations):
        raise ValueError("authorization stages must progress canary to pilot to confirmatory")

    for trajectory in spec.trajectories:
        if trajectory.dependence_cluster_id not in cluster_index:
            raise ValueError(
                f"{trajectory.trajectory_id}: unknown dependence cluster "
                f"{trajectory.dependence_cluster_id}"
            )
    _validate_real_window_independence(spec)

    llm_families = {
        allocation.family
        for cohort in spec.cohorts
        if cohort.technology == "llm"
        for allocation in cohort.allocations
    }
    _require_unique(spec.held_out_families, "held_out_families")
    unknown_held_out = set(spec.held_out_families) - llm_families
    if unknown_held_out:
        raise ValueError(
            f"held-out model families are not in the design: {sorted(unknown_held_out)}"
        )

    pricing = pricing or load_pricing()
    llm_pricing_keys = {
        allocation.pricing_key
        for cohort in spec.cohorts
        if cohort.technology == "llm"
        for allocation in cohort.allocations
    }
    if None in llm_pricing_keys:
        raise ValueError("every LLM allocation requires a pricing_key")
    missing_prices = llm_pricing_keys - set(pricing.api)
    if missing_prices:
        raise ValueError(f"LLM allocations have no dated pricing: {sorted(missing_prices)}")

    shares = [level.ai_share_bps for level in spec.capital_share_levels]
    _require_unique(shares, "H5 capital-share levels")

    for output in spec.required_outputs:
        _require_unique(output.estimand_ids, f"{output.output_id} estimand_ids")
        missing = set(output.estimand_ids) - set(estimand_index)
        if missing:
            raise ValueError(f"{output.output_id}: unknown estimands {sorted(missing)}")

    compiled_stages: list[CompiledStage] = []
    for stage in sorted(spec.stages, key=lambda item: item.order):
        for values, label, index in (
            (stage.trajectory_ids, "trajectory_ids", trajectory_index),
            (stage.cohort_ids, "cohort_ids", cohort_index),
            (stage.mphiq_pair_ids, "mphiq_pair_ids", pair_index),
            (stage.capital_share_level_ids, "capital_share_level_ids", capital_index),
            (stage.estimand_ids, "estimand_ids", estimand_index),
            (stage.output_ids, "output_ids", output_index),
        ):
            _require_unique(values, f"{stage.stage_id} {label}")
            missing = set(values) - set(index)
            if missing:
                raise ValueError(f"{stage.stage_id}: unknown {label} {sorted(missing)}")
        _require_unique(stage.seeds, f"{stage.stage_id} seeds")
        _validate_h1_matched_design(stage, cohort_index)
        if stage.design == "capital_share":
            stage_shares = [
                capital_index[level].ai_share_bps
                for level in stage.capital_share_level_ids
            ]
            if 0 not in stage_shares:
                raise ValueError(
                    f"{stage.stage_id}: capital-share design requires a zero-AI control"
                )
            totals = {
                capital_index[level].total_capital_usd
                for level in stage.capital_share_level_ids
            }
            if len(totals) != 1:
                raise ValueError(f"{stage.stage_id}: H5 levels must hold total capital fixed")
        compiled_stages.append(_compile_stage(stage, cohort_index, pair_index))

    exact_runs = sum(stage.exact_counts.runs for stage in compiled_stages)
    exact_steps = sum(stage.exact_counts.steps for stage in compiled_stages)
    exact_agent_steps = sum(stage.exact_counts.agent_steps for stage in compiled_stages)
    exact_calls = sum(stage.exact_counts.calls for stage in compiled_stages)
    planned_cost = sum(stage.planned_cost_usd for stage in compiled_stages)
    canary_cost = sum(
        stage.planned_cost_usd
        for stage in compiled_stages
        if stage.authorization_stage == "canary"
    )
    pilot_cost = sum(
        stage.planned_cost_usd
        for stage in compiled_stages
        if stage.authorization_stage == "pilot"
    )
    if canary_cost > 50:
        raise ValueError("canary authorization exceeds the $50 hard ceiling")
    if pilot_cost > 5_200:
        raise ValueError("pilot authorization exceeds the $5,200 hard ceiling")
    if exact_calls > spec.budget_cap.max_calls:
        raise ValueError("design exceeds global call cap")
    if planned_cost > spec.budget_cap.max_cost_usd:
        raise ValueError("design exceeds global cost cap")

    payload = {
        "schema_version": spec.schema_version,
        "study_id": spec.study_id,
        "title": spec.title,
        "source_spec": spec.model_dump(mode="json"),
        "stages": [stage.model_dump(mode="json") for stage in compiled_stages],
        "exact_runs": exact_runs,
        "exact_steps": exact_steps,
        "exact_agent_steps": exact_agent_steps,
        "exact_calls": exact_calls,
        "planned_cost_usd": planned_cost,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return FrozenStudyPlan(
        schema_version=spec.schema_version,
        study_id=spec.study_id,
        title=spec.title,
        source_spec=spec,
        stages=tuple(compiled_stages),
        exact_runs=exact_runs,
        exact_steps=exact_steps,
        exact_agent_steps=exact_agent_steps,
        exact_calls=exact_calls,
        planned_cost_usd=planned_cost,
        plan_hash=hashlib.sha256(canonical.encode()).hexdigest(),
    )


def compile_study_file(path: Path = Path("configs/studies/paper-core.yaml")) -> FrozenStudyPlan:
    """Load and compile one study YAML file."""
    return compile_study(load_study_spec(path))
