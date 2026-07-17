"""Strict, immutable schemas for executable paper study plans."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Identifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=96,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    ),
]
MPHIQCode = Annotated[str, StringConstraints(pattern=r"^[01]{5}$")]

_PLACEHOLDER_TOKENS = {
    "dummy",
    "example",
    "placeholder",
    "replace-me",
    "tbd",
    "temp",
    "todo",
    "unspecified",
}
_MUTABLE_MODEL_TOKEN = re.compile(
    r"(?:^|[-_.:/])(auto|current|default|frontier|latest|preview|stable)(?:$|[-_.:/])",
    re.IGNORECASE,
)


class StrictFrozenModel(BaseModel):
    """Shared fail-closed model configuration for study contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


def _reject_placeholder(value: str, field_name: str) -> str:
    if value.lower() in _PLACEHOLDER_TOKENS:
        raise ValueError(f"{field_name} cannot be a placeholder: {value!r}")
    return value


class DependenceClusterSpec(StrictFrozenModel):
    cluster_id: Identifier
    independent_unit: Literal["trajectory", "market_window", "market_replica"]
    description: Annotated[str, StringConstraints(min_length=12, max_length=300)]

    @field_validator("cluster_id")
    @classmethod
    def reject_placeholder_cluster_id(cls, value: str) -> str:
        return _reject_placeholder(value, "cluster_id")


class TrajectoryWindowSpec(StrictFrozenModel):
    trajectory_id: Identifier
    window_id: Identifier
    source: Literal["synthetic", "real"]
    market_id: Identifier
    start_date: str
    end_date: str
    dependence_cluster_id: Identifier

    @field_validator("trajectory_id", "window_id", "dependence_cluster_id")
    @classmethod
    def reject_placeholder_ids(cls, value: str, info) -> str:
        return _reject_placeholder(value, info.field_name)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_iso_date(cls, value: str) -> str:
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("must be an ISO-8601 calendar date") from error
        return value

    @model_validator(mode="after")
    def validate_date_order(self) -> TrajectoryWindowSpec:
        if date.fromisoformat(self.start_date) > date.fromisoformat(self.end_date):
            raise ValueError("start_date must not be after end_date")
        return self


class ModelAllocationSpec(StrictFrozenModel):
    model_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=160)]
    revision: Annotated[str, StringConstraints(strip_whitespace=True, min_length=4, max_length=80)]
    provider: Identifier
    family: Identifier
    count: Annotated[int, Field(ge=1, le=10_000)]

    @field_validator("model_id")
    @classmethod
    def require_immutable_model_id(cls, value: str) -> str:
        if _MUTABLE_MODEL_TOKEN.search(value):
            raise ValueError(f"model_id looks like a mutable alias: {value!r}")
        return value


class CohortSpec(StrictFrozenModel):
    cohort_id: Identifier
    technology: Literal["llm", "classical", "null"]
    ecology: Literal["homogeneous", "heterogeneous"]
    allocations: list[ModelAllocationSpec] = Field(min_length=1)

    @property
    def total_agents(self) -> int:
        return sum(allocation.count for allocation in self.allocations)

    @model_validator(mode="after")
    def validate_ecology(self) -> CohortSpec:
        counts = [allocation.count for allocation in self.allocations]
        model_ids = {allocation.model_id for allocation in self.allocations}
        families = {allocation.family for allocation in self.allocations}
        if len(model_ids) != len(self.allocations):
            raise ValueError("cohort contains duplicate model_id allocations")
        if self.ecology == "homogeneous" and len(self.allocations) != 1:
            raise ValueError("homogeneous cohorts require exactly one allocation")
        if self.ecology == "heterogeneous":
            if len(self.allocations) < 2 or len(families) < 2:
                raise ValueError("heterogeneous cohorts require at least two model families")
            if max(counts) - min(counts) > 1:
                raise ValueError("heterogeneous allocation counts must differ by at most one")
        if self.technology == "null" and self.ecology != "homogeneous":
            raise ValueError("null cohorts must use the homogeneous ecology label")
        return self


class MPHIQPairAssignmentSpec(StrictFrozenModel):
    pair_id: Identifier
    factor: Literal["M", "P", "H", "I", "Q"]
    different_code: MPHIQCode
    same_code: MPHIQCode
    assignment_seed: Annotated[int, Field(ge=0, le=2**32 - 1)]

    @model_validator(mode="after")
    def validate_hamming_pair(self) -> MPHIQPairAssignmentSpec:
        positions = {factor: index for index, factor in enumerate("MPHIQ")}
        bit_pairs = zip(self.different_code, self.same_code, strict=True)
        changed = [i for i, values in enumerate(bit_pairs) if values[0] != values[1]]
        expected = positions[self.factor]
        if changed != [expected]:
            raise ValueError("MPHIQ pair must differ only at its declared factor")
        if self.different_code[expected] != "0" or self.same_code[expected] != "1":
            raise ValueError("MPHIQ pair direction must be different_code=0 to same_code=1")
        return self


