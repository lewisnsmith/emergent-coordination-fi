"""Pydantic schemas for experiment, sweep, persona, and model-registry YAML."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

CONFIG_DIR = Path("configs")


class ModelSpec(BaseModel):
    """One entry in configs/models.yaml."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["mock", "anthropic", "openai", "google", "openai_compatible"]
    model_id: str
    max_tokens: int = 1024
    family: str = ""
    deployment: Literal["mock", "api", "local"] = "api"
    frontier_eligible: bool = False
    verified_on: str | None = None
    pricing_key: str | None = None
    supports_seed: bool = False
    supports_structured_output: bool = False
    # mock-only knobs
    behavior: Literal["momentum", "contrarian", "random", "hold"] | None = None
    noise: float = 0.0


class PersonaConfig(BaseModel):
    """One persona YAML in configs/personas/."""

    model_config = ConfigDict(extra="forbid")

    name: str
    system_prompt: str
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    profile_version: int | str = 1
    financial_facts: dict[str, Any] = Field(default_factory=dict)
    identity_context: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] | dict[str, Any] = Field(default_factory=list)
    matched_set: dict[str, Any] | str | None = None
    counterfactual: dict[str, Any] = Field(default_factory=dict)
    counterfactual_of: str | None = None
    counterfactual_axis: str | None = None


class MPHIQAgentTreatment(BaseModel):
    """One agent's fully resolved MPHIQ assignment.

    A treatment is intentionally redundant with the executable ``AgentGroup``:
    the redundancy makes the scientific factor levels explicit and lets schema
    validation catch a config whose claimed assignment differs from what the
    runner will actually instantiate.
    """

    model_config = ConfigDict(extra="forbid")

    scheme_code: Annotated[str, StringConstraints(pattern=r"^[01]{5}$")]
    agent_index: int = Field(ge=0)
    model_id: str
    model_revision: str
    model_registry_key: str
    profile_id: str
    harness_id: str
    harness_temperature: float = Field(ge=0, le=2, allow_inf_nan=False)
    harness_memory: bool
    information_policy: str
    prompt_id: str
    prompt_semantic_group: str
    assignment_digest: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]

    @model_validator(mode="after")
    def validate_assignment_digest(self) -> MPHIQAgentTreatment:
        payload = self.model_dump(exclude={"assignment_digest"}, mode="json")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        if self.assignment_digest != expected:
            raise ValueError("MPHIQ assignment_digest does not match treatment fields")
        return self


