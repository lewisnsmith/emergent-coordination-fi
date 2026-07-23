"""Coordination metrics on synthetic fixtures with known herding levels."""

import numpy as np
import pandas as pd

from flock.analysis.coordination import (
    activity_match_report,
    buy_sell_counts,
    detect_cascades,
    harmonize_13f_holdings_changes,
    holdings_change_counts,
    lsv_cell_statistics,
    lsv_herding,
    net_flow_series,
    overlap_13f,
    sias_decomposition,
    sias_decomposition_from_panel,
    sias_herding,
)


def _decisions(orders_by_agent_step) -> pd.DataFrame:
    rows = []
    for (agent, step), orders in orders_by_agent_step.items():
        rows.append(
            {"agent_id": agent, "cohort": "c", "step": step, "ts": f"t{step}",
             "action": "buy", "parse_ok": True, "orders_clipped": orders}
        )
    return pd.DataFrame(rows)


def _herded(n_agents=8, n_steps=30, seed=0):
    """All agents trade the same direction each (step, symbol)."""
    rng = np.random.default_rng(seed)
    data = {}
    for step in range(n_steps):
        side = "buy" if rng.random() < 0.5 else "sell"
        opposite = "sell" if side == "buy" else "buy"
        for i in range(n_agents):
            data[(f"a{i}", step)] = [
                {"symbol": "X", "side": side, "quantity": 10.0},
                {"symbol": "Y", "side": opposite, "quantity": 10.0},
            ]
    return _decisions(data)


def _independent(n_agents=8, n_steps=200, seed=0):
    rng = np.random.default_rng(seed)
    data = {}
    for step in range(n_steps):
        for i in range(n_agents):
            data[(f"a{i}", step)] = [
                {
                    "symbol": symbol,
                    "side": "buy" if rng.random() < 0.5 else "sell",
                    "quantity": 10.0,
                }
                for symbol in ("X", "Y")
            ]
    return _decisions(data)


def test_lsv_high_for_herded_cohort():
    agents = [f"a{i}" for i in range(8)]
    herded = lsv_herding(buy_sell_counts(_herded(), agents))
    independent = lsv_herding(buy_sell_counts(_independent(), agents))
    assert herded > 0.2
    assert independent < 0.05
    assert herded > independent


def test_lsv_uses_contemporaneous_expected_buy_fraction():
    counts = pd.DataFrame(
        [
            {"step": 0, "symbol": "A", "buy": 8, "sell": 2},
            {"step": 0, "symbol": "B", "buy": 6, "sell": 4},
            {"step": 1, "symbol": "A", "buy": 2, "sell": 8},
            {"step": 1, "symbol": "B", "buy": 4, "sell": 6},
        ]
    )
    cells = lsv_cell_statistics(counts)
    assert cells.loc[cells["step"] == 0, "expected_buy_fraction"].eq(0.7).all()
    assert cells.loc[cells["step"] == 1, "expected_buy_fraction"].eq(0.3).all()
    assert lsv_herding(counts) == np.mean(cells["h"])


def test_sias_detects_serial_herding():
    # buyers fraction persists across steps by construction: two symbols with
    # persistent opposite-direction flows
    rows = {}
    for step in range(40):
        for i in range(6):
            rows[(f"a{i}", step)] = [
                {"symbol": "X", "side": "buy" if i < 5 else "sell", "quantity": 1.0},
                {"symbol": "Y", "side": "sell" if i < 5 else "buy", "quantity": 1.0},
                {"symbol": "Z", "side": "buy" if (i + step) % 2 else "sell", "quantity": 1.0},
            ]
    sias = sias_herding(buy_sell_counts(_decisions(rows), [f"a{i}" for i in range(6)]))
    assert sias > 0.3


def test_sias_decomposition_reconciles_to_full_correlation():
    rows = {}
    patterns = {
        "X": [1, 1, 1, 0],
        "Y": [1, 0, 0, 0],
        "Z": [1, 1, 0, 0],
    }
    for step in range(3):
        for agent in range(4):
            rows[(f"a{agent}", step)] = [
                {
                    "symbol": symbol,
                    "side": "buy" if pattern[agent] else "sell",
                    "quantity": 1.0,
                }
                for symbol, pattern in patterns.items()
            ]
    decisions = _decisions(rows)
    result = sias_decomposition(decisions, [f"a{i}" for i in range(4)])
    assert result.period_pairs == 2
    np.testing.assert_allclose(
        result.full, result.following_own + result.following_others, atol=1e-12
    )
    np.testing.assert_allclose(result.full, 1.0, atol=1e-12)


