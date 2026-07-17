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


def _binary_bars(symbol: str, days: range, resolution: float) -> list[dict]:
    rows = []
    day_values = list(days)
    for offset, day in enumerate(day_values):
        close = 0.35 + offset * 0.02
        rows.append(
            {
                "ts": f"2030-01-{day:02d}",
                "symbol": symbol,
                "open": close,
                "high": min(close + 0.03, 1.0),
                "low": max(close - 0.03, 0.0),
                "close": close,
                "volume": 1000,
            }
        )
    rows[-1]["close"] = resolution
    rows[-1]["high"] = max(rows[-1]["high"], resolution)
    rows[-1]["low"] = min(rows[-1]["low"], resolution)
    return rows


def _binary_context(
    symbol: str, open_day: int, close_day: int, resolution: float
) -> dict:
    return {
        "symbol": symbol,
        "question": f"Will {symbol} occur?",
        "rules": f"Resolves Yes if {symbol} occurs.",
        "open_ts": f"2030-01-{open_day:02d}T00:00:00Z",
        "close_ts": f"2030-01-{close_day:02d}T00:00:00Z",
        "resolution": resolution,
        "yes_label": "Yes",
        "no_label": "No",
        "price_semantics": "YES probability in [0,1]",
        "result": "yes" if resolution else "no",
    }


def _asynchronous_binary_market(*, max_steps: int | None = None) -> ReplayMarket:
    bars = pd.DataFrame(
        _binary_bars("X", range(1, 7), 1.0)
        + _binary_bars("Y", range(3, 10), 0.0)
    )
    contexts = {
        "X": _binary_context("X", 1, 6, 1.0),
        "Y": _binary_context("Y", 3, 9, 0.0),
    }
    return ReplayMarket(
        bars,
        observation_window=1,
        fee_bps=0.0,
        slippage_bps=0.0,
        max_steps=max_steps,
        instrument_context=contexts,
    )


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


def test_binary_replay_uses_union_timeline_and_contract_lifetimes():
    market = _asynchronous_binary_market()

    assert market.timestamps == [f"2030-01-{day:02d}" for day in range(2, 9)]
    assert market.state().symbols == ("X",)
    assert set(market.state().prices) == set(market.state().symbols)
    market.step()
    # Y has a price row on its listing date but lacks sufficient visible history.
    assert market.state().ts == "2030-01-03"
    assert market.state().symbols == ("X",)
    assert set(market.state().prices) == {"X"}
    market.step()
    assert market.state().ts == "2030-01-04"
    assert market.state().symbols == ("X", "Y")


def test_binary_replay_preserves_contract_definition_without_outcome_leakage():
    market = _asynchronous_binary_market()
    context = market.state().instrument_context["X"]

    assert context["question"] == "Will X occur?"
    assert context["rules"] == "Resolves Yes if X occurs."
    assert context["close_ts"] == "2030-01-06T00:00:00Z"
    assert context["tradable_side"] == "YES"
    assert "direct NO shares are not traded" in context["no_payout"]
    assert "resolution" not in context
    assert "result" not in context
    assert all(bar.close != 1.0 for bar in market.state().bars["X"])


def test_binary_replay_rejects_bar_before_intraday_listing():
    context = _binary_context("X", 1, 6, 1.0)
    context["open_ts"] = "2030-01-01T12:00:00Z"

    with pytest.raises(ValueError, match="outside the contract lifetime"):
        ReplayMarket(
            pd.DataFrame(_binary_bars("X", range(1, 7), 1.0)),
            observation_window=1,
            instrument_context={"X": context},
        )


def test_binary_replay_settles_yes_holdings_and_rejects_matured_orders():
    market = _asynchronous_binary_market()
    market.register_position("agent", "X", 2.0)
    while market.state().ts != "2030-01-05":
        assert market.step() == []

    # The order expires at maturity; the terminal outcome bar is not tradable.
    market.submit("agent", (Order("X", "buy", 1.0),))
    fills = market.step()
    assert [(fill.side, fill.quantity, fill.price) for fill in fills] == [
        ("sell", 2.0, 1.0)
    ]
    assert market.state().symbols == ("Y",)
    with pytest.raises(ValueError, match="inactive binary contract X"):
        market.submit("agent", (Order("X", "buy", 1.0),))


def test_binary_replay_zero_payout_removes_yes_position():
    market = _asynchronous_binary_market()
    while market.state().ts != "2030-01-04":
        market.step()
    market.submit("agent", (Order("Y", "buy", 3.0),))
    purchase = market.step()
    assert len(purchase) == 1 and purchase[0].side == "buy"

    terminal_fills = []
    while not market.done:
        terminal_fills.extend(market.step())
    assert any(
        fill.symbol == "Y"
        and fill.side == "sell"
        and fill.quantity == purchase[0].quantity
        and fill.price == 0.0
        for fill in terminal_fills
    )


def test_truncated_binary_replay_does_not_reveal_future_settlement():
    market = _asynchronous_binary_market(max_steps=4)
    market.register_position("agent", "X", 2.0)

    while market.state().ts != "2030-01-05":
        assert market.step() == []
    market.submit("agent", (Order("X", "buy", 1.0),))
    # The next unselected timestamp is the close, but truncation freezes the
    # selected horizon: neither the order nor the known payout may enter.
    assert market.step() == []
    assert market.done


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
