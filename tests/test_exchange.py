import json

import pandas as pd
import pytest

from flock.core.types import Order
from flock.experiments.ledger import Ledger
from flock.experiments.runner import log_exchange_events
from flock.logging_.decisions import RunWriter
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
    assert m.order_lifetime == "step"
    m.submit("a", (Order("X", "sell", 3, limit_price=100.0),))
    m.submit("b", (Order("X", "buy", 10),))  # market order
    fills = m.step()
    b_fills = [f for f in fills if f.agent_id == "b"]
    assert sum(f.quantity for f in b_fills) == 3
    # remainder expired; next step nothing rests
    assert m.step() == []


def test_unsupported_order_lifetime_is_rejected():
    with pytest.raises(ValueError, match="only 'step' is supported"):
        _market(order_lifetime="good_til_cancelled")


def test_self_cross_does_not_fill_and_book_is_auditable():
    m = _market()
    m.submit("same", (Order("X", "sell", 2, limit_price=99.0),))
    m.submit("same", (Order("X", "buy", 2, limit_price=101.0),))

    assert m.step() == []
    assert m.last_step_trades == ()
    assert {
        (order.side, order.agent_id, order.price, order.quantity)
        for side in ("buy", "sell")
        for order in m.last_book_snapshot["X"][side]
    } == {
        ("buy", "same", 101.0, 2),
        ("sell", "same", 99.0, 2),
    }


def test_matcher_searches_past_own_resting_order():
    m = _market(seed=1)
    # Seed 1 preserves this three-order submission order at step zero. The
    # incoming buy must skip its own better-priced ask and trade externally.
    m.submit("same", (Order("X", "sell", 1, limit_price=99.0),))
    m.submit("other", (Order("X", "sell", 1, limit_price=100.0),))
    m.submit("same", (Order("X", "buy", 1, limit_price=101.0),))

    fills = m.step()

    assert {fill.agent_id for fill in fills} == {"same", "other"}
    assert all(fill.price == 100.0 for fill in fills)
    assert m.last_step_trades[0].buyer_id == "same"
    assert m.last_step_trades[0].seller_id == "other"
    assert m.last_book_snapshot["X"]["sell"][0].agent_id == "same"


def test_partial_fill_conserves_shares_and_cash_net_of_fees():
    m = _market(fee_bps=100.0)
    buyer = Ledger(initial_cash=1000.0, max_position_per_symbol=20.0, fee_bps=100.0)
    seller = Ledger(initial_cash=0.0, max_position_per_symbol=20.0, fee_bps=100.0)
    seller.qty["X"] = 10.0
    seller.avg_price["X"] = 80.0
    ledgers = {"buyer": buyer, "seller": seller}

    m.submit("seller", (Order("X", "sell", 10, limit_price=100.0),))
    m.submit("buyer", (Order("X", "buy", 6, limit_price=100.0),))
    fills = m.step()
    for fill in fills:
        ledgers[fill.agent_id].apply(fill)

    assert buyer.qty["X"] + seller.qty["X"] == pytest.approx(10.0)
    assert buyer.cash + seller.cash == pytest.approx(1000.0 - sum(f.fee for f in fills))
    assert m.last_book_snapshot["X"]["sell"][0].quantity == pytest.approx(4.0)
    assert len(m.trade_tape) == 1
    trade = m.trade_tape[0]
    assert (trade.buyer_id, trade.seller_id, trade.quantity) == ("buyer", "seller", 6)
    assert trade.fee_per_side == pytest.approx(6.0)


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
    assert len(m.last_step_bars) == 1
    assert m.last_step_bars[0].close == 99.0


def test_exchange_events_export_tape_book_expiry_and_endogenous_bars(tmp_path):
    m = _market()
    m.submit("seller", (Order("X", "sell", 7, limit_price=100.0),))
    m.submit("buyer", (Order("X", "buy", 5, limit_price=100.0),))
    m.step()
    writer = RunWriter("exchange-events", tmp_path)

    log_exchange_events(writer, m)
    writer.fail(RuntimeError("test terminal close"))

    events = [
        json.loads(line)
        for line in (writer.work_dir / "market_events.jsonl").read_text().splitlines()
    ]
    event_types = {event["event_type"] for event in events}
    assert event_types == {
        "trade",
        "resting_order_snapshot",
        "expiry",
        "endogenous_bar",
    }
    trade = next(event for event in events if event["event_type"] == "trade")
    assert (trade["buyer_id"], trade["seller_id"], trade["quantity"]) == (
        "buyer",
        "seller",
        5,
    )
