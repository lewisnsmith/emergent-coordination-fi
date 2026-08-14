import pandas as pd
import pytest

from flock.analysis.crossed import analyze_first_paper_estimands, mphiq_cube_edges


def _identity(block: str) -> dict[str, str]:
    return {
        "independent_block": block,
        "dependence_cluster": f"cluster-{block}",
        "trajectory_id": f"trajectory-{block}",
    }


def _crossed_rows(values: dict[str, tuple[float, float, float, float]]) -> pd.DataFrame:
    rows = []
    cells = (
        ("llm", "homogeneous"),
        ("llm", "heterogeneous"),
        ("classical", "homogeneous"),
        ("classical", "heterogeneous"),
    )
    for block, block_values in values.items():
        for (technology, ecology), value in zip(cells, block_values, strict=True):
            for family in ("family-a", "family-b"):
                rows.append(
                    {
                        **_identity(block),
                        "metric": "kappa",
                        "technology": technology,
                        "ecology": ecology,
                        "family": f"{technology}-{family}",
                        "value": value,
                    }
                )
    return pd.DataFrame(rows)


def _lineage_rows() -> pd.DataFrame:
    rows = []
    values = {
        "b1": {"same_model": 0.9, "same_provider": 0.7, "cross_provider": 0.4},
        "b2": {"same_model": 0.8, "same_provider": 0.6, "cross_provider": 0.2},
    }
    for block, relationships in values.items():
        for relationship, value in relationships.items():
            for stratum in ("provider-a", "provider-b"):
                rows.append(
                    {
                        **_identity(block),
                        "metric": "kappa",
                        "relationship": relationship,
                        "family_stratum": stratum,
                        "pair_id": f"{relationship}-{stratum}",
                        "value": value,
                    }
                )
    return pd.DataFrame(rows)


def _mphiq_rows() -> pd.DataFrame:
    rows = []
    for block, base_effect in (("b1", 0.2), ("b2", 0.4)):
        for index, (component, edges) in enumerate(mphiq_cube_edges().items()):
            for same, different in edges:
                rows.append(
                    {
                        **_identity(block),
                        "metric": "kappa",
                        "component": component,
                        "pair_id": f"pair-{component}-{different}-{same}",
                        "code_same": same,
                        "code_different": different,
                        "value_same": 0.8,
                        "value_different": 0.8 - base_effect - index * 0.01,
                    }
                )
    return pd.DataFrame(rows)


def _estimate(result, estimand_id: str) -> float:
    row = result.effects.loc[result.effects["estimand_id"] == estimand_id]
    assert len(row) == 1
    return float(row.iloc[0]["estimate"])


def test_crossed_design_recovers_hand_computed_factorial_effects():
    crossed = _crossed_rows(
        {
            # llm-h, llm-heterogeneous, classical-h, classical-heterogeneous
            "b1": (2.0, 5.0, 1.0, 3.0),
            "b2": (2.0, 5.0, 1.0, 3.0),
        }
    )

    result = analyze_first_paper_estimands(
        crossed, confirmatory_metrics=["kappa"], n_bootstrap=200
    )

    assert _estimate(result, "H1.delta_tech") == pytest.approx(1.5)
    assert _estimate(result, "H1.delta_int") == pytest.approx(-1.0)
    assert not {
        "H1.technology.homogeneous",
        "H1.technology.heterogeneous",
    } & set(result.effects["estimand_id"])
    h1 = result.effects.loc[result.effects["hypothesis"] == "H1"]
    assert set(h1["inference_role"]) == {"sensitivity_only"}
    assert not h1["confirmatory"].any()
    assert not h1["paper_eligible"].any()
    assert set(h1["multiplicity_status"]) == {"excluded_sensitivity"}
    assert h1["p_adjusted"].isna().all()
    assert set(result.effects["independent_n"]) == {2}
    assert len(result.block_effects) == 4


def test_factorial_contrasts_do_not_mistake_ecology_for_technology():
    crossed = _crossed_rows(
        {
            "b1": (1.0, 3.0, 1.0, 3.0),
            "b2": (2.0, 5.0, 2.0, 5.0),
        }
    )

    # Comparing LLM heterogeneous (4) to classical homogeneous (1.5) would
    # manufacture a 2.5-point technology effect. The crossed estimands are 0.
    result = analyze_first_paper_estimands(
        crossed, confirmatory_metrics=["kappa"], n_bootstrap=100
    )

    assert _estimate(result, "H1.delta_tech") == 0.0
    assert _estimate(result, "H1.delta_int") == 0.0


def test_family_balancing_prevents_endpoint_count_reweighting():
    crossed = _crossed_rows(
        {
            "b1": (0.0, 0.0, 5.0, 5.0),
            "b2": (0.0, 0.0, 5.0, 5.0),
        }
    )
    llm = crossed["technology"] == "llm"
    family_a = crossed["family"] == "llm-family-a"
    crossed.loc[llm & family_a, "value"] = 10.0
    # This field documents unequal endpoint counts but cannot reweight the
    # already aggregated family rows: (10 + 0) / 2 equals the classical 5.
    crossed["within_family_endpoint_count"] = 1
    crossed.loc[llm & family_a, "within_family_endpoint_count"] = 100

    result = analyze_first_paper_estimands(
        crossed, confirmatory_metrics=["kappa"], n_bootstrap=100
    )

    assert _estimate(result, "H1.delta_tech") == 0.0
    assert _estimate(result, "H1.delta_int") == 0.0


