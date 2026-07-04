import pandas as pd

from flock.core.types import Order
from flock.markets.exchange import ExchangeMarket


def _seed_bars(n: int = 12, price: float = 100.0) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"ts": f"2030-01-{i + 1:02d}", "symbol": "X", "open": price, "high": price,
             "low": price, "close": price, "volume": 100}
            for i in range(n)
        ]
    )


def _market(**kw) -> ExchangeMarket:
    defaults = dict(observation_window=5, fee_bps=0.0, tick_size=0.01, seed=1)
    defaults.update(kw)
    return ExchangeMarket(_seed_bars(), None, **defaults)


def test_crossing_limits_trade_at_resting_price():
    m = _market()
    m.submit("a", (Order("X", "sell", 10, limit_price=99.0),))
    m.submit("b", (Order("X", "buy", 10, limit_price=101.0),))
    fills = m.step()
    assert len(fills) == 2  # both sides recorded
    assert all(f.quantity == 10 for f in fills)
    # fill at the resting order's price (whichever arrived first in shuffle)
    assert fills[0].price in (99.0, 101.0)
    buyer = next(f for f in fills if f.side == "buy")
    seller = next(f for f in fills if f.side == "sell")
    assert buyer.agent_id == "b" and seller.agent_id == "a"


def test_non_crossing_orders_do_not_trade():
    m = _market()
    m.submit("a", (Order("X", "sell", 10, limit_price=105.0),))
    m.submit("b", (Order("X", "buy", 10, limit_price=95.0),))
    assert m.step() == []
    state = m.state()
    assert state.prices["X"] == 100.0  # carry-forward close


def test_partial_fill_and_price_impact():
    m = _market()
    m.submit("mm", (Order("X", "sell", 5, limit_price=100.5),))
    m.submit("mm", (Order("X", "sell", 5, limit_price=101.5),))
    m.submit("agg", (Order("X", "buy", 8, limit_price=102.0),))
    fills = m.step()
    agg_fills = [f for f in fills if f.agent_id == "agg"]
    assert sum(f.quantity for f in agg_fills) == 8
    assert {f.price for f in agg_fills} == {100.5, 101.5}  # walked the book
    assert m.state().prices["X"] == 101.5  # buying pressure moved the close up


def test_market_order_unfilled_remainder_expires():
    m = _market()
    m.submit("a", (Order("X", "sell", 3, limit_price=100.0),))
    m.submit("b", (Order("X", "buy", 10),))  # market order
    fills = m.step()
    b_fills = [f for f in fills if f.agent_id == "b"]
    assert sum(f.quantity for f in b_fills) == 3
    # remainder expired; next step nothing rests
    assert m.step() == []


def test_deterministic_given_seed():
    def run(seed):
        m = _market(seed=seed)
        m.submit("a", (Order("X", "sell", 5, limit_price=100.0),))
        m.submit("b", (Order("X", "buy", 5, limit_price=100.0),))
        m.submit("c", (Order("X", "buy", 5, limit_price=100.0),))
        return [(f.agent_id, f.quantity, f.price) for f in m.step()]

    assert run(7) == run(7)


def test_endogenous_history_grows():
    m = _market()
    m.submit("a", (Order("X", "sell", 5, limit_price=99.0),))
    m.submit("b", (Order("X", "buy", 5, limit_price=99.0),))
    m.step()
    state = m.state()
    assert state.step == 1
    assert state.prices["X"] == 99.0  # last trade became the close
