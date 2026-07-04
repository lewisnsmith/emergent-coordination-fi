"""Coordination metrics on synthetic fixtures with known herding levels."""

import numpy as np
import pandas as pd

from flock.analysis.coordination import (
    buy_sell_counts,
    detect_cascades,
    lsv_herding,
    net_flow_series,
    overlap_13f,
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
        for i in range(n_agents):
            data[(f"a{i}", step)] = [{"symbol": "X", "side": side, "quantity": 10.0}]
    return _decisions(data)


def _independent(n_agents=8, n_steps=200, seed=0):
    rng = np.random.default_rng(seed)
    data = {}
    for step in range(n_steps):
        for i in range(n_agents):
            side = "buy" if rng.random() < 0.5 else "sell"
            data[(f"a{i}", step)] = [{"symbol": "X", "side": side, "quantity": 10.0}]
    return _decisions(data)


def test_lsv_high_for_herded_cohort():
    agents = [f"a{i}" for i in range(8)]
    herded = lsv_herding(buy_sell_counts(_herded(), agents))
    independent = lsv_herding(buy_sell_counts(_independent(), agents))
    assert herded > 0.2
    assert independent < 0.05
    assert herded > independent


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