class CapitalShareLevelSpec(StrictFrozenModel):
    level_id: Identifier
    ai_share_bps: Annotated[int, Field(ge=0, le=10_000)]
    total_capital_usd: Annotated[int, Field(gt=0)]
    ai_capital_usd: Annotated[int, Field(ge=0)]
    background_capital_usd: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def validate_capital_reconciliation(self) -> CapitalShareLevelSpec:
        if self.ai_capital_usd + self.background_capital_usd != self.total_capital_usd:
            raise ValueError("AI and background capital must sum to total capital")
        if self.ai_capital_usd * 10_000 != self.total_capital_usd * self.ai_share_bps:
            raise ValueError("ai_capital_usd must exactly match ai_share_bps")
        return self


class EstimandSpec(StrictFrozenModel):
    estimand_id: Identifier
    hypothesis_id: Annotated[str, StringConstraints(pattern=r"^H(?:[1-9]|1[0-2]|2b)$")]
    outcome: Annotated[str, StringConstraints(min_length=5, max_length=240)]
    contrast: Annotated[str, StringConstraints(min_length=5, max_length=320)]
    independent_unit: Annotated[str, StringConstraints(min_length=5, max_length=160)]
    estimator: Annotated[str, StringConstraints(min_length=5, max_length=240)]


class RequiredOutputSpec(StrictFrozenModel):
    output_id: Identifier
    path: Annotated[str, StringConstraints(min_length=5, max_length=240)]
    format: Literal["json", "jsonl", "parquet", "csv", "markdown", "png", "svg"]
    estimand_ids: list[Identifier] = Field(min_length=1)


class BudgetCapSpec(StrictFrozenModel):
    max_calls: Annotated[int, Field(ge=0)]
    max_cost_usd: Annotated[float, Field(ge=0, allow_inf_nan=False)]


class ExactCountsSpec(StrictFrozenModel):
    runs: Annotated[int, Field(gt=0)]
    steps: Annotated[int, Field(gt=0)]
    agents_per_run: Annotated[int, Field(gt=0)]
    agent_steps: Annotated[int, Field(gt=0)]
    calls: Annotated[int, Field(ge=0)]


class StageSpec(StrictFrozenModel):
    stage_id: Identifier
    order: Annotated[int, Field(ge=1)]
    design: Literal["replay", "mphiq", "capital_share"]
    trajectory_ids: list[Identifier] = Field(min_length=1)
    cohort_ids: list[Identifier] = Field(min_length=1)
    seeds: list[Annotated[int, Field(ge=0, le=2**32 - 1)]] = Field(min_length=1)
    steps_per_run: Annotated[int, Field(gt=0)]
    calls_per_llm_agent_step: Annotated[int, Field(ge=1, le=10)] = 1
    mphiq_pair_ids: list[Identifier] = Field(default_factory=list)
    capital_share_level_ids: list[Identifier] = Field(default_factory=list)
    estimand_ids: list[Identifier] = Field(min_length=1)
    output_ids: list[Identifier] = Field(min_length=1)
    expected_counts: ExactCountsSpec
    planned_cost_usd: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    budget_cap: BudgetCapSpec

    @model_validator(mode="after")
    def validate_design_axes(self) -> StageSpec:
        if self.design == "mphiq" and not self.mphiq_pair_ids:
            raise ValueError("MPHIQ stages require pair assignments")
        if self.design != "mphiq" and self.mphiq_pair_ids:
            raise ValueError("only MPHIQ stages may reference pair assignments")
        if self.design == "capital_share" and not self.capital_share_level_ids:
            raise ValueError("capital-share stages require H5 levels")
        if self.design != "capital_share" and self.capital_share_level_ids:
            raise ValueError("only capital-share stages may reference H5 levels")
        return self


class StudySpec(StrictFrozenModel):
    schema_version: Literal[1]
    study_id: Identifier
    title: Annotated[str, StringConstraints(min_length=12, max_length=200)]
    max_stages: Annotated[int, Field(ge=1, le=20)]
    dependence_clusters: list[DependenceClusterSpec] = Field(min_length=1)
    trajectories: list[TrajectoryWindowSpec] = Field(min_length=1)
    cohorts: list[CohortSpec] = Field(min_length=1)
    held_out_families: list[Identifier] = Field(min_length=1)
    mphiq_pairs: list[MPHIQPairAssignmentSpec] = Field(default_factory=list)
    capital_share_levels: list[CapitalShareLevelSpec] = Field(default_factory=list)
    estimands: list[EstimandSpec] = Field(min_length=1)
    required_outputs: list[RequiredOutputSpec] = Field(min_length=1)
    stages: list[StageSpec] = Field(min_length=1)
    budget_cap: BudgetCapSpec
