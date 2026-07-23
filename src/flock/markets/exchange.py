"""Phase-2 shared exchange: a step-synchronous continuous double auction.

Agents' orders trade against each other, so herding has price impact and
feedback loops can emerge. Mechanics per step:

  1. All agents observe the same state (seeded history + endogenous bars).
  2. Submitted orders arrive in a deterministically shuffled order.
  3. Each arriving limit order matches against resting opposite orders that
     cross (price-time priority, fill at the resting price) and then rests.
     Market orders match what they can and the remainder expires.
  4. All unmatched limit orders expire at step end (the only supported order
     lifetime is ``step``). The book is snapshotted for audit, then cleared,
     and the step's trades are synthesized into a bar (no trades ->
     carry-forward close, zero volume).

Public information is the tape (bar history), not the intra-step book, so
agents coordinate only through prices — the phenomenon under study.

The dataset provides symbols, seeded price history, timestamps, and news;
prices become endogenous from the first step onward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

import numpy as np
import pandas as pd

from flock.core.types import Bar, Fill, NewsEvent, Order, Side
from flock.markets.base import MarketState

ORDER_LIFETIME = "step"


@dataclass(frozen=True)
class RestingOrderSnapshot:
    """One auditable order in the end-of-step book before expiry."""

    symbol: str
    side: Side
    price: float
    quantity: float
    agent_id: str
    arrival: int


@dataclass(frozen=True)
class TradeRecord:
    """Counterparty-linked trade from which both emitted fills can be rebuilt."""

    step: int
    sequence: int
    ts: str
    symbol: str
    price: float
    quantity: float
    buyer_id: str
    seller_id: str
    fee_per_side: float


@dataclass(order=True)
class _Resting:
    sort_key: tuple = field(init=False, repr=False)
    price: float
    arrival: int
    agent_id: str = field(compare=False)
    side: Side = field(compare=False)
    quantity: float = field(compare=False)

    def __post_init__(self):
        # bids: matched best (highest) first -> sort by -price; asks by price
        direction = -1.0 if self.side == "buy" else 1.0
        self.sort_key = (direction * self.price, self.arrival)


class ExchangeMarket:
    def __init__(
        self,
        bars: pd.DataFrame,
        events: pd.DataFrame | None = None,
        observation_window: int = 20,
        fee_bps: float = 5.0,
        tick_size: float = 0.01,
        max_steps: int | None = None,
        seed: int = 0,
        order_lifetime: str = ORDER_LIFETIME,
    ):
        if order_lifetime != ORDER_LIFETIME:
            raise ValueError(
                f"Unsupported order_lifetime {order_lifetime!r}; only 'step' is supported"
            )
        self.fee_bps = fee_bps
        self.tick = tick_size
        self.window = observation_window
        self.seed = seed
        self.order_lifetime = order_lifetime

        bars = bars.sort_values(["ts", "symbol"])
        self.timestamps: list[str] = sorted(bars["ts"].unique().tolist())
        self.symbols: tuple[str, ...] = tuple(sorted(bars["symbol"].unique().tolist()))
        seeded = {
            cast(str, s): [Bar(**row) for row in g.to_dict("records")][: self.window]
            for s, g in bars.groupby("symbol")
        }
        self._history: dict[str, list[Bar]] = seeded

        self._events_by_ts: dict[str, list[NewsEvent]] = {}
        if events is not None and len(events):
            for row in events.to_dict("records"):
                self._events_by_ts.setdefault(row["ts"], []).append(NewsEvent(**row))

        n_available = max(len(self.timestamps) - self.window - 1, 0)
        self.n_steps = min(n_available, max_steps) if max_steps else n_available
        self.reset()

    def reset(self) -> None:
        self._step = 0
        self._pending: list[tuple[str, Order]] = []
        self.last_book_snapshot: dict[
            str, dict[str, tuple[RestingOrderSnapshot, ...]]
        ] = {symbol: {"buy": (), "sell": ()} for symbol in self.symbols}
        self.last_step_trades: tuple[TradeRecord, ...] = ()
        self.last_step_bars: tuple[Bar, ...] = ()
        self.trade_tape: tuple[TradeRecord, ...] = ()

    @property
    def done(self) -> bool:
        return self._step >= self.n_steps

    @property
    def last_completed_step(self) -> int:
        if self._step == 0:
            raise RuntimeError("exchange has not completed a step")
        return self._step - 1

    def _ts(self) -> str:
        return self.timestamps[self.window + self._step]

    def state(self) -> MarketState:
        window_bars = {s: tuple(self._history[s][-self.window :]) for s in self.symbols}
        ts = self._ts()
        return MarketState(
            step=self._step,
            ts=ts,
            symbols=self.symbols,
            bars=window_bars,
            prices={s: window_bars[s][-1].close for s in self.symbols},
            news=tuple(self._events_by_ts.get(ts, ())),
        )

    def submit(self, agent_id: str, orders: tuple[Order, ...]) -> None:
        self._pending.extend((agent_id, o) for o in orders)

    def step(self) -> list[Fill]:
        ts = self._ts()
        rng = np.random.default_rng([self.seed, self._step])
        arrival_order = rng.permutation(len(self._pending))
        fills: list[Fill] = []
        step_trades: list[TradeRecord] = []
        trades: dict[str, list[tuple[float, float]]] = {s: [] for s in self.symbols}
        books: dict[str, dict[str, list[_Resting]]] = {
            s: {"buy": [], "sell": []} for s in self.symbols
        }

        for arrival, idx in enumerate(arrival_order):
            agent_id, order = self._pending[idx]
            book = books[order.symbol]
            remaining = order.quantity
            opposite = book["sell" if order.side == "buy" else "buy"]
            opposite.sort()
            while remaining > 1e-9 and opposite:
                match_index = self._match_index(agent_id, order, opposite)
                if match_index is None:
                    break
                best = opposite[match_index]
                qty = min(remaining, best.quantity)
                price = best.price
                fills.append(self._fill(agent_id, ts, order.symbol, order.side, qty, price))
                fills.append(self._fill(best.agent_id, ts, order.symbol, best.side, qty, price))
                buyer_id = agent_id if order.side == "buy" else best.agent_id
                seller_id = agent_id if order.side == "sell" else best.agent_id
                step_trades.append(
                    TradeRecord(
                        step=self._step,
                        sequence=len(step_trades),
                        ts=ts,
                        symbol=order.symbol,
                        price=price,
                        quantity=qty,
                        buyer_id=buyer_id,
                        seller_id=seller_id,
                        fee_per_side=abs(price * qty) * self.fee_bps / 1e4,
                    )
                )
                trades[order.symbol].append((price, qty))
                remaining -= qty
                best.quantity -= qty
                if best.quantity <= 1e-9:
                    opposite.pop(match_index)
            if remaining > 1e-9 and order.limit_price is not None:
                book[order.side].append(
                    _Resting(
                        price=self._snap(order.limit_price), arrival=arrival,
                        agent_id=agent_id, side=order.side, quantity=remaining,
                    )
                )

        self.last_book_snapshot = self._snapshot_books(books)
        self.last_step_trades = tuple(step_trades)
        self.trade_tape += self.last_step_trades
        self.last_step_bars = self._append_bars(ts, trades)
        self._pending = []
        self._step += 1
        return fills

    @classmethod
    def _match_index(
        cls, agent_id: str, incoming: Order, opposite: list[_Resting]
    ) -> int | None:
        """Find the best crossing counterparty while skipping the agent's own orders."""
        for index, resting in enumerate(opposite):
            if incoming.limit_price is not None and not cls._crosses(incoming, resting):
                return None
            if resting.agent_id != agent_id:
                return index
        return None

    @staticmethod
    def _snapshot_books(
        books: dict[str, dict[str, list[_Resting]]],
    ) -> dict[str, dict[str, tuple[RestingOrderSnapshot, ...]]]:
        snapshot: dict[str, dict[str, tuple[RestingOrderSnapshot, ...]]] = {}
        for symbol, book in books.items():
            snapshot[symbol] = {}
            for side in ("buy", "sell"):
                orders = sorted(book[side])
                snapshot[symbol][side] = tuple(
                    RestingOrderSnapshot(
                        symbol=symbol,
                        side=side,
                        price=order.price,
                        quantity=order.quantity,
                        agent_id=order.agent_id,
                        arrival=order.arrival,
                    )
                    for order in orders
                )
        return snapshot

    @staticmethod
    def _crosses(incoming: Order, resting: _Resting) -> bool:
        limit_price = incoming.limit_price
        if limit_price is None:
            return True
        if incoming.side == "buy":
            return resting.price <= limit_price
        return resting.price >= limit_price

    def _snap(self, price: float) -> float:
        return round(round(price / self.tick) * self.tick, 10)

    def _fill(
        self, agent_id: str, ts: str, symbol: str, side: Side, qty: float, price: float
    ) -> Fill:
        fee = abs(price * qty) * self.fee_bps / 1e4
        return Fill(agent_id, self._step, ts, symbol, side, qty, price, fee)

    def _append_bars(
        self, ts: str, trades: dict[str, list[tuple[float, float]]]
    ) -> tuple[Bar, ...]:
        appended: list[Bar] = []
        for s in self.symbols:
            prev_close = self._history[s][-1].close
            t = trades[s]
            if t:
                prices = [p for p, _ in t]
                volume = sum(q for _, q in t)
                bar = Bar(
                    ts, s,
                    open=prices[0], high=max(prices), low=min(prices),
                    close=prices[-1], volume=volume,
                )
            else:
                bar = Bar(ts, s, prev_close, prev_close, prev_close, prev_close, 0.0)
            self._history[s].append(bar)
            appended.append(bar)
        return tuple(appended)


def cascade_ready_history(market: ExchangeMarket) -> pd.DataFrame:
    """Endogenous bar history as a DataFrame (for coordination analysis)."""
    rows = [
        {"ts": b.ts, "symbol": s, "open": b.open, "high": b.high,
         "low": b.low, "close": b.close, "volume": b.volume}
        for s in market.symbols
        for b in market._history[s]
    ]
    return pd.DataFrame(rows)
