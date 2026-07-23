"""Materialize frozen study cells into auditable run assignments.

The study compiler freezes scientific design and aggregate counts.  This module
is the deliberately stricter boundary between that design and the existing
experiment runner: it enumerates every run, preserves its independent-unit
lineage and model allocations, and only emits an ``ExperimentConfig`` when all
runner-specific choices were supplied explicitly.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field, model_validator

from flock.agents.prompts import resolve_prompt
from flock.core.config import (
    AgentGroup,
    CohortConfig,
    ExperimentConfig,
    MarketConfig,
    ModelSpec,
    MPHIQAgentTreatment,
    RuntimeBudget,
    load_models,
    load_persona,
)
from flock.core.study import (
    BudgetCapSpec,
    CapitalShareLevelSpec,
    CohortSpec,
    ExactCountsSpec,
    ModelAllocationSpec,
    MPHIQPairAssignmentSpec,
    StrictFrozenModel,
    TrajectoryWindowSpec,
)
from flock.data.registry import Registry
from flock.experiments.study import CompiledStage, FrozenStudyPlan, load_study_plan


class StageExecutionDefaults(StrictFrozenModel):
    """Runner choices that cannot be inferred from the scientific design."""

    market: MarketConfig
    observation_window: int = Field(gt=0)
    initial_cash: float = Field(gt=0, allow_inf_nan=False)
    initial_position_per_symbol: float = Field(ge=0, allow_inf_nan=False)
    max_position_per_symbol: float = Field(gt=0, allow_inf_nan=False)
    persona_id: str | None = None
    prompt_id: str | None = None
    temperature: float = Field(default=0.7, ge=0, le=2, allow_inf_nan=False)
    memory: bool = False
    harness_id: str = "default"
    information_policy: str = "shared-all"
    grounding_mode: Literal["audit", "strict"] = "strict"
    runtime_budget: RuntimeBudget | None = None


class MPHIQHarnessPreset(StrictFrozenModel):
    """One preregistered harness level supported by the current runner."""

    level_id: str
    temperature: float = Field(ge=0, le=2, allow_inf_nan=False)
    memory: bool
    harness_id: str


class MPHIQExecutionLevels(StrictFrozenModel):
    """Explicit executable levels for the non-model MPHIQ factors."""

    persona_ids: list[str] = Field(min_length=2)
    harness_presets: list[MPHIQHarnessPreset] = Field(min_length=2)
    information_policies: list[
        Literal[
            "shared-all",
            "no-news",
            "price-only",
            "news-partition-a",
            "news-partition-b",
        ]
    ] = Field(min_length=2)
    prompt_ids: list[str] = Field(min_length=2)
    prompt_semantic_group: str

    def validate_unique_levels(self) -> tuple[str, ...]:
        errors: list[str] = []
        for label, values in (
            ("persona_ids", self.persona_ids),
            ("information_policies", self.information_policies),
            ("prompt_ids", self.prompt_ids),
        ):
            if len(values) != len(set(values)):
                errors.append(f"{label} contains duplicate levels")
        harness_ids = [preset.level_id for preset in self.harness_presets]
        if len(harness_ids) != len(set(harness_ids)):
            errors.append("harness_presets contains duplicate level_id values")
        effective = {
            (preset.temperature, preset.memory, preset.harness_id)
            for preset in self.harness_presets
        }
        if len(effective) != len(self.harness_presets):
            errors.append("harness_presets contains duplicate executable settings")
        return tuple(errors)


class ExecutionResolution(StrictFrozenModel):
    """Explicit bridge from study identifiers to runner registry identifiers."""

    schema_version: Literal[1]
    execution_mode: Literal["exact", "offline_mock"] = "exact"
    trajectory_datasets: dict[str, str]
    model_registry_keys: dict[str, str] = Field(default_factory=dict)
    mock_model_registry_keys: dict[str, str] = Field(default_factory=dict)
    baseline_kinds: dict[
        str,
        Literal["momentum", "mean_reversion", "market_maker", "buy_hold", "random"],
    ] = Field(default_factory=dict)
    stage_defaults: dict[str, StageExecutionDefaults]
    mphiq_levels: dict[str, MPHIQExecutionLevels] = Field(default_factory=dict)
    disabled_stages: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_execution_mode(self) -> ExecutionResolution:
        if self.execution_mode == "exact" and self.mock_model_registry_keys:
            raise ValueError("exact execution cannot declare mock_model_registry_keys")
        if self.execution_mode == "offline_mock":
            if self.model_registry_keys:
                raise ValueError("offline_mock execution cannot declare exact model_registry_keys")
            if not self.mock_model_registry_keys:
                raise ValueError("offline_mock execution requires explicit mock substitutions")
            targets = list(self.mock_model_registry_keys.values())
            if len(targets) != len(set(targets)):
                raise ValueError("offline_mock model substitutions must be one-to-one")
        if any(not reason.strip() for reason in self.disabled_stages.values()):
            raise ValueError("disabled stage reasons must be non-empty")
        return self


class MaterializedCell(StrictFrozenModel):
    cell_id: str
    mphiq_code: str | None = None
    mphiq_pairs: tuple[MPHIQPairAssignmentSpec, ...] = ()
    capital_share: CapitalShareLevelSpec | None = None


class RunAssignment(StrictFrozenModel):
    assignment_id: str
    ordinal: int = Field(gt=0)
    study_id: str
    plan_hash: str
    stage_id: str
    authorization_stage: str
    design: str
    trajectory_id: str
    window_id: str
    dependence_cluster_id: str
    independent_unit: str
    market_replica_id: str | None
    seed: int
    cell: MaterializedCell
    steps: int = Field(gt=0)
    calls_per_llm_agent_step: int = Field(gt=0)
    cohorts: tuple[CohortSpec, ...]
    exact_counts: ExactCountsSpec
    calls_by_pricing_key: dict[str, int]
    stage_budget_cap: BudgetCapSpec
    model_revisions: dict[str, str]
    evidence_kind: Literal["mock", "real", "unresolved"] = "unresolved"
    model_registry_substitutions: dict[str, str] = Field(default_factory=dict)
    execution_config: dict[str, Any] | None
    execution_blockers: tuple[str, ...]


class MaterializedStudy(StrictFrozenModel):
    schema_version: Literal[1]
    study_id: str
    plan_hash: str
    assignments: tuple[RunAssignment, ...]
    exact_runs: int = Field(gt=0)
    exact_steps: int = Field(gt=0)
    exact_agent_steps: int = Field(gt=0)
    exact_calls: int = Field(ge=0)
    executable_runs: int = Field(ge=0)
    materialization_hash: str

    def to_jsonable(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def load_execution_resolution(path: Path) -> ExecutionResolution:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError("execution resolution must contain one mapping")
    return ExecutionResolution.model_validate(raw)


def _cell(plan: FrozenStudyPlan, stage: CompiledStage, cell_id: str) -> MaterializedCell:
    if stage.design == "mphiq":
        pairs = tuple(
            sorted(
                (
                    pair
                    for pair in plan.source_spec.mphiq_pairs
                    if cell_id in {pair.different_code, pair.same_code}
                ),
                key=lambda pair: pair.pair_id,
            )
        )
        return MaterializedCell(cell_id=cell_id, mphiq_code=cell_id, mphiq_pairs=pairs)
    if stage.design == "capital_share":
        level = next(
            level for level in plan.source_spec.capital_share_levels if level.level_id == cell_id
        )
        return MaterializedCell(cell_id=cell_id, capital_share=level)
    return MaterializedCell(cell_id=cell_id)


def _calls(
    cohorts: tuple[CohortSpec, ...],
    steps: int,
    calls_per_step: int,
    mphiq_models: tuple[ModelAllocationSpec, ...] | None = None,
) -> tuple[ExactCountsSpec, dict[str, int]]:
    agents = sum(cohort.total_agents for cohort in cohorts)
    llm_agents = sum(cohort.total_agents for cohort in cohorts if cohort.technology == "llm")
    calls_by_key: dict[str, int] = {}
    llm_allocations = (
        mphiq_models
        if mphiq_models is not None
        else tuple(
            allocation
            for cohort in cohorts
            if cohort.technology == "llm"
            for allocation in cohort.allocations
            for _ in range(allocation.count)
        )
    )
    for allocation in llm_allocations:
        if allocation.pricing_key is None:  # compiler already rejects this
            raise ValueError(f"LLM allocation {allocation.model_id} lacks pricing_key")
        calls_by_key[allocation.pricing_key] = (
            calls_by_key.get(allocation.pricing_key, 0) + steps * calls_per_step
        )
    return (
        ExactCountsSpec(
            runs=1,
            steps=steps,
            agents_per_run=agents,
            agent_steps=steps * agents,
            calls=steps * llm_agents * calls_per_step,
        ),
        calls_by_key,
    )


def _validate_model(
    allocation: ModelAllocationSpec,
    resolution: ExecutionResolution,
    models: dict[str, ModelSpec],
) -> tuple[str | None, str | None]:
    if resolution.execution_mode == "offline_mock":
        registry_key = resolution.mock_model_registry_keys.get(allocation.model_id)
        if registry_key is None:
            return None, f"missing mock substitution for {allocation.model_id}"
        spec = models.get(registry_key)
        if spec is None:
            return None, f"model registry has no mock substitution key {registry_key!r}"
        if spec.provider != "mock" or spec.deployment != "mock":
            return (
                None,
                f"mock substitution {registry_key!r} must resolve to a mock provider/deployment",
            )
        return registry_key, None

    registry_key = resolution.model_registry_keys.get(allocation.model_id)
    if registry_key is None:
        return None, f"missing model_registry_keys mapping for {allocation.model_id}"
    spec = models.get(registry_key)
    if spec is None:
        return None, f"model registry has no key {registry_key!r}"
    comparisons = {
        "model_id": (spec.model_id, allocation.model_id),
        "provider": (spec.provider, allocation.provider),
        "family": (spec.family, allocation.family),
        "pricing_key": (spec.pricing_key, allocation.pricing_key),
    }
    mismatches = [
        f"{field}={actual!r} (expected {expected!r})"
        for field, (actual, expected) in comparisons.items()
        if actual != expected
    ]
    if spec.provider != "mock" and spec.verified_on != allocation.revision:
        mismatches.append(
            f"verified_on={spec.verified_on!r} (expected revision {allocation.revision!r})"
        )
    if spec.provider != "mock" and not spec.frontier_eligible:
        mismatches.append("frontier_eligible=False (required for API execution)")
    if mismatches:
        detail = "; ".join(mismatches)
        return None, f"model mapping {registry_key!r} does not match frozen allocation: {detail}"
    return registry_key, None


def _stable_index(key: str, length: int) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % length


def _balanced_permutation(values: list[Any], count: int, key: str) -> list[Any]:
    base = [values[index % len(values)] for index in range(count)]
    order = sorted(
        range(count),
        key=lambda index: hashlib.sha256(f"{key}|{index}".encode()).hexdigest(),
    )
    return [base[index] for index in order]


def _perfectly_confounded(left: list[str], right: list[str]) -> bool:
    left_to_right: dict[str, set[str]] = {}
    right_to_left: dict[str, set[str]] = {}
    for left_value, right_value in zip(left, right, strict=True):
        left_to_right.setdefault(left_value, set()).add(right_value)
        right_to_left.setdefault(right_value, set()).add(left_value)
    return all(len(values) == 1 for values in left_to_right.values()) and all(
        len(values) == 1 for values in right_to_left.values()
    )


def _mphiq_model_assignments(
    cohort: CohortSpec, code: str, same_model_id: str
) -> tuple[ModelAllocationSpec, ...]:
    allocations = {allocation.model_id: allocation for allocation in cohort.allocations}
    if code[0] == "1":
        selected = allocations[same_model_id]
        return tuple(selected for _ in range(cohort.total_agents))
    return tuple(allocation for allocation in cohort.allocations for _ in range(allocation.count))


def _mphiq_same_model_schedule(
    stage: CompiledStage, cohorts: tuple[CohortSpec, ...]
) -> dict[tuple[str, int], str]:
    if stage.design != "mphiq":
        return {}
    if len(cohorts) != 1 or cohorts[0].technology != "llm":
        raise ValueError("MPHIQ materialization requires exactly one LLM cohort")
    cohort = cohorts[0]
    blocks = sorted(
        (trajectory_id, seed) for trajectory_id in stage.trajectory_ids for seed in stage.seeds
    )
    choices: list[str] = []
    for allocation in cohort.allocations:
        numerator = len(blocks) * allocation.count
        if numerator % cohort.total_agents:
            raise ValueError(
                f"{stage.stage_id}: MPHIQ same-model blocks cannot preserve the frozen "
                f"pricing allocation for {allocation.model_id}; add independent blocks"
            )
        choices.extend([allocation.model_id] * (numerator // cohort.total_agents))
    if len(choices) != len(blocks):
        raise ValueError(f"{stage.stage_id}: MPHIQ same-model schedule does not reconcile")
    ordered_choices = _balanced_permutation(
        choices, len(choices), f"{stage.stage_id}|same-model-schedule"
    )
    return dict(zip(blocks, ordered_choices, strict=True))


def _prompt_semantic_groups(prompt_dir: Path) -> dict[str, str]:
    catalog_path = prompt_dir / "catalog.yaml"
    raw = yaml.safe_load(catalog_path.read_text())
    if not isinstance(raw, dict):
        raise ValueError("prompt catalog must contain one mapping")
    return {
        str(item["id"]): str(item["semantic_group"]) for item in raw.get("semantic_paraphrases", [])
    }


def _mphiq_groups(
    *,
    stage: CompiledStage,
    trajectory: TrajectoryWindowSpec,
    cell: MaterializedCell,
    seed: int,
    cohort: CohortSpec,
    same_model_id: str,
    levels: MPHIQExecutionLevels,
    defaults: StageExecutionDefaults,
    resolution: ExecutionResolution,
    models: dict[str, ModelSpec],
    root: Path,
) -> tuple[CohortConfig | None, set[str], tuple[str, ...]]:
    blockers = list(levels.validate_unique_levels())
    if cell.mphiq_code is None:
        return None, set(), ("MPHIQ cell is missing its scheme code",)
    code = cell.mphiq_code
    if cohort.technology != "llm" or cohort.ecology != "heterogeneous":
        blockers.append("MPHIQ execution requires one heterogeneous LLM source cohort")

    registry_keys: dict[str, str] = {}
    deployments: set[str] = set()
    for allocation in cohort.allocations:
        registry_key, error = _validate_model(allocation, resolution, models)
        if error is not None:
            blockers.append(error)
            continue
        assert registry_key is not None
        registry_keys[allocation.model_id] = registry_key
        deployments.add(models[registry_key].provider)

    for persona_id in levels.persona_ids:
        try:
            load_persona(persona_id, root / "configs/personas")
        except (FileNotFoundError, ValueError) as error:
            blockers.append(f"persona {persona_id!r} cannot be resolved: {error}")
    prompt_dir = root / "configs/prompts"
    try:
        semantic_groups = _prompt_semantic_groups(prompt_dir)
    except (FileNotFoundError, KeyError, TypeError, ValueError) as error:
        blockers.append(f"prompt semantic catalog cannot be resolved: {error}")
        semantic_groups = {}
    for prompt_id in levels.prompt_ids:
        try:
            resolve_prompt(prompt_id, prompt_dir)
        except (FileNotFoundError, KeyError, ValueError) as error:
            blockers.append(f"prompt {prompt_id!r} cannot be resolved: {error}")
        if semantic_groups.get(prompt_id) != levels.prompt_semantic_group:
            blockers.append(
                f"prompt {prompt_id!r} is not in semantic group {levels.prompt_semantic_group!r}"
            )
    if blockers:
        return None, deployments, tuple(sorted(set(blockers)))

    total = cohort.total_agents
    model_pool = list(_mphiq_model_assignments(cohort, "00000", same_model_id))
    pools: dict[str, list[Any]] = {
        "model_id": model_pool,
        "profile_id": list(levels.persona_ids),
        "harness_id": list(levels.harness_presets),
        "information_policy": list(levels.information_policies),
        "prompt_id": list(levels.prompt_ids),
    }
    id_value = {
        "model_id": lambda value: value.model_id,
        "profile_id": str,
        "harness_id": lambda value: value.level_id,
        "information_policy": str,
        "prompt_id": str,
    }
    block_key = f"{stage.stage_id}|{trajectory.trajectory_id}|{seed}"
    different: dict[str, list[Any]] | None = None
    for nonce in range(256):
        candidate = {
            name: _balanced_permutation(values, total, f"{block_key}|{name}|{nonce}")
            for name, values in pools.items()
        }
        encoded = {
            name: [id_value[name](value) for value in values] for name, values in candidate.items()
        }
        names = list(encoded)
        if not any(
            _perfectly_confounded(encoded[left], encoded[right])
            for index, left in enumerate(names)
            for right in names[index + 1 :]
        ):
            different = candidate
            break
    if different is None:
        return (
            None,
            deployments,
            ("MPHIQ level pools cannot produce non-confounded per-agent assignments",),
        )

    same_model = next(
        allocation for allocation in cohort.allocations if allocation.model_id == same_model_id
    )
    same: dict[str, Any] = {
        "model_id": same_model,
        "profile_id": levels.persona_ids[
            _stable_index(f"{block_key}|profile_id|same", len(levels.persona_ids))
        ],
        "harness_id": levels.harness_presets[
            _stable_index(f"{block_key}|harness_id|same", len(levels.harness_presets))
        ],
        "information_policy": levels.information_policies[
            _stable_index(
                f"{block_key}|information_policy|same",
                len(levels.information_policies),
            )
        ],
        "prompt_id": levels.prompt_ids[
            _stable_index(f"{block_key}|prompt_id|same", len(levels.prompt_ids))
        ],
    }
    factor_names = list(pools)
    assigned = {
        name: ([same[name]] * total if bit == "1" else different[name])
        for bit, name in zip(code, factor_names, strict=True)
    }
    groups: list[AgentGroup] = []
    for agent_index in range(total):
        allocation = assigned["model_id"][agent_index]
        resolved_model = models[registry_keys[allocation.model_id]]
        persona_id = assigned["profile_id"][agent_index]
        harness = assigned["harness_id"][agent_index]
        information_policy = assigned["information_policy"][agent_index]
        prompt_id = assigned["prompt_id"][agent_index]
        treatment_payload = {
            "scheme_code": code,
            "agent_index": agent_index,
            "model_id": (
                resolved_model.model_id
                if resolution.execution_mode == "offline_mock"
                else allocation.model_id
            ),
            "model_revision": (
                resolved_model.verified_on or "offline-mock"
                if resolution.execution_mode == "offline_mock"
                else allocation.revision
            ),
            "model_registry_key": registry_keys[allocation.model_id],
            "profile_id": persona_id,
            "harness_id": harness.harness_id,
            "harness_temperature": harness.temperature,
            "harness_memory": harness.memory,
            "information_policy": information_policy,
            "prompt_id": prompt_id,
            "prompt_semantic_group": levels.prompt_semantic_group,
        }
        digest_payload = json.dumps(treatment_payload, sort_keys=True, separators=(",", ":"))
        treatment = MPHIQAgentTreatment(
            **treatment_payload,
            assignment_digest=hashlib.sha256(digest_payload.encode()).hexdigest(),
        )
        groups.append(
            AgentGroup(
                kind="llm",
                count=1,
                model=treatment.model_registry_key,
                persona=persona_id,
                temperature=harness.temperature,
                memory=harness.memory,
                harness_id=harness.harness_id,
                prompt_id=prompt_id,
                information_policy=information_policy,
                grounding_mode=defaults.grounding_mode,
                mphiq_treatment=treatment,
            )
        )
    return CohortConfig(name=cohort.cohort_id, agents=groups), deployments, ()


def _execution_config(
    assignment_id: str,
    stage: CompiledStage,
    stage_budget_cap: BudgetCapSpec,
    trajectory: TrajectoryWindowSpec,
    cell: MaterializedCell,
    seed: int,
    cohorts: tuple[CohortSpec, ...],
    exact: ExactCountsSpec,
    resolution: ExecutionResolution | None,
    models: dict[str, ModelSpec],
    root: Path,
    hypothesis_ids: list[str],
    mphiq_same_model_id: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    blockers: list[str] = []
    if resolution is None:
        return None, (
            "missing execution resolution (datasets, registry keys, personas, prompts, "
            "and runtime defaults)",
        )
    defaults = resolution.stage_defaults.get(stage.stage_id)
    if defaults is None:
        blockers.append(f"missing stage_defaults for {stage.stage_id}")
    dataset = resolution.trajectory_datasets.get(trajectory.trajectory_id)
    if dataset is None:
        blockers.append(f"missing trajectory_datasets mapping for {trajectory.trajectory_id}")
    else:
        try:
            registry = Registry(root / "datasets")
            entry = registry.get(dataset)
            dataset_errors = registry.verify(entry)
            blockers.extend(f"dataset {dataset!r}: {error}" for error in dataset_errors)
        except KeyError as error:
            blockers.append(str(error))

    if stage.design == "capital_share":
        blockers.append(
            "capital-share cells require capital-weighted agent/background allocation "
            "not represented by ExperimentConfig"
        )
    if stage.stage_id in resolution.disabled_stages:
        blockers.append(f"stage explicitly disabled: {resolution.disabled_stages[stage.stage_id]}")

    groups_by_cohort: list[CohortConfig] = []
    deployments: set[str] = set()
    if stage.design == "mphiq":
        levels = resolution.mphiq_levels.get(stage.stage_id)
        if levels is None:
            blockers.append(f"missing mphiq_levels for {stage.stage_id}")
        if mphiq_same_model_id is None:
            blockers.append("missing block-level MPHIQ same-model assignment")
        if defaults is not None and levels is not None and mphiq_same_model_id is not None:
            if len(cohorts) != 1:
                blockers.append("MPHIQ execution requires exactly one source cohort")
            else:
                resolved, providers, mphiq_blockers = _mphiq_groups(
                    stage=stage,
                    trajectory=trajectory,
                    cell=cell,
                    seed=seed,
                    cohort=cohorts[0],
                    same_model_id=mphiq_same_model_id,
                    levels=levels,
                    defaults=defaults,
                    resolution=resolution,
                    models=models,
                    root=root,
                )
                deployments.update(providers)
                blockers.extend(mphiq_blockers)
                if resolved is not None:
                    groups_by_cohort.append(resolved)
    else:
        for cohort in cohorts:
            groups: list[AgentGroup] = []
            for allocation in cohort.allocations:
                if cohort.technology == "llm":
                    registry_key, error = _validate_model(allocation, resolution, models)
                    if error is not None:
                        blockers.append(error)
                        continue
                    assert registry_key is not None
                    deployments.add(models[registry_key].provider)
                    if defaults is None or defaults.persona_id is None:
                        blockers.append(f"missing persona_id for LLM cohort {cohort.cohort_id}")
                        continue
                    if defaults.prompt_id is None:
                        blockers.append(f"missing prompt_id for LLM cohort {cohort.cohort_id}")
                        continue
                    groups.append(
                        AgentGroup(
                            kind="llm",
                            count=allocation.count,
                            model=registry_key,
                            persona=defaults.persona_id,
                            temperature=defaults.temperature,
                            memory=defaults.memory,
                            harness_id=defaults.harness_id,
                            prompt_id=defaults.prompt_id,
                            information_policy=defaults.information_policy,
                            grounding_mode=defaults.grounding_mode,
                        )
                    )
                else:
                    kind = resolution.baseline_kinds.get(allocation.model_id)
                    if kind is None:
                        blockers.append(f"missing baseline_kinds mapping for {allocation.model_id}")
                        continue
                    groups.append(AgentGroup(kind=kind, count=allocation.count))
            if groups:
                groups_by_cohort.append(CohortConfig(name=cohort.cohort_id, agents=groups))

    if defaults is not None:
        if stage.design != "mphiq" and defaults.persona_id is not None:
            try:
                load_persona(defaults.persona_id, root / "configs/personas")
            except (FileNotFoundError, ValueError) as error:
                blockers.append(f"persona {defaults.persona_id!r} cannot be resolved: {error}")
        if stage.design != "mphiq" and defaults.prompt_id is not None:
            try:
                resolve_prompt(defaults.prompt_id, root / "configs/prompts")
            except (FileNotFoundError, KeyError, ValueError) as error:
                blockers.append(f"prompt {defaults.prompt_id!r} cannot be resolved: {error}")
        paid = any(provider != "mock" for provider in deployments)
        if "mock" in deployments and paid:
            blockers.append("runner cannot mix mock and API LLMs under one model_policy")
        if paid and defaults.runtime_budget is None:
            blockers.append("paid/API assignment requires an explicit runtime_budget")
        if defaults.runtime_budget is not None:
            if defaults.runtime_budget.max_requests < exact.calls:
                blockers.append(
                    f"runtime max_requests {defaults.runtime_budget.max_requests} is below "
                    f"exact calls {exact.calls}"
                )
            if defaults.runtime_budget.max_requests > stage_budget_cap.max_calls:
                blockers.append("per-run runtime max_requests exceeds the frozen stage call cap")

    if blockers or defaults is None or dataset is None:
        return None, tuple(sorted(set(blockers)))
    model_policy: Literal["mock_only", "frontier_only"] = (
        "mock_only" if deployments == {"mock"} else "frontier_only"
    )
    config = ExperimentConfig(
        name=assignment_id,
        seed=seed,
        dataset=dataset,
        market=defaults.market,
        steps=exact.steps,
        observation_window=defaults.observation_window,
        initial_cash=defaults.initial_cash,
        initial_position_per_symbol=defaults.initial_position_per_symbol,
        max_position_per_symbol=defaults.max_position_per_symbol,
        model_policy=model_policy,
        runtime_budget=defaults.runtime_budget,
        hypothesis_ids=hypothesis_ids,
        independent_block=trajectory.trajectory_id,
        dependence_cluster=trajectory.dependence_cluster_id,
        trajectory_id=trajectory.trajectory_id,
        market_replica_id=(
            f"{trajectory.trajectory_id}-s{seed}" if cell.capital_share is not None else None
        ),
        window_start=trajectory.start_date,
        window_end=trajectory.end_date,
        cohorts=groups_by_cohort,
    )
    return config.model_dump(mode="json"), ()


def materialize_study(
    plan: FrozenStudyPlan,
    resolution: ExecutionResolution | None = None,
    *,
    root: Path = Path("."),
    models_path: Path | None = None,
    require_executable: bool = False,
) -> MaterializedStudy:
    """Enumerate all run assignments and optionally resolve runner configs.

    No experiment is executed.  ``require_executable`` turns any unresolved
    assignment into a hard error after deterministic enumeration.
    """
    models = load_models(models_path or root / "configs/models.yaml")
    trajectories = {item.trajectory_id: item for item in plan.source_spec.trajectories}
    clusters = {item.cluster_id: item for item in plan.source_spec.dependence_clusters}
    cohorts = {item.cohort_id: item for item in plan.source_spec.cohorts}
    stages = {item.stage_id: item for item in plan.source_spec.stages}
    estimands = {item.estimand_id: item for item in plan.source_spec.estimands}
    assignments: list[RunAssignment] = []

    for compiled in sorted(plan.stages, key=lambda item: item.order):
        source_stage = stages[compiled.stage_id]
        selected_cohorts = tuple(cohorts[cohort_id] for cohort_id in compiled.cohort_ids)
        same_model_schedule = _mphiq_same_model_schedule(compiled, selected_cohorts)
        hypotheses = sorted(
            {estimands[estimand_id].hypothesis_id for estimand_id in compiled.estimand_ids}
        )
        for trajectory_id in compiled.trajectory_ids:
            trajectory = trajectories[trajectory_id]
            cluster = clusters[trajectory.dependence_cluster_id]
            for seed in compiled.seeds:
                for cell_id in compiled.design_cells:
                    cell = _cell(plan, compiled, cell_id)
                    same_model_id = same_model_schedule.get((trajectory_id, seed))
                    mphiq_models = None
                    if cell.mphiq_code is not None:
                        if same_model_id is None:
                            raise ValueError("MPHIQ assignment lacks a same-model schedule")
                        mphiq_models = _mphiq_model_assignments(
                            selected_cohorts[0], cell.mphiq_code, same_model_id
                        )
                    exact, calls_by_key = _calls(
                        selected_cohorts,
                        source_stage.steps_per_run,
                        source_stage.calls_per_llm_agent_step,
                        mphiq_models,
                    )
                    assignment_id = (
                        f"{plan.study_id}--{compiled.stage_id}--{trajectory_id}--{cell_id}--s{seed}"
                    )
                    config, blockers = _execution_config(
                        assignment_id,
                        compiled,
                        source_stage.budget_cap,
                        trajectory,
                        cell,
                        seed,
                        selected_cohorts,
                        exact,
                        resolution,
                        models,
                        root,
                        hypotheses,
                        same_model_id,
                    )
                    assignments.append(
                        RunAssignment(
                            assignment_id=assignment_id,
                            ordinal=len(assignments) + 1,
                            study_id=plan.study_id,
                            plan_hash=plan.plan_hash,
                            stage_id=compiled.stage_id,
                            authorization_stage=compiled.authorization_stage,
                            design=compiled.design,
                            trajectory_id=trajectory_id,
                            window_id=trajectory.window_id,
                            dependence_cluster_id=trajectory.dependence_cluster_id,
                            independent_unit=cluster.independent_unit,
                            market_replica_id=(
                                f"{trajectory_id}-s{seed}"
                                if compiled.design == "capital_share"
                                else None
                            ),
                            seed=seed,
                            cell=cell,
                            steps=source_stage.steps_per_run,
                            calls_per_llm_agent_step=source_stage.calls_per_llm_agent_step,
                            cohorts=selected_cohorts,
                            exact_counts=exact,
                            calls_by_pricing_key=calls_by_key,
                            stage_budget_cap=source_stage.budget_cap,
                            model_revisions={
                                allocation.model_id: allocation.revision
                                for cohort in selected_cohorts
                                for allocation in cohort.allocations
                            },
                            evidence_kind=(
                                "unresolved"
                                if resolution is None
                                else (
                                    "mock"
                                    if resolution.execution_mode == "offline_mock"
                                    or (
                                        any(
                                            cohort.technology == "llm"
                                            for cohort in selected_cohorts
                                        )
                                        and all(
                                            allocation.provider == "mock"
                                            for cohort in selected_cohorts
                                            if cohort.technology == "llm"
                                            for allocation in cohort.allocations
                                        )
                                    )
                                    else "real"
                                )
                            ),
                            model_registry_substitutions=(
                                {
                                    allocation.model_id: resolution.mock_model_registry_keys[
                                        allocation.model_id
                                    ]
                                    for cohort in selected_cohorts
                                    if cohort.technology == "llm"
                                    for allocation in cohort.allocations
                                    if allocation.model_id
                                    in resolution.mock_model_registry_keys
                                }
                                if resolution is not None
                                and resolution.execution_mode == "offline_mock"
                                else {}
                            ),
                            execution_config=config,
                            execution_blockers=blockers,
                        )
                    )

    exact_runs = len(assignments)
    exact_steps = sum(item.exact_counts.steps for item in assignments)
    exact_agent_steps = sum(item.exact_counts.agent_steps for item in assignments)
    exact_calls = sum(item.exact_counts.calls for item in assignments)
    if (exact_runs, exact_steps, exact_agent_steps, exact_calls) != (
        plan.exact_runs,
        plan.exact_steps,
        plan.exact_agent_steps,
        plan.exact_calls,
    ):
        raise ValueError("materialized assignments do not reconcile with frozen plan counts")
    for compiled in plan.stages:
        stage_assignments = [item for item in assignments if item.stage_id == compiled.stage_id]
        calls = sum(item.exact_counts.calls for item in stage_assignments)
        calls_by_key: dict[str, int] = {}
        for item in stage_assignments:
            for key, value in item.calls_by_pricing_key.items():
                calls_by_key[key] = calls_by_key.get(key, 0) + value
        if calls != compiled.exact_counts.calls or calls_by_key != compiled.calls_by_pricing_key:
            raise ValueError(f"{compiled.stage_id}: materialized call allocation drift")

    payload = [item.model_dump(mode="json") for item in assignments]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    result = MaterializedStudy(
        schema_version=1,
        study_id=plan.study_id,
        plan_hash=plan.plan_hash,
        assignments=tuple(assignments),
        exact_runs=exact_runs,
        exact_steps=exact_steps,
        exact_agent_steps=exact_agent_steps,
        exact_calls=exact_calls,
        executable_runs=sum(item.execution_config is not None for item in assignments),
        materialization_hash=hashlib.sha256(canonical.encode()).hexdigest(),
    )
    unresolved = [item for item in result.assignments if item.execution_config is None]
    if require_executable and unresolved:
        first = unresolved[0]
        raise ValueError(
            f"{len(unresolved)} of {result.exact_runs} assignments are not executable; "
            f"{first.assignment_id}: {'; '.join(first.execution_blockers)}"
        )
    return result


def materialize_study_file(
    plan_path: Path,
    resolution_path: Path | None = None,
    **kwargs: Any,
) -> MaterializedStudy:
    resolution = load_execution_resolution(resolution_path) if resolution_path is not None else None
    return materialize_study(load_study_plan(plan_path), resolution, **kwargs)


def write_materialized_study(materialized: MaterializedStudy, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(materialized.to_jsonable(), indent=2) + "\n")
    temporary.replace(path)
