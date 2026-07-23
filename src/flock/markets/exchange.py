"""Phase-2 shared exchange: a step-synchronous price-time-priority market.

Agents' orders trade against each other, so herding has price impact and
feedback loops can emerge. Mechanics per step:

  1. All agents observe the same state (seeded history + endogenous bars).
  2. Submitted orders arrive in a deterministically shuffled order.
  3. Each arriving limit order matches against resting opposite orders that
     cross (price-time priority, fill at the resting price) and then rests.
     Market orders match what they can and the remainder expires.
  4. Unmatched limits either expire at step end or persist until cancellation
     or session end, according to ``order_lifetime``. Every lifecycle event and
     complete book snapshot is retained for reconstruction.
  5. The step's trades are synthesized into a bar (no trades -> carry-forward
     close, zero volume).

Public information is the tape (bar history), not the intra-step book. Agents
receive no intra-step cross-agent signal.

The dataset provides symbols, seeded price history, timestamps, and news;
prices become endogenous from the first step onward.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import cast

import numpy as np
import pandas as pd

from flock.core.types import Bar, Fill, NewsEvent, Order, Side
from flock.markets.base import MarketState

ORDER_LIFETIME = "step"
ORDER_LIFETIMES = frozenset({ORDER_LIFETIME, "good_til_cancelled"})


@dataclass(frozen=True)
class RestingOrderSnapshot:
    """One auditable order in the end-of-step book."""

    order_id: str
    symbol: str
    side: Side
    price: float
    quantity: float
    agent_id: str
    arrival: int
    created_step: int


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
    buyer_order_id: str
    seller_order_id: str
    fee_per_side: float


@dataclass(order=True)
class _Resting:
    sort_key: tuple = field(init=False, repr=False)
    price: float
    arrival: int
    order_id: str = field(compare=False)
    agent_id: str = field(compare=False)
    side: Side = field(compare=False)
    quantity: float = field(compare=False)
    created_step: int = field(compare=False)

    def __post_init__(self):
        # bids: matched best (highest) first -> sort by -price; asks by price
        direction = -1.0 if self.side == "buy" else 1.0
        self.sort_key = (direction * self.price, self.arrival)


@dataclass(frozen=True)
class _Pending:
    order_id: str
    agent_id: str
    order: Order


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
        if order_lifetime not in ORDER_LIFETIMES:
            raise ValueError(
                f"Unsupported order_lifetime {order_lifetime!r}; "
                f"expected one of {sorted(ORDER_LIFETIMES)}"
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
        self._pending: list[_Pending] = []
        self._books: dict[str, dict[str, list[_Resting]]] = {
            symbol: {"buy": [], "sell": []} for symbol in self.symbols
        }
        self._submission_sequence = 0
        self._arrival_sequence = 0
        self._queued_order_events: list[dict] = []
        self.last_book_snapshot: dict[
            str, dict[str, tuple[RestingOrderSnapshot, ...]]
        ] = {symbol: {"buy": (), "sell": ()} for symbol in self.symbols}
        self.last_step_events: tuple[dict, ...] = ()
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
        for order in orders:
            order_id = f"o-{self._submission_sequence:012d}"
            self._submission_sequence += 1
            self._pending.append(_Pending(order_id, agent_id, order))

    def open_orders(self, agent_id: str) -> tuple[Order, ...]:
        """Return an agent's live limits for cross-step reservation accounting."""
        return tuple(
            Order(symbol, resting.side, resting.quantity, resting.price)
            for symbol in self.symbols
            for side in ("buy", "sell")
            for resting in self._books[symbol][side]
            if resting.agent_id == agent_id
        )

    def cancel(self, agent_id: str, order_id: str) -> bool:
        """Cancel one live order owned by ``agent_id`` and queue an audit event."""
        for symbol in self.symbols:
            for side in ("buy", "sell"):
                orders = self._books[symbol][side]
                for index, resting in enumerate(orders):
                    if resting.order_id != order_id:
                        continue
                    if resting.agent_id != agent_id:
                        return False
                    orders.pop(index)
                    self._queued_order_events.append(
                        {
                            "event_type": "order_cancelled",
                            "step": self._step,
                            "ts": self._ts(),
                            "order_id": resting.order_id,
                            "agent_id": resting.agent_id,
                            "symbol": symbol,
                            "side": side,
                            "price": resting.price,
                            "quantity": resting.quantity,
                            "reason": "agent_cancel",
                        }
                    )
                    return True
        return False

    def step(self) -> list[Fill]:
        ts = self._ts()
        rng = np.random.default_rng([self.seed, self._step])
        arrival_order = rng.permutation(len(self._pending))
        fills: list[Fill] = []
        step_trades: list[TradeRecord] = []
        step_events: list[dict] = []
        trades: dict[str, list[tuple[float, float]]] = {s: [] for s in self.symbols}

        def emit(event: dict) -> None:
            step_events.append({"event_sequence": len(step_events), **event})

        for event in self._queued_order_events:
            emit(event)
        self._queued_order_events = []

        for idx in arrival_order:
            pending = self._pending[idx]
            agent_id = pending.agent_id
            submitted = pending.order
            order = Order(
                submitted.symbol,
                submitted.side,
                submitted.quantity,
                (
                    self._snap(submitted.limit_price)
                    if submitted.limit_price is not None
                    else None
                ),
            )
            arrival = self._arrival_sequence
            self._arrival_sequence += 1
            emit(
                {
                    "event_type": "order_submitted",
                    "step": self._step,
                    "ts": ts,
                    "order_id": pending.order_id,
                    "agent_id": agent_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "price": order.limit_price,
                    "quantity": order.quantity,
                    "arrival": arrival,
                }
            )
            book = self._books[order.symbol]
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
                buyer_order_id = (
                    pending.order_id if order.side == "buy" else best.order_id
                )
                seller_order_id = (
                    pending.order_id if order.side == "sell" else best.order_id
                )
                trade = TradeRecord(
                    step=self._step,
                    sequence=len(step_trades),
                    ts=ts,
                    symbol=order.symbol,
                    price=price,
                    quantity=qty,
                    buyer_id=buyer_id,
                    seller_id=seller_id,
                    buyer_order_id=buyer_order_id,
                    seller_order_id=seller_order_id,
                    fee_per_side=abs(price * qty) * self.fee_bps / 1e4,
                )
                step_trades.append(trade)
                emit({"event_type": "trade", **asdict(trade)})
                trades[order.symbol].append((price, qty))
                remaining -= qty
                best.quantity -= qty
                if best.quantity <= 1e-9:
                    opposite.pop(match_index)
            if remaining > 1e-9 and order.limit_price is not None:
                book[order.side].append(
                    _Resting(
                        price=self._snap(order.limit_price), arrival=arrival,
                        order_id=pending.order_id, agent_id=agent_id,
                        side=order.side, quantity=remaining, created_step=self._step,
                    )
                )
            elif remaining > 1e-9:
                emit(
                    {
                        "event_type": "order_expired",
                        "step": self._step,
                        "ts": ts,
                        "order_id": pending.order_id,
                        "agent_id": agent_id,
                        "symbol": order.symbol,
                        "side": order.side,
                        "price": None,
                        "quantity": remaining,
                        "reason": "unfilled_market_remainder",
                    }
                )

        self.last_book_snapshot = self._snapshot_books(self._books)
        for symbol, sides in self.last_book_snapshot.items():
            for side, orders in sides.items():
                emit(
                    {
                        "event_type": "book_snapshot",
                        "step": self._step,
                        "ts": ts,
                        "symbol": symbol,
                        "side": side,
                        "orders": [asdict(order) for order in orders],
                    }
                )
        expiry_reason = (
            "step_end"
            if self.order_lifetime == ORDER_LIFETIME
            else "session_end"
            if self._step + 1 >= self.n_steps
            else None
        )
        if expiry_reason is not None:
            for sides in self.last_book_snapshot.values():
                for orders in sides.values():
                    for order in orders:
                        emit(
                            {
                                "event_type": "order_expired",
                                "step": self._step,
                                "ts": ts,
                                **asdict(order),
                                "reason": expiry_reason,
                            }
                        )
            self._books = {
                symbol: {"buy": [], "sell": []} for symbol in self.symbols
            }
        self.last_step_trades = tuple(step_trades)
        self.trade_tape += self.last_step_trades
        self.last_step_bars = self._append_bars(ts, trades)
        for bar in self.last_step_bars:
            emit({"event_type": "endogenous_bar", "step": self._step, **asdict(bar)})
        self.last_step_events = tuple(step_events)
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
                        order_id=order.order_id,
                        agent_id=order.agent_id,
                        arrival=order.arrival,
                        created_step=order.created_step,
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