def test_cascade_detection_flags_sustained_one_sided_flow():
    quiet = list(np.random.default_rng(0).normal(0, 1, 40))
    surge = [25.0] * 6
    flow = pd.Series(quiet + surge + quiet)
    result = detect_cascades(flow, n_permutations=200, min_length=3, seed=1)
    assert result["n_cascades"] >= 1
    assert result["max_length"] >= 5


def test_cascade_absent_in_noise():
    flow = pd.Series(np.random.default_rng(3).normal(0, 1, 100))
    result = detect_cascades(flow, n_permutations=200, min_length=4, seed=1)
    assert result["n_cascades"] == 0


def test_net_flow_series_signs():
    d = _decisions(
        {
            ("a0", 0): [{"symbol": "X", "side": "buy", "quantity": 5.0}],
            ("a1", 0): [{"symbol": "X", "side": "buy", "quantity": 5.0}],
            ("a0", 1): [{"symbol": "X", "side": "sell", "quantity": 5.0}],
            ("a1", 1): [],
        }
    )
    flow = net_flow_series(d, ["a0", "a1"])
    assert flow.loc[0] == 10.0 and flow.loc[1] == -5.0
    counts = buy_sell_counts(d, ["a0", "a1"])
    assert counts["decision_basis"].eq("intended_clipped_order").all()
    assert counts["execution_status"].eq("intended_not_executed").all()


def _holding(
    manager: str,
    period: str,
    cusip: str,
    shares: float | None,
    *,
    shares_type: str = "SH",
    put_call: str = "",
) -> dict:
    accession = f"{manager}-{period}"
    return {
        "manager": manager,
        "period": period,
        "cusip": cusip,
        "shares": shares,
        "shares_type": shares_type,
        "put_call": put_call,
        "value_usd": 1_000.0,
        "accession": accession,
        "filing_date": str(pd.Timestamp(period) + pd.Timedelta(days=45))[:10],
        "acceptance_datetime": f"{period}T17:00:00Z",
        "source_url": f"https://example.test/{accession}.xml",
    }


def test_13f_harmonization_uses_share_changes_and_reports_unmatched_units():
    panel = pd.DataFrame(
        [
            _holding("m1", "2024-03-31", "AAA", 100),
            _holding("m1", "2024-03-31", "BBB", 50),
            _holding("m1", "2024-06-30", "AAA", 150),
            _holding("m2", "2024-06-30", "AAA", 100),
            _holding("m3", "2024-03-31", "AAA", 100),
            _holding("m3", "2024-09-30", "AAA", 125),
            _holding("m4", "2024-03-31", "OPT", 10, put_call="CALL"),
            _holding("m4", "2024-06-30", "OPT", 12, put_call="CALL"),
            _holding("m5", "2024-03-31", "MISS", None),
        ]
    )
    harmonized = harmonize_13f_holdings_changes(panel)

    m1 = harmonized.activity[harmonized.activity["manager"] == "m1"]
    assert set(zip(m1["symbol"], m1["delta_shares"], strict=True)) == {
        ("AAA", 50.0),
        ("BBB", -50.0),
    }
    assert m1["prior_accession"].eq("m1-2024-03-31").all()
    assert m1["accession"].eq("m1-2024-06-30").all()
    assert m1["decision_basis"].eq("realized_holdings_change").all()
    assert m1["execution_status"].eq("realized_position_not_order_level").all()
    assert harmonized.period_coverage.iloc[0]["eligible_managers"] == ["m1"]

    reasons = set(harmonized.unmatched["reason"])
    assert {
        "missing_prior_period",
        "nonconsecutive_prior_period",
        "unsupported_position_type",
        "missing_share_amount",
    } <= reasons


