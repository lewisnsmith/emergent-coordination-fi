from datetime import date

import pytest

from flock.experiments.costs import (
    APIPrice,
    EffectiveRate,
    PricingCatalog,
    TokenCase,
    VMPrice,
    Workload,
    estimate_costs,
    load_run_matrix,
    load_workload,
)
from flock.experiments.design import (
    balanced_levels,
    generate_mphiq_schemes,
    generate_pressure_cells,
)


def test_all_mphiq_schemes_exist_with_documented_bit_semantics():
    schemes = generate_mphiq_schemes()
    assert len(schemes) == 32
    assert len({scheme.code for scheme in schemes}) == 32
    assert schemes[0].code == "00000" and len(schemes[0].different_factors) == 5
    assert schemes[-1].code == "11111" and len(schemes[-1].same_factors) == 5


def test_pressure_design_is_full_three_by_two_by_two_by_two():
    cells = generate_pressure_cells()
    assert len(cells) == 24
    assert len({cell.code for cell in cells}) == 24
    assert {cell.stakes for cell in cells} == {
        "ordinary", "high_financial", "fictional_life_or_death"
    }


def test_balanced_levels_differ_by_at_most_one():
    assigned = balanced_levels(["a", "b", "c"], 10)
    counts = [assigned.count(level) for level in ("a", "b", "c")]
    assert max(counts) - min(counts) <= 1


def test_cost_estimator_includes_retries_vm_and_contingency():
    pricing = PricingCatalog(
        version="test",
        api={
            "m": APIPrice(
                input_per_million_usd=2,
                output_per_million_usd=10,
                source="official",
                verified_on="2026-01-01",
            )
        },
        vm={
            "h100": VMPrice(
                hourly_usd=4, gpu_count=1, gpu_type="H100", source="official",
                verified_on="2026-01-01",
            )
        },
    )
    workload = Workload(
        calls=1000,
        model_mix={"m": 1.0},
        token_cases={
            "low": TokenCase(input_tokens=100, output_tokens=10),
            "expected": TokenCase(input_tokens=200, output_tokens=20, retry_rate=0.1),
            "high": TokenCase(input_tokens=400, output_tokens=40, retry_rate=0.2),
        },
        local_gpu_hours={"h100": 10},
        storage_usd=5,
        contingency=0.2,
    )
    result = estimate_costs(workload, pricing)
    assert result.vm_usd == 40
    assert result.low_api_usd < result.expected_api_usd < result.high_api_usd
    assert result.total_expected_usd == pytest.approx(
        (result.expected_api_usd + 40 + 5) * 1.2
    )
    assert result.pricing_version == "test"


def test_cost_estimator_fails_closed_on_unknown_model():
    pricing = PricingCatalog(version="test", api={}, vm={})
    workload = Workload(
        calls=1,
        model_mix={"unknown": 1.0},
        token_cases={
            name: TokenCase(input_tokens=1, output_tokens=1)
            for name in ("low", "expected", "high")
        },
    )
    with pytest.raises(ValueError, match="no verified API price"):
        estimate_costs(workload, pricing)


def test_committed_run_matrix_has_staged_stop_go_envelopes():
    matrix = load_run_matrix()
    assert set(matrix.scenarios) == {"pilot", "base", "high"}
    assert matrix.scenarios["pilot"].total_calls < matrix.scenarios["base"].total_calls
    assert matrix.scenarios["base"].recommended_credit_envelope_usd.total > 0


def test_effective_dated_price_changes_estimate():
    pricing = PricingCatalog(
        version="dated",
        api={
            "m": APIPrice(
                input_per_million_usd=2,
                output_per_million_usd=10,
                future_rates=[
                    EffectiveRate(
                        effective_from=date(2026, 9, 1),
                        input_per_million_usd=3,
                        output_per_million_usd=15,
                    )
                ],
                source="official",
                verified_on="2026-07-17",
            )
        },
        vm={},
    )
    workload = Workload(
        calls=1000,
        model_mix={"m": 1.0},
        token_cases={
            name: TokenCase(input_tokens=1000, output_tokens=100)
            for name in ("low", "expected", "high")
        },
    )
    before = estimate_costs(workload, pricing, as_of=date(2026, 8, 31))
    after = estimate_costs(workload, pricing, as_of=date(2026, 9, 1))
    assert after.expected_api_usd > before.expected_api_usd


def test_legacy_run_matrix_cannot_masquerade_as_calculable_workload():
    with pytest.raises(ValueError, match="legacy summary"):
        load_workload()
