import numpy as np
import pytest

from flock.analysis.stats import (
    bootstrap_ci,
    equivalence_tost,
    holm_bonferroni,
    paired_randomization_test,
    permutation_test,
    power_seeds,
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


def test_tost_can_establish_practical_sameness_but_not_from_nonsignificance():
    equivalent = equivalence_tost([0.01, -0.01, 0.0, 0.005, -0.005], -0.1, 0.1)
    assert equivalent.equivalent
    too_uncertain = equivalence_tost([0.2, -0.2, 0.15, -0.15], -0.1, 0.1)
    assert not too_uncertain.equivalent


def test_paired_randomization_uses_independent_block_effects():
    result = paired_randomization_test([0.3] * 12, n_randomizations=2_000, seed=4)
    assert result.estimate == pytest.approx(0.3)
    assert result.p_value < 0.05
