"""Pydantic schemas for experiment, sweep, persona, and model-registry YAML."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

CONFIG_DIR = Path("configs")


class ModelSpec(BaseModel):
    """One entry in configs/models.yaml."""

    provider: Literal["mock", "anthropic", "openai", "google", "openai_compatible"]
    model_id: str
    max_tokens: int = 1024
    # mock-only knobs
    behavior: Literal["momentum", "contrarian", "random", "hold"] | None = None
    noise: float = 0.0


class PersonaConfig(BaseModel):
    """One persona YAML in configs/personas/."""

    name: str
    system_prompt: str
    risk_tolerance: Literal["low", "medium", "high"] = "medium"


class AgentGroup(BaseModel):
    """A homogeneous group of agents inside a cohort."""

    kind: Literal[
        "llm", "momentum", "mean_reversion", "market_maker", "buy_hold", "random"
    ]
    count: int = 1
    # llm agents
    model: str | None = None  # key into configs/models.yaml
    persona: str | None = None  # persona name in configs/personas/
    temperature: float = 0.7
    memory: bool = False
    # baseline agents: hyperparameters are randomized per-instance from the run
    # seed unless pinned here
    params: dict[str, float] = Field(default_factory=dict)


class CohortConfig(BaseModel):
    name: str
    agents: list[AgentGroup]


class MarketConfig(BaseModel):
    kind: Literal["replay", "exchange"] = "replay"
    fee_bps: float = 5.0
    slippage_bps: float = 2.0  # replay only
    tick_size: float = 0.01  # exchange only


class ExperimentConfig(BaseModel):
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
    cohorts: list[CohortConfig]

    def config_hash(self) -> str:
        payload = json.dumps(self.model_dump(), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class SweepConfig(BaseModel):
    """Grid sweep: base experiment x models x personas x seeds."""

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