def test_13f_harmonization_does_not_turn_exclusions_into_liquidations():
    panel = pd.DataFrame(
        [
            _holding("m1", "2024-03-31", "AAA", 100),
            _holding("m1", "2024-03-31", "BBB", 50),
            _holding("m1", "2024-06-30", "AAA", None),
            _holding("m1", "2024-06-30", "BBB", 60),
        ]
    )

    harmonized = harmonize_13f_holdings_changes(panel)

    assert not (
        (harmonized.activity["manager"] == "m1")
        & (harmonized.activity["symbol"] == "AAA")
    ).any()
    bbb = harmonized.activity[harmonized.activity["symbol"] == "BBB"]
    assert bbb.iloc[0]["delta_shares"] == 10
    excluded = harmonized.unmatched[
        harmonized.unmatched["reason"] == "comparison_input_excluded"
    ]
    assert set(excluded["symbol"]) == {"AAA"}


def test_13f_output_is_lsv_and_sias_compatible():
    patterns = {
        "AAA": [1, 1, 1, 0],
        "BBB": [1, 0, 0, 0],
        "CCC": [1, 1, 0, 0],
    }
    rows = []
    levels = {(manager, symbol): 100.0 for manager in range(4) for symbol in patterns}
    for period in ("2024-03-31", "2024-06-30", "2024-09-30"):
        if period != "2024-03-31":
            for symbol, pattern in patterns.items():
                for manager, is_buy in enumerate(pattern):
                    levels[(manager, symbol)] += 10.0 if is_buy else -10.0
        for (manager, symbol), shares in levels.items():
            rows.append(_holding(f"m{manager}", period, symbol, shares))

    harmonized = harmonize_13f_holdings_changes(pd.DataFrame(rows))
    counts = holdings_change_counts(harmonized)
    cells = lsv_cell_statistics(counts, min_traders=3)
    assert cells.groupby("step")["expected_buy_fraction"].first().eq(0.5).all()
    assert cells["decision_basis"].eq("realized_holdings_change").all()
    assert counts["n_eligible"].eq(4).all()
    assert counts["activity_rate"].eq(1.0).all()

    sias = sias_decomposition_from_panel(harmonized.activity, min_traders=2)
    assert sias.period_pairs == 1
    np.testing.assert_allclose(sias.full, 1.0, atol=1e-12)
    np.testing.assert_allclose(
        sias.full,
        sias.following_own + sias.following_others,
        atol=1e-12,
    )


def test_activity_match_report_exposes_basis_and_activity_mismatches():
    reference = pd.DataFrame(
        [
            {
                "step": "2024-06-30",
                "symbol": "AAA",
                "buy": 2,
                "sell": 2,
                "n_active": 4,
                "n_eligible": 4,
                "activity_rate": 1.0,
                "decision_basis": "realized_holdings_change",
            },
            {
                "step": "2024-06-30",
                "symbol": "BBB",
                "buy": 1,
                "sell": 1,
                "n_active": 2,
                "n_eligible": 4,
                "activity_rate": 0.5,
                "decision_basis": "realized_holdings_change",
            },
        ]
    )
    intended = reference.iloc[[0]].copy()
    intended["decision_basis"] = "intended_clipped_order"

    strict = activity_match_report(reference, intended, min_traders=3)
    assert set(strict["reason"]) == {
        "decision_basis_mismatch",
        "below_min_traders",
    }
    assert not strict["matched"].any()

    activity_only = activity_match_report(
        reference,
        intended,
        min_traders=3,
        require_same_basis=False,
    )
    assert activity_only.loc[
        activity_only["symbol"] == "AAA", "matched"
    ].all()


def test_13f_overlap_bounds():
    panel = pd.DataFrame(
        [
            {"manager": "m1", "period": "q1", "cusip": "AAA", "value_usd": 50.0},
            {"manager": "m1", "period": "q1", "cusip": "BBB", "value_usd": 50.0},
            {"manager": "m2", "period": "q1", "cusip": "AAA", "value_usd": 50.0},
            {"manager": "m2", "period": "q1", "cusip": "BBB", "value_usd": 50.0},
            {"manager": "m3", "period": "q1", "cusip": "CCC", "value_usd": 100.0},
        ]
    )
    # m1-m2 overlap 1.0; m1-m3 and m2-m3 overlap 0.0
    assert abs(overlap_13f(panel) - (1.0 + 0.0 + 0.0) / 3) < 1e-9
