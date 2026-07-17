"""Study-level H1 aggregation over genuinely independent market blocks.

Response seeds, agents, calls, pairs, and steps are nested observations.  They
must never manufacture an additional independent market unit.
"""

from __future__ import annotations

import itertools
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
    p_sign_flip: float
    p_holm: float
    reject: bool
    block_effects: dict[str, float]
    dependence_clusters: dict[str, str]
    method: str = "paired sign-flip test under block-effect symmetry"
    verified: bool = True

    @property
    def p_randomization(self) -> float:
        """Backward-compatible alias; do not describe this as design-based RI."""
        return self.p_sign_flip


_PLACEHOLDER_BLOCKS = {
    "",
    "unspecified",
    "equities-window-config-required",
    "prediction-window-config-required",
}


def _exact_or_monte_carlo_sign_flip(values: list[float], seed: int) -> float:
    """Two-sided sign-flip p-value over independent block effects.

    Exact enumeration is used through 20 blocks. Larger studies use the
    seeded Monte Carlo implementation with its finite-sample correction.
    """
    observed = abs(float(np.mean(values)))
    if len(values) <= 20:
        hits = 0
        total = 2 ** len(values)
        for signs in itertools.product((-1.0, 1.0), repeat=len(values)):
            candidate = abs(float(np.mean(np.asarray(signs) * values)))
            hits += candidate >= observed - 1e-12
        return hits / total
    return paired_randomization_test(values, seed=seed).p_value


def analyze_h1_study(run_dirs: list[Path], seed: int = 0) -> StudyInference:
    """Aggregate κ(LLM)-κ(classical) over independent market units.

    ``independent_block`` identifies the market trajectory/window itself. A
    model sampling seed is deliberately excluded from the unit key.
    ``dependence_cluster`` must also be unique; overlapping windows therefore
    cannot masquerade as independent evidence.
    """
    effects: dict[str, float] = {}
    clusters: dict[str, str] = {}
    seen_clusters: set[str] = set()
    for run_dir in run_dirs:
        run = convergence.load_run(run_dir)
        config = run["manifest"]["config"]
        block = str(config.get("independent_block", "")).strip()
        if block in _PLACEHOLDER_BLOCKS or "config-required" in block:
            raise ValueError(f"invalid independent block identifier {block!r}")
        if block in effects:
            raise ValueError(f"duplicate independent block {block}")
        cluster = str(config.get("dependence_cluster", block)).strip()
        if not cluster:
            raise ValueError(f"missing dependence cluster for {block}")
        if cluster in seen_clusters:
            raise ValueError(f"duplicate dependence cluster {cluster}")
        llm = convergence.cohort_metrics(run, "llm")["kappa"]
        baseline = convergence.cohort_metrics(run, "baseline")["kappa"]
        effect = float(llm - baseline)
        if not np.isfinite(effect):
            raise ValueError(f"non-finite H1 effect for independent block {block}")
        effects[block] = effect
        clusters[block] = cluster
        seen_clusters.add(cluster)
    if len(effects) < 2:
        raise ValueError("study inference requires at least two independent blocks")
    values = list(effects.values())
    p_sign_flip = _exact_or_monte_carlo_sign_flip(values, seed)
    ci = bootstrap_ci(values, lambda sample: float(np.mean(sample)), seed=seed + 1)
    holm = holm_bonferroni({"H1": p_sign_flip})["H1"]
    return StudyInference(
        n_blocks=len(values),
        mean_effect=float(np.mean(values)),
        ci95=(ci.low, ci.high),
        p_sign_flip=p_sign_flip,
        p_holm=holm["p_adjusted"],
        reject=holm["reject"] and ci.low > 0,
        block_effects=effects,
        dependence_clusters=clusters,
    )


def write_study_inference(inference: StudyInference, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(inference), indent=2) + "\n")
    return output
