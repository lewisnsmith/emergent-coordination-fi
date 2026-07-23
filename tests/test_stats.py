import numpy as np
import pytest

from flock.analysis.stats import (
    bootstrap_ci,
    equivalence_tost,
    holm_bonferroni,
    paired_randomization_test,
    paired_sign_flip_test,
    permutation_test,
    power_seeds,
    simulate_nested_power,
)


def test_permutation_detects_real_difference():
    rng = np.random.default_rng(0)
    vals = {f"a{i}": 1.0 + rng.normal(0, 0.05) for i in range(8)}
    vals |= {f"b{i}": 0.0 + rng.normal(0, 0.05) for i in range(8)}

    def stat(a, b):
        return float(np.mean([vals[u] for u in a]) - np.mean([vals[u] for u in b]))

    res = permutation_test(list(vals)[:8], list(vals)[8:], stat, n_permutations=500, seed=1)
    assert res.observed > 0.9
    assert res.p_value < 0.05


def test_permutation_null_does_not_reject_exchangeable_groups():
    # fixed seed chosen so the arbitrary split is unremarkable; a single draw's
    # p-value is uniform under H0, so this guards implementation, not calibration
    rng = np.random.default_rng(5)
    vals = {f"u{i}": rng.normal() for i in range(16)}

    def stat(a, b):
        return float(np.mean([vals[u] for u in a]) - np.mean([vals[u] for u in b]))

    res = permutation_test(list(vals)[:8], list(vals)[8:], stat, n_permutations=500, seed=2)
    assert res.p_value > 0.05


def test_bootstrap_ci_covers_mean():
    rng = np.random.default_rng(3)
    units = list(rng.normal(5.0, 1.0, 40))
    ci = bootstrap_ci(units, lambda u: float(np.mean(u)), n_resamples=500, seed=4)
    assert ci.low < 5.0 < ci.high
    assert ci.low < ci.estimate < ci.high


def test_holm_bonferroni_monotone_and_rejects():
    out = holm_bonferroni({"h1": 0.001, "h2": 0.03, "h3": 0.6}, alpha=0.05)
    assert out["h1"]["reject"] is True
    assert out["h3"]["reject"] is False
    assert out["h1"]["p_adjusted"] <= out["h2"]["p_adjusted"] <= out["h3"]["p_adjusted"]


def test_power_seeds_scales_with_variance():
    low_var = power_seeds([0.1, 0.11, 0.09, 0.1], target_delta=0.1)
    high_var = power_seeds([0.3, -0.2, 0.25, -0.15], target_delta=0.1)
    assert high_var > low_var
    assert "DIAGNOSTIC ONLY" in (power_seeds.__doc__ or "")


def test_tost_can_establish_practical_sameness_but_not_from_nonsignificance():
    equivalent = equivalence_tost([0.01, -0.01, 0.0, 0.005, -0.005], -0.1, 0.1)
    assert equivalent.equivalent
    too_uncertain = equivalence_tost([0.2, -0.2, 0.15, -0.15], -0.1, 0.1)
    assert not too_uncertain.equivalent


def test_paired_randomization_uses_independent_block_effects():
    result = paired_randomization_test([0.3] * 12, n_randomizations=2_000, seed=4)
    assert result.estimate == pytest.approx(0.3)
    assert result.p_value < 0.05


def test_sign_flip_uses_exact_enumeration_when_feasible():
    result = paired_sign_flip_test([0.3] * 8, seed=999)
    assert result.estimate == pytest.approx(0.3)
    assert result.p_value == pytest.approx(2 / (2**8))
    assert result.n_randomizations == 2**8
    assert result.exact is True
    assert "symmetric" in result.assumption


def test_nested_power_is_deterministic_and_recovers_provider_balanced_effect():
    settings = {
        "block_counts": [9],
        "agents_per_condition": 6,
        "steps_per_agent": 8,
        "provider_effects": {"alpha": -0.06, "beta": 0.0, "gamma": 0.06},
        "block_effect_sd": 0.04,
        "agent_sd": 0.08,
        "step_sd": 0.12,
        "n_simulations": 300,
        "seed": 418,
    }
    signal = simulate_nested_power(effect=0.16, **settings)
    repeated = simulate_nested_power(effect=0.16, **settings)
    null = simulate_nested_power(effect=0.0, **settings)

    assert signal == repeated
    assert signal != simulate_nested_power(effect=0.16, **(settings | {"seed": 419}))
    assert signal.points[0].mean_estimate == pytest.approx(0.16, abs=0.015)
    assert signal.points[0].rejection_rate > 0.9
    assert null.points[0].rejection_rate < 0.1
    assert signal.points[0].exact_sign_flip_fraction == 1.0


def test_nested_power_models_whole_block_missingness_and_monte_carlo_boundary():
    missing = simulate_nested_power(
        [12],
        effect=0.12,
        agents_per_condition=4,
        steps_per_agent=5,
        provider_effects={"alpha": -0.02, "beta": 0.02},
        missing_block_probability=0.35,
        n_simulations=200,
        seed=91,
    ).points[0]
    large = simulate_nested_power(
        [21],
        effect=0.12,
        agents_per_condition=4,
        steps_per_agent=5,
        n_simulations=20,
        n_randomizations=500,
        seed=91,
    ).points[0]

    assert missing.mean_observed_blocks == pytest.approx(7.8, abs=0.5)
    assert missing.analyzable_fraction > 0.98
    assert missing.exact_sign_flip_fraction == 1.0
    assert large.mean_observed_blocks == 21
    assert large.exact_sign_flip_fraction == 0.0