class AgentGroup(BaseModel):
    """A homogeneous group of agents inside a cohort."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["llm", "momentum", "mean_reversion", "market_maker", "buy_hold", "random"]
    count: int = 1
    # llm agents
    model: str | None = None  # key into configs/models.yaml
    persona: str | None = None  # persona name in configs/personas/
    temperature: float = 0.7
    memory: bool = False
    harness_id: str = "default"
    prompt_id: str = "task-neutral-v1"
    information_policy: str = "shared-all"
    grounding_mode: Literal["audit", "strict"] = "strict"
    mphiq_treatment: MPHIQAgentTreatment | None = None
    # baseline agents: hyperparameters are randomized per-instance from the run
    # seed unless pinned here
    params: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mphiq_treatment(self) -> AgentGroup:
        treatment = self.mphiq_treatment
        if treatment is None:
            return self
        if self.kind != "llm" or self.count != 1:
            raise ValueError("MPHIQ treatments require one-agent LLM groups")
        executable_levels = {
            "model_registry_key": self.model,
            "profile_id": self.persona,
            "harness_id": self.harness_id,
            "harness_temperature": self.temperature,
            "harness_memory": self.memory,
            "information_policy": self.information_policy,
            "prompt_id": self.prompt_id,
        }
        mismatches = [
            name for name, actual in executable_levels.items() if actual != getattr(treatment, name)
        ]
        if mismatches:
            raise ValueError(
                "MPHIQ treatment disagrees with executable agent fields: " + ", ".join(mismatches)
            )
        return self


class CohortConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    agents: list[AgentGroup]


class MarketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["replay", "exchange"] = "replay"
    fee_bps: float = 5.0
    slippage_bps: float = 2.0  # replay only
    tick_size: float = 0.01  # exchange only


class RuntimeBudget(BaseModel):
    """Fail-closed limits for one resolved experiment run.

    ``request_cost_reserve_usd`` is a deliberately conservative pre-request
    reserve. It prevents the runner from starting a call that could cross the
    dollar ceiling; actual billed usage is reconciled after the response.
    """

    model_config = ConfigDict(extra="forbid")

    max_requests: int = Field(gt=0)
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    max_cost_usd: float = Field(gt=0, allow_inf_nan=False)
    request_cost_reserve_usd: float = Field(gt=0, allow_inf_nan=False)


class ExperimentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    seed: int = 42
    dataset: str  # name in datasets/manifests.json
    market: MarketConfig = Field(default_factory=MarketConfig)
    steps: int | None = None  # None = full dataset
    observation_window: int = 20
    initial_cash: float = 100_000.0
    # per-symbol share endowment at t0 (essential for exchange markets:
    # long-only agents with zero holdings can never provide the sell side)
    initial_position_per_symbol: float = 0.0
    max_position_per_symbol: float = 1_000.0
    model_policy: Literal["mock_only", "frontier_only"] = "frontier_only"
    runtime_budget: RuntimeBudget | None = None
    hypothesis_ids: list[str] = Field(default_factory=list)
    independent_block: str = "unspecified"
    dependence_cluster: str | None = None
    trajectory_id: str | None = None
    market_replica_id: str | None = None
    window_start: str | None = None
    window_end: str | None = None
    cohorts: list[CohortConfig]

    @model_validator(mode="after")
    def require_paid_run_budget(self) -> ExperimentConfig:
        if self.model_policy == "frontier_only" and self.runtime_budget is None:
            raise ValueError("frontier-only experiments require an explicit runtime_budget")
        return self

    @model_validator(mode="after")
    def validate_mphiq_assignment(self) -> ExperimentConfig:
        groups = [group for cohort in self.cohorts for group in cohort.agents]
        treatments = [group.mphiq_treatment for group in groups if group.mphiq_treatment]
        if not treatments:
            return self
        if len(treatments) != len(groups):
            raise ValueError("MPHIQ configs cannot mix treated and untreated agents")
        codes = {treatment.scheme_code for treatment in treatments}
        if len(codes) != 1:
            raise ValueError("all agents in an MPHIQ run must use one scheme_code")
        indices = sorted(treatment.agent_index for treatment in treatments)
        if indices != list(range(len(treatments))):
            raise ValueError("MPHIQ agent_index values must be unique and contiguous from zero")

        code = next(iter(codes))
        factor_values = (
            ("model_id", [treatment.model_id for treatment in treatments]),
            ("profile_id", [treatment.profile_id for treatment in treatments]),
            (
                "harness",
                [
                    json.dumps(
                        {
                            "harness_id": treatment.harness_id,
                            "temperature": treatment.harness_temperature,
                            "memory": treatment.harness_memory,
                        },
                        sort_keys=True,
                    )
                    for treatment in treatments
                ],
            ),
            (
                "information_policy",
                [treatment.information_policy for treatment in treatments],
            ),
            ("prompt_id", [treatment.prompt_id for treatment in treatments]),
        )
        different_assignments: dict[str, list[str]] = {}
        for bit, (field_name, values) in zip(code, factor_values, strict=True):
            counts = Counter(values)
            if bit == "1" and len(counts) != 1:
                raise ValueError(f"MPHIQ same-factor {field_name} resolved to multiple levels")
            if bit == "0":
                if len(counts) < 2:
                    raise ValueError(
                        f"MPHIQ different-factor {field_name} requires at least two levels"
                    )
                if max(counts.values()) - min(counts.values()) > 1:
                    raise ValueError(f"MPHIQ different-factor {field_name} is unbalanced")
                different_assignments[field_name] = values

        semantic_groups = {item.prompt_semantic_group for item in treatments}
        if len(semantic_groups) != 1:
            raise ValueError("MPHIQ prompt variants must share one semantic group")
        for left_index, (left_name, left_values) in enumerate(different_assignments.items()):
            for right_name, right_values in list(different_assignments.items())[left_index + 1 :]:
                left_to_right: dict[str, set[str]] = {}
                right_to_left: dict[str, set[str]] = {}
                for left, right in zip(left_values, right_values, strict=True):
                    left_to_right.setdefault(left, set()).add(right)
                    right_to_left.setdefault(right, set()).add(left)
                if all(len(values) == 1 for values in left_to_right.values()) and all(
                    len(values) == 1 for values in right_to_left.values()
                ):
                    raise ValueError(
                        "MPHIQ different factors are perfectly confounded: "
                        f"{left_name} and {right_name}"
                    )
        return self

    def config_hash(self) -> str:
        payload = json.dumps(self.model_dump(), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class SweepConfig(BaseModel):
    """Grid sweep: base experiment x models x personas x seeds."""

    model_config = ConfigDict(extra="forbid")

    name: str
    base: str  # path to base ExperimentConfig YAML
    models: list[str] = Field(default_factory=list)  # override llm groups' model
    personas: list[str] = Field(default_factory=list)  # override llm groups' persona
    temperatures: list[float] = Field(default_factory=list)
    seeds: list[int] = Field(default_factory=lambda: [42])


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_experiment(path: Path) -> ExperimentConfig:
    return ExperimentConfig.model_validate(load_yaml(path))


def load_sweep(path: Path) -> SweepConfig:
    return SweepConfig.model_validate(load_yaml(path))


def load_models(path: Path = CONFIG_DIR / "models.yaml") -> dict[str, ModelSpec]:
    raw = load_yaml(path)
    return {name: ModelSpec.model_validate(spec) for name, spec in raw.items()}


def load_persona(name: str, personas_dir: Path = CONFIG_DIR / "personas") -> PersonaConfig:
    return PersonaConfig.model_validate(load_yaml(personas_dir / f"{name}.yaml"))
