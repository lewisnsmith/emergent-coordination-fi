import pandas as pd
import pytest

from flock.core.types import Fill, Order
from flock.experiments.ledger import Ledger
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


def _symbol_bars(symbol: str, days: range) -> list[dict]:
    multiplier = 1 if symbol == "X" else 10
    return [
        {
            "ts": f"2030-01-{day:02d}",
            "symbol": symbol,
            "open": day * multiplier,
            "high": day * multiplier + 1,
            "low": day * multiplier - 1,
            "close": day * multiplier,
            "volume": 1000,
        }
        for day in days
    ]


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


def test_replay_market_buy_preserves_reserved_notional_across_upward_gap():
    bars = _tiny_bars()
    bars.loc[3, ["open", "high", "low", "close"]] = [200.0, 201.0, 199.0, 200.0]
    m = ReplayMarket(bars, observation_window=2, fee_bps=0.0, slippage_bps=0.0)
    ledger = Ledger(initial_cash=1000.0, max_position_per_symbol=100.0, fee_bps=0.0)
    order = ledger.clip_orders((Order("X", "buy", 100),), m.state().prices)

    m.submit("agent", order)
    fill = m.step()[0]
    ledger.apply(fill)

    assert fill.price == 200.0
    assert fill.quantity < order[0].quantity
    assert fill.price * fill.quantity == pytest.approx(103.0 * order[0].quantity)
    assert ledger.cash >= 0.0


def test_replay_aligns_staggered_symbol_histories_on_exact_intersection():
    bars = pd.DataFrame(
        _symbol_bars("X", range(1, 8)) + _symbol_bars("Y", range(2, 9))
    )
    m = ReplayMarket(bars, observation_window=2, fee_bps=0.0, slippage_bps=0.0)

    state = m.state()

    assert m.timestamps == [f"2030-01-{day:02d}" for day in range(2, 8)]
    assert state.ts == "2030-01-04"
    assert tuple(bar.ts for bar in state.bars["X"]) == ("2030-01-03", "2030-01-04")
    assert tuple(bar.ts for bar in state.bars["Y"]) == ("2030-01-03", "2030-01-04")
    m.submit("agent", (Order("X", "buy", 1), Order("Y", "buy", 1)))
    assert {fill.ts for fill in m.step()} == {"2030-01-05"}


def test_replay_rejects_insufficient_common_history():
    bars = pd.DataFrame(
        _symbol_bars("X", range(1, 6)) + _symbol_bars("Y", range(3, 6))
    )

    with pytest.raises(
        ValueError,
        match=r"observation_window \+ 2 \(4\).*found 3",
    ):
        ReplayMarket(bars, observation_window=2)


def test_replay_rejects_duplicate_symbol_timestamp():
    bars = _tiny_bars()
    bars = pd.concat([bars, bars.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match=r"duplicate \(symbol, ts\)"):
        ReplayMarket(bars, observation_window=2)


def test_replay_exposes_prediction_question_expiry_and_rules():
    context = {
        "X": {
            "question": "Will X occur?",
            "close_ts": "2030-01-06T00:00:00Z",
            "rules": "Resolves Yes if X occurs.",
            "price_semantics": "YES probability in [0,1]",
        }
    }
    market = ReplayMarket(
        _tiny_bars(), observation_window=2, instrument_context=context
    )
    assert market.state().instrument_context == context


def test_simultaneous_orders_cannot_create_capacity_for_each_other():
    empty = Ledger(initial_cash=1000.0, max_position_per_symbol=10.0, fee_bps=0.0)
    clipped = empty.clip_orders(
        (Order("X", "buy", 5), Order("X", "sell", 5)),
        {"X": 100.0},
    )
    assert [(order.side, order.quantity) for order in clipped] == [("buy", 5)]

    capped = Ledger(initial_cash=1000.0, max_position_per_symbol=10.0, fee_bps=0.0)
    capped.qty["X"] = 10.0
    clipped = capped.clip_orders(
        (Order("X", "sell", 5), Order("X", "buy", 5)),
        {"X": 100.0},
    )
    assert [(order.side, order.quantity) for order in clipped] == [("sell", 5)]

    cashless = Ledger(initial_cash=0.0, max_position_per_symbol=20.0, fee_bps=0.0)
    cashless.qty["X"] = 10.0
    clipped = cashless.clip_orders(
        (Order("X", "sell", 5), Order("X", "buy", 5)),
        {"X": 100.0},
    )
    assert [(order.side, order.quantity) for order in clipped] == [("sell", 5)]


def test_ledger_apply_rejects_invariant_violations_before_mutation():
    insufficient_cash = Ledger(50.0, 10.0, 0.0)
    short_sale = Ledger(1000.0, 10.0, 0.0)
    short_sale.qty["X"] = 1.0
    short_sale.avg_price["X"] = 90.0
    over_cap = Ledger(1000.0, 10.0, 0.0)
    over_cap.qty["X"] = 9.0
    over_cap.avg_price["X"] = 90.0
    cases = (
        (
            insufficient_cash,
            Fill("a", 0, "2030-01-01", "X", "buy", 1, 100.0, 0.0),
            "cash negative",
        ),
        (
            short_sale,
            Fill("a", 0, "2030-01-01", "X", "sell", 2, 100.0, 0.0),
            "short position",
        ),
        (
            over_cap,
            Fill("a", 0, "2030-01-01", "X", "buy", 2, 100.0, 0.0),
            "position cap",
        ),
    )

    for ledger, fill, message in cases:
        before = (ledger.cash, dict(ledger.qty), dict(ledger.avg_price))
        with pytest.raises(ValueError, match=message):
            ledger.apply(fill)
        assert (ledger.cash, ledger.qty, ledger.avg_price) == before