def test_h3_and_full_cube_h4_are_aggregated_to_one_effect_per_block():
    crossed = _crossed_rows(
        {
            "b1": (2.0, 5.0, 1.0, 3.0),
            "b2": (4.0, 7.0, 2.0, 4.0),
        }
    )

    result = analyze_first_paper_estimands(
        crossed,
        confirmatory_metrics=["kappa"],
        lineage_rows=_lineage_rows(),
        mphiq_rows=_mphiq_rows(),
        n_bootstrap=200,
    )

    assert _estimate(result, "H3.same_model_vs_cross_provider") == pytest.approx(0.55)
    assert _estimate(result, "H3.same_provider_vs_cross_provider") == pytest.approx(0.35)
    assert _estimate(result, "H4.mphiq.M") == pytest.approx(0.3)
    assert _estimate(result, "H4.mphiq.Q") == pytest.approx(0.34)
    assert _estimate(result, "H4.information_vs_profile") == pytest.approx(0.02)
    assert _estimate(result, "H4.information_vs_question") == pytest.approx(-0.01)
    assert len(result.effects) == 11
    assert result.multiplicity["frozen_contrasts"] == []
    assert len(result.multiplicity["provisional_contrasts"]) == 9
    assert len(result.multiplicity["sensitivity_contrasts"]) == 2
    assert not result.multiplicity["paper_eligible"]
    provisional = result.effects.loc[
        result.effects["multiplicity_status"] == "provisional_holm"
    ]
    assert all(provisional["p_adjusted"] >= provisional["p_value"])
    assert set(result.effects["independent_n"]) == {2}
    h4_components = result.block_effects.loc[
        result.block_effects["estimand_id"].isin(
            [f"H4.mphiq.{component}" for component in "MPHIQ"]
        )
    ]
    assert set(h4_components["nested_observations_aggregated"]) == {16}


def test_rejects_reused_trajectory_cluster_and_nested_rows_as_independent_evidence():
    crossed = _crossed_rows(
        {
            "b1": (2.0, 5.0, 1.0, 3.0),
            "b2": (4.0, 7.0, 2.0, 4.0),
        }
    )
    crossed.loc[crossed["independent_block"] == "b2", "trajectory_id"] = "trajectory-b1"
    with pytest.raises(ValueError, match="reuses trajectory"):
        analyze_first_paper_estimands(
            crossed, confirmatory_metrics=["kappa"], n_bootstrap=10
        )

    crossed = _crossed_rows(
        {
            "b1": (2.0, 5.0, 1.0, 3.0),
            "b2": (4.0, 7.0, 2.0, 4.0),
        }
    )
    crossed["agent_id"] = "agent-1"
    with pytest.raises(ValueError, match="family-level aggregates"):
        analyze_first_paper_estimands(
            crossed, confirmatory_metrics=["kappa"], n_bootstrap=10
        )


def test_rejects_incomplete_cells_changed_family_sets_and_non_hamming_pairs():
    crossed = _crossed_rows(
        {
            "b1": (2.0, 5.0, 1.0, 3.0),
            "b2": (4.0, 7.0, 2.0, 4.0),
        }
    )
    incomplete = crossed.drop(crossed.index[0])
    with pytest.raises(ValueError, match="changes the frozen family set"):
        analyze_first_paper_estimands(
            incomplete, confirmatory_metrics=["kappa"], n_bootstrap=10
        )

    ecology_confounded = crossed.copy()
    heterogeneous_llm = (ecology_confounded["technology"] == "llm") & (
        ecology_confounded["ecology"] == "heterogeneous"
    )
    ecology_confounded.loc[heterogeneous_llm, "family"] += "-different-ecology"
    with pytest.raises(ValueError, match="family composition across ecologies"):
        analyze_first_paper_estimands(
            ecology_confounded, confirmatory_metrics=["kappa"], n_bootstrap=10
        )

    mphiq = _mphiq_rows()
    mphiq.loc[0, "code_different"] = "00001"
    with pytest.raises(ValueError, match="Hamming-one"):
        analyze_first_paper_estimands(
            crossed,
            confirmatory_metrics=["kappa"],
            mphiq_rows=mphiq,
            n_bootstrap=10,
        )

    incomplete_mphiq = _mphiq_rows().drop(index=0)
    with pytest.raises(ValueError, match="exactly 16 unique Hamming-one edges"):
        analyze_first_paper_estimands(
            crossed,
            confirmatory_metrics=["kappa"],
            mphiq_rows=incomplete_mphiq,
            n_bootstrap=10,
        )

    duplicate_mphiq = _mphiq_rows()
    first = duplicate_mphiq.iloc[0]
    duplicate_mphiq.loc[1, ["code_same", "code_different"]] = [
        first["code_same"],
        first["code_different"],
    ]
    with pytest.raises(ValueError, match="repeats cube edge"):
        analyze_first_paper_estimands(
            crossed,
            confirmatory_metrics=["kappa"],
            mphiq_rows=duplicate_mphiq,
            n_bootstrap=10,
        )
