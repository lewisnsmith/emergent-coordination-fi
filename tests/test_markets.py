import pandas as pd
import pytest

from flock.core.types import Order
from flock.markets.replay import ReplayMarket


def _tiny_bars() -> pd.DataFrame:
    rows = []
    closes = [100, 101, 103, 102, 105, 104]
    for i, c in enumerate(closes):
        rows.append(
            {
                "ts": f"2030-01-{i + 1:02d}",
                "symbol": "X",
                "open": c - 0.5,
                "high": c + 1,
                "low": c - 1.5,
                "close": c,
                "volume": 1000,
            }
        )
    return pd.DataFrame(rows)


def test_replay_market_fill_at_next_open_with_slippage():
    m = ReplayMarket(_tiny_bars(), observation_window=2, fee_bps=0.0, slippage_bps=10.0)
    state = m.state()
    assert state.prices["X"] == 103  # window=2 -> first decision bar is index 2
    m.submit("a1", (Order("X", "buy", 10),))
    fills = m.step()
    assert len(fills) == 1
    next_open = 102 - 0.5
    assert fills[0].price == pytest.approx(next_open * (1 + 10 / 1e4))


def test_replay_limit_order_fills_only_when_crossed():
    m = ReplayMarket(_tiny_bars(), observation_window=2, fee_bps=0.0, slippage_bps=0.0)
    # Next bar (index 3): open 101.5, high 103, low 100.5.
    m.submit("a1", (Order("X", "buy", 1, limit_price=99.0),))  # below low -> no fill
    assert m.step() == []
    # Next bar (index 4): open 104.5, high 106, low 103.5.
    m.submit("a1", (Order("X", "sell", 1, limit_price=105.0),))  # high 106 crosses
    fills = m.step()
    assert len(fills) == 1
    assert fills[0].price == 105.0


def test_replay_identical_states_across_observers(replay_market):
    s1 = replay_market.state()
    s2 = replay_market.state()
    assert s1.prices == s2.prices
    assert s1.ts == s2.ts


def test_replay_terminates(replay_market):
    n = 0
    while not replay_market.done:
        replay_market.step()
        n += 1
    assert n == replay_market.n_steps
