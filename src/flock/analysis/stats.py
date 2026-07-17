"""Statistical inference: permutation tests, BCa bootstrap, Holm-Bonferroni,
seed-count power analysis. See docs/research/03-metrics.md."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PermutationResult:
    observed: float
    p_value: float
    n_permutations: int


@dataclass(frozen=True)
class TOSTResult:
    estimate: float
    lower_bound: float
    upper_bound: float
    p_lower: float
    p_upper: float
    alpha: float
    equivalent: bool


@dataclass(frozen=True)
class PairedRandomizationResult:
    estimate: float
    p_value: float
    n_randomizations: int


def permutation_test(
    group_a: Sequence[str],
    group_b: Sequence[str],
    statistic: Callable[[list[str], list[str]], float],
    n_permutations: int = 10_000,
    seed: int = 0,
) -> PermutationResult:
    """Two-sided permutation test relabeling *units* (agents) across groups.

    `statistic(a_units, b_units)` computes the contrast for a given labeling.
    """
    rng = np.random.default_rng(seed)
    pooled = list(group_a) + list(group_b)
    n_a = len(group_a)
    observed = statistic(list(group_a), list(group_b))
    hits = 0
    for _ in range(n_permutations):
        perm = rng.permutation(len(pooled))
        a = [pooled[i] for i in perm[:n_a]]
        b = [pooled[i] for i in perm[n_a:]]
        if abs(statistic(a, b)) >= abs(observed) - 1e-12:
            hits += 1
    # add-one smoothing (Phipson & Smyth): valid p-values under permutation
    p = (hits + 1) / (n_permutations + 1)
    return PermutationResult(observed, p, n_permutations)


def paired_randomization_test(
    block_differences: Sequence[float],
    n_randomizations: int = 10_000,
    seed: int = 0,
) -> PairedRandomizationResult:
    """Two-sided sign-flip test over independent paired market blocks."""
    values = np.asarray(block_differences, dtype=float)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("at least two independent block differences are required")
    observed = float(values.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice((-1.0, 1.0), size=(n_randomizations, len(values)))
    null = (signs * values).mean(axis=1)
    hits = int(np.sum(np.abs(null) >= abs(observed) - 1e-12))
    p = (hits + 1) / (n_randomizations + 1)
    return PairedRandomizationResult(observed, p, n_randomizations)


def equivalence_tost(
    differences: Sequence[float],
    lower_bound: float,
    upper_bound: float,
    alpha: float = 0.05,
) -> TOSTResult:
    """Paired two-one-sided equivalence test over independent block effects.

    Equivalence is established only when both one-sided nulls are rejected;
    an ordinary nonsignificant difference is not evidence of sameness.
    """
    from scipy.stats import t

    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("at least two independent block differences are required")
    if lower_bound >= upper_bound:
        raise ValueError("lower_bound must be smaller than upper_bound")
    estimate = float(values.mean())
    se = float(values.std(ddof=1) / np.sqrt(len(values)))
    if se == 0:
        p_lower = 0.0 if estimate > lower_bound else 1.0
        p_upper = 0.0 if estimate < upper_bound else 1.0
    else:
        df = len(values) - 1
        p_lower = float(t.sf((estimate - lower_bound) / se, df))
        p_upper = float(t.cdf((estimate - upper_bound) / se, df))
    return TOSTResult(
        estimate=estimate,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        p_lower=p_lower,
        p_upper=p_upper,
        alpha=alpha,
        equivalent=p_lower < alpha and p_upper < alpha,
    )


@dataclass(frozen=True)
class BootstrapCI:
    estimate: float
    low: float
    high: float
    level: float
    n_resamples: int


def bootstrap_ci(
    units: Sequence,
    statistic: Callable[[list], float],
    n_resamples: int = 10_000,
    level: float = 0.95,
    seed: int = 0,
) -> BootstrapCI:
    """BCa bootstrap CI over exchangeable units (agents or seeds)."""
    from scipy.stats import norm

    units = list(units)
    n = len(units)
    estimate = statistic(units)
    rng = np.random.default_rng(seed)
    boots = np.array(
        [statistic([units[i] for i in rng.integers(0, n, n)]) for _ in range(n_resamples)]
    )

    # bias correction
    prop_less = np.mean(boots < estimate)
    z0 = float(norm.ppf(np.clip(prop_less, 1e-9, 1 - 1e-9)))
    # acceleration via jackknife
    jack = np.array([statistic(units[:i] + units[i + 1 :]) for i in range(n)])
    jbar = jack.mean()
    num = ((jbar - jack) ** 3).sum()
    den = 6.0 * (((jbar - jack) ** 2).sum()) ** 1.5
    a = num / den if den > 0 else 0.0

    alpha = (1 - level) / 2
    z_lo = float(norm.ppf(alpha))
    z_hi = float(norm.ppf(1 - alpha))

    def adj(z: float) -> float:
        return float(norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z))))

    lo = float(np.quantile(boots, np.clip(adj(z_lo), 0, 1)))
    hi = float(np.quantile(boots, np.clip(adj(z_hi), 0, 1)))
    return BootstrapCI(estimate, lo, hi, level, n_resamples)


def holm_bonferroni(p_values: dict[str, float], alpha: float = 0.05) -> dict[str, dict]:
    """Holm step-down correction. Returns per-hypothesis adjusted p and rejection."""
    items = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(items)
    out: dict[str, dict] = {}
    running_max = 0.0
    rejecting = True
    for rank, (name, p) in enumerate(items):
        adj = min(1.0, (m - rank) * p)
        running_max = max(running_max, adj)
        adj = running_max  # enforce monotonicity
        if adj > alpha:
            rejecting = False
        out[name] = {"p": p, "p_adjusted": adj, "reject": rejecting and adj <= alpha}
    return out


def power_seeds(
    pilot_deltas: Sequence[float],
    target_delta: float,
    alpha: float = 0.05,
    power: float = 0.8,
    max_seeds: int = 200,
) -> int:
    """Seeds per cell needed to detect `target_delta` given pilot run-level
    variance of the contrast (two-sided one-sample t against 0)."""
    from scipy.stats import norm

    sd = float(np.std(pilot_deltas, ddof=1))
    if sd == 0:
        return 2
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    n = ((z_a + z_b) * sd / abs(target_delta)) ** 2
    return int(min(max(np.ceil(n), 2), max_seeds))
