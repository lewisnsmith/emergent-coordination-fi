"""Schemas and validation for the complete research-program catalog.

The ordinary :mod:`flock.core.config` schema describes a runnable market
simulation.  This module describes the larger research program, including
observational, human-subjects, and interpretability studies that must not be
misrepresented as ordinary trading runs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class HypothesisSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    claim: str
    claim_boundary: str


class ExperimentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    hypotheses: list[str]
    mode: Literal[
        "simulation",
        "observational",
        "human_subjects",
        "projection",
        "black_box_interpretability",
        "local_mechanistic_interpretability",
        "data_product",
        "validation",
    ]
    question: str
    status: Literal["executable", "scaffolded", "blocked_external"]
    estimand: str
    independent_unit: str
    inputs: list[str] = Field(default_factory=list)
    treatments: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    inference: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    executable_configs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)


class ResearchProgram(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    hypotheses: dict[str, HypothesisSpec]
    experiments: dict[str, ExperimentSpec]


class ProgramValidation(BaseModel):
    ok: bool
    errors: list[str]
    warnings: list[str]
    n_hypotheses: int
    n_experiments: int
    n_executable: int
    n_scaffolded: int
    n_blocked_external: int


def load_research_program(path: Path = Path("configs/research-program.yaml")) -> ResearchProgram:
    with path.open() as f:
        return ResearchProgram.model_validate(yaml.safe_load(f))


def validate_research_program(
    program: ResearchProgram,
    repo_root: Path = Path("."),
) -> ProgramValidation:
    """Validate internal references without pretending external data exist."""
    errors: list[str] = []
    warnings: list[str] = []
    known_hypotheses = set(program.hypotheses)
    for experiment_id, experiment in program.experiments.items():
        unknown = sorted(set(experiment.hypotheses) - known_hypotheses)
        if unknown:
            errors.append(f"{experiment_id}: unknown hypotheses {unknown}")
        for config in experiment.executable_configs:
            if not (repo_root / config).exists():
                errors.append(f"{experiment_id}: missing executable config {config}")
        if experiment.status == "executable" and not experiment.executable_configs:
            errors.append(f"{experiment_id}: executable study has no executable config")
        if experiment.mode in {"human_subjects", "observational"}:
            if not experiment.dependencies:
                warnings.append(f"{experiment_id}: external study has no declared dependencies")
        if not experiment.verification:
            errors.append(f"{experiment_id}: no verification contract")
        if not experiment.outputs:
            errors.append(f"{experiment_id}: no output contract")

    counts = {status: 0 for status in ("executable", "scaffolded", "blocked_external")}
    for experiment in program.experiments.values():
        counts[experiment.status] += 1
    return ProgramValidation(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        n_hypotheses=len(program.hypotheses),
        n_experiments=len(program.experiments),
        n_executable=counts["executable"],
        n_scaffolded=counts["scaffolded"],
        n_blocked_external=counts["blocked_external"],
    )
