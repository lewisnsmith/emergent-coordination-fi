"""Study-level H1 aggregation over independent market-window/seed blocks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from flock.analysis import convergence
from flock.analysis.stats import bootstrap_ci, holm_bonferroni, paired_randomization_test


@dataclass(frozen=True)
class StudyInference:
    n_blocks: int
    mean_effect: float
    ci95: tuple[float, float]
    p_randomization: float
    p_holm: float
    reject: bool
    block_effects: dict[str, float]


def analyze_h1_study(run_dirs: list[Path], seed: int = 0) -> StudyInference:
    """Aggregate κ(LLM)-κ(baseline) without treating calls/pairs as replicates."""
    effects: dict[str, float] = {}
    for run_dir in run_dirs:
        run = convergence.load_run(run_dir)
        config = run["manifest"]["config"]
        block = f"{config['independent_block']}::seed-{config['seed']}"
        if block in effects:
            raise ValueError(f"duplicate independent block {block}")
        llm = convergence.cohort_metrics(run, "llm")["kappa"]
        baseline = convergence.cohort_metrics(run, "baseline")["kappa"]
        effects[block] = float(llm - baseline)
    if len(effects) < 2:
        raise ValueError("study inference requires at least two independent blocks")
    values = list(effects.values())
    randomization = paired_randomization_test(values, seed=seed)
    ci = bootstrap_ci(values, lambda sample: float(np.mean(sample)), seed=seed + 1)
    holm = holm_bonferroni({"H1": randomization.p_value})["H1"]
    return StudyInference(
        n_blocks=len(values),
        mean_effect=float(np.mean(values)),
        ci95=(ci.low, ci.high),
        p_randomization=randomization.p_value,
        p_holm=holm["p_adjusted"],
        reject=holm["reject"] and ci.low > 0,
        block_effects=effects,
    )


def write_study_inference(inference: StudyInference, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(inference), indent=2) + "\n")
    return output
