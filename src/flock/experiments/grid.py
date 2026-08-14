"""Sweep runner: base experiment x models x personas x temperatures x seeds.

Each cell derives a config from the base (overriding every llm agent group),
so cells are addressed by config hash and a sweep is resumable: cells whose
run directory already holds a manifest are skipped.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path

from flock.core.config import ExperimentConfig, SweepConfig, load_experiment, load_sweep
from flock.experiments.runner import _require_config_execution_lease, make_run_id, run_config
from flock.logging_.decisions import RESULTS_DIR


@dataclass
class SweepSummary:
    completed: int = 0
    skipped: int = 0
    run_ids: list[str] = field(default_factory=list)


def derive_cell(
    base: ExperimentConfig,
    model: str | None,
    persona: str | None,
    temperature: float | None,
    seed: int,
) -> ExperimentConfig:
    cfg = base.model_copy(deep=True)
    cfg.seed = seed
    for cohort in cfg.cohorts:
        for group in cohort.agents:
            if group.kind != "llm":
                continue
            if model is not None:
                group.model = model
            if persona is not None:
                group.persona = persona
            if temperature is not None:
                group.temperature = temperature
    return cfg


def sweep_cells(sweep: SweepConfig, base: ExperimentConfig) -> list[ExperimentConfig]:
    models = sweep.models or [None]
    personas = sweep.personas or [None]
    temperatures = sweep.temperatures or [None]
    return [
        derive_cell(base, m, p, t, s)
        for m, p, t, s in itertools.product(models, personas, temperatures, sweep.seeds)
    ]


def run_sweep(
    config_path: Path,
    resume: bool = True,
    results_root: Path = RESULTS_DIR,
    *,
    execution_lease: object | None = None,
) -> SweepSummary:
    sweep = load_sweep(config_path)
    base = load_experiment(Path(sweep.base))
    cells = sweep_cells(sweep, base)
    for cfg in cells:
        _require_config_execution_lease(cfg, execution_lease)

    summary = SweepSummary()
    for cfg in cells:
        run_id = make_run_id(cfg)
        if resume and (results_root / run_id / "manifest.json").exists():
            summary.skipped += 1
            summary.run_ids.append(run_id)
            continue
        result = run_config(
            cfg,
            results_root=results_root,
            execution_lease=execution_lease,
        )
        summary.completed += 1
        summary.run_ids.append(result.run_id)
    return summary
