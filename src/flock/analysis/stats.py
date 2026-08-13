"""Statistical inference and simulation-based design diagnostics.

The nested power simulator is the confirmatory planning path.  The legacy
normal-approximation seed count is retained only as a quick diagnostic.  See
docs/research/experimental-methods-and-statistical-analysis.md.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
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


@dataclass(frozen=True)
class SignFlipResult:
    """Inference over independent paired block effects."""

    estimate: float
    p_value: float
    n_randomizations: int
    exact: bool
    assumption: str = "independent block effects are symmetric under the null"


@dataclass(frozen=True)
class NestedPowerPoint:
    """Operating characteristics for one planned independent-block count."""

    planned_blocks: int
    mean_observed_blocks: float
    analyzable_fraction: float
    rejection_rate: float
    monte_carlo_se: float
    mean_estimate: float
    exact_sign_flip_fraction: float


@dataclass(frozen=True)
class NestedPowerResult:
    """Deterministic simulation result across candidate block counts."""

    points: tuple[NestedPowerPoint, ...]
    n_simulations: int
    alpha: float
    seed: int
    decision_rule: str = (
        "two-sided paired sign-flip test over observed independent blocks; "
        "exact through 20 blocks, seeded Monte Carlo otherwise"
    )


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


def paired_sign_flip_test(
    block_differences: Sequence[float],
    n_randomizations: int = 10_000,
    seed: int = 0,
) -> SignFlipResult:
    """Apply the paper's sign-flip rule to independent paired block effects.

    Exact enumeration is used when at most 20 complete blocks remain.  Larger
    samples use a seeded Monte Carlo test with add-one correction.  This is
    design-based only when the signs reproduce an actual randomized assignment;
    otherwise the stated block-effect symmetry assumption is required.
    """
    values = np.asarray(block_differences, dtype=float)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("at least two independent block differences are required")
    if not np.all(np.isfinite(values)):
        raise ValueError("block differences must be finite")
    if n_randomizations < 1:
        raise ValueError("n_randomizations must be positive")

    observed = abs(float(values.mean()))
    if len(values) <= 20:
        null_sums = np.array([0.0])
        for value in values:
            null_sums = np.concatenate((null_sums - value, null_sums + value))
        total = len(null_sums)
        hits = int(
            np.sum(np.abs(null_sums / len(values)) >= observed - 1e-12)
        )
        return SignFlipResult(
            estimate=float(values.mean()),
            p_value=hits / total,
            n_randomizations=total,
            exact=True,
        )

    result = paired_randomization_test(
        [float(value) for value in values],
        n_randomizations=n_randomizations,
        seed=seed,
    )
    return SignFlipResult(
        estimate=result.estimate,
        p_value=result.p_value,
        n_randomizations=result.n_randomizations,
        exact=False,
    )


def simulate_nested_power(
    block_counts: Sequence[int],
    *,
    effect: float,
    agents_per_condition: int,
    steps_per_agent: int,
    provider_effects: Mapping[str, float] | None = None,
    block_effect_sd: float = 0.05,
    agent_sd: float = 0.1,
    step_sd: float = 0.2,
    missing_block_probability: float = 0.0,
    n_simulations: int = 1_000,
    alpha: float = 0.05,
    n_randomizations: int = 10_000,
    seed: int = 0,
) -> NestedPowerResult:
    """Estimate power for the full paired, nested independent-block design.

    Each planned block is assigned a provider in a randomized balanced rotation.
    The provider value is an additive deviation from ``effect``.  A block gets
    its own random treatment-effect deviation.  Separate treatment and control
    agents have nested agent intercepts and per-step noise; only their within-
    block mean contrast enters inference.  Whole blocks can then be missing.

    Missing or incomplete simulations with fewer than two observed blocks count
    as non-rejections, so ``rejection_rate`` is unconditional operating power.
    ``analyzable_fraction`` reports how often inference was possible.  Supplying
    the same seed and inputs yields byte-for-byte equal result objects.
    """
    counts = tuple(int(value) for value in block_counts)
    if not counts or any(value < 2 for value in counts):
        raise ValueError("block_counts must contain values of at least two")
    if agents_per_condition < 1 or steps_per_agent < 1:
        raise ValueError("agents_per_condition and steps_per_agent must be positive")
    if n_simulations < 1 or n_randomizations < 1:
        raise ValueError("simulation and randomization counts must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    if not 0 <= missing_block_probability < 1:
        raise ValueError("missing_block_probability must be in [0, 1)")
    numeric = (effect, block_effect_sd, agent_sd, step_sd)
    if not all(np.isfinite(value) for value in numeric):
        raise ValueError("effect and standard deviations must be finite")
    if any(value < 0 for value in (block_effect_sd, agent_sd, step_sd)):
        raise ValueError("standard deviations cannot be negative")

    effects = dict({"default": 0.0} if provider_effects is None else provider_effects)
    if not effects or any(not name for name in effects):
        raise ValueError("at least one named provider is required")
    if not all(np.isfinite(value) for value in effects.values()):
        raise ValueError("provider effects must be finite")
    provider_names = tuple(sorted(effects))
    root_sequence = np.random.SeedSequence(seed)
    count_sequences = root_sequence.spawn(len(counts))
    points: list[NestedPowerPoint] = []

    for planned_blocks, count_sequence in zip(counts, count_sequences, strict=True):
        simulation_sequences = count_sequence.spawn(n_simulations)
        estimates: list[float] = []
        observed_counts: list[int] = []
        rejections = 0
        analyzable = 0
        exact_tests = 0

        for simulation_sequence in simulation_sequences:
            data_sequence, test_sequence = simulation_sequence.spawn(2)
            rng = np.random.default_rng(data_sequence)
            provider_order = np.asarray(provider_names, dtype=object)
            rng.shuffle(provider_order)
            assignments = np.resize(provider_order, planned_blocks)
            rng.shuffle(assignments)
            block_differences: list[float] = []

            for provider in assignments:
                true_effect = (
                    effect
                    + effects[str(provider)]
                    + float(rng.normal(0.0, block_effect_sd))
                )
                agent_intercepts = rng.normal(
                    0.0, agent_sd, size=(2, agents_per_condition, 1)
                )
                step_errors = rng.normal(
                    0.0,
                    step_sd,
                    size=(2, agents_per_condition, steps_per_agent),
                )
                observations = agent_intercepts + step_errors
                observations[1, :, :] += true_effect
                difference = float(observations[1].mean() - observations[0].mean())
                if rng.random() >= missing_block_probability:
                    block_differences.append(difference)

            observed_counts.append(len(block_differences))
            if len(block_differences) < 2:
                continue
            analyzable += 1
            estimates.append(float(np.mean(block_differences)))
            test_seed = int(test_sequence.generate_state(1, dtype=np.uint64)[0])
            inference = paired_sign_flip_test(
                block_differences,
                n_randomizations=n_randomizations,
                seed=test_seed,
            )
            exact_tests += int(inference.exact)
            rejections += int(inference.p_value <= alpha)

        rejection_rate = rejections / n_simulations
        monte_carlo_se = float(
            np.sqrt(rejection_rate * (1.0 - rejection_rate) / n_simulations)
        )
        points.append(
            NestedPowerPoint(
                planned_blocks=planned_blocks,
                mean_observed_blocks=float(np.mean(observed_counts)),
                analyzable_fraction=analyzable / n_simulations,
                rejection_rate=rejection_rate,
                monte_carlo_se=monte_carlo_se,
                mean_estimate=float(np.mean(estimates)) if estimates else float("nan"),
                exact_sign_flip_fraction=exact_tests / analyzable if analyzable else 0.0,
            )
        )

    return NestedPowerResult(
        points=tuple(points),
        n_simulations=n_simulations,
        alpha=alpha,
        seed=seed,
    )


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
    """DIAGNOSTIC ONLY: normal-approximation run count from pilot variance.

    This shortcut ignores nesting, provider heterogeneity, missing blocks, and
    the confirmatory sign-flip decision rule.  It must not authorize paid or
    confirmatory runs; use :func:`simulate_nested_power` for study planning.
    """
    from scipy.stats import norm

    sd = float(np.std(pilot_deltas, ddof=1))
    if sd == 0:
        return 2
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    n = ((z_a + z_b) * sd / abs(target_delta)) ** 2
    return int(min(max(np.ceil(n), 2), max_seeds))
