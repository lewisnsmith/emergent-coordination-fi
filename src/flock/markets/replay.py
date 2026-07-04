"""Phase-1 replay market: agents trade replayed data with no interaction.

No price impact. Orders submitted at step t fill at bar t+1's open (no
lookahead) adjusted by slippage, plus fees. Limit orders fill only if the
next bar's range crosses the limit.
"""

from __future__ import annotations

import pandas as pd

from flock.core.types import Bar, Fill, NewsEvent, Order
from flock.markets.base import MarketState


class ReplayMarket:
    def __init__(
        self,
        bars: pd.DataFrame,  # columns: ts, symbol, open, high, low, close, volume
        events: pd.DataFrame | None = None,  # columns: ts, symbol, headline, sentiment
        observation_window: int = 20,
        fee_bps: float = 5.0,
        slippage_bps: float = 2.0,
        max_steps: int | None = None,
    ):
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.window = observation_window

        bars = bars.sort_values(["ts", "symbol"])
        self.timestamps: list[str] = sorted(bars["ts"].unique().tolist())
        self.symbols: tuple[str, ...] = tuple(sorted(bars["symbol"].unique().tolist()))
        self._bars_by_symbol: dict[str, list[Bar]] = {
            s: [Bar(**row) for row in g.to_dict("records")]
            for s, g in bars.groupby("symbol")
        }
        self._events_by_ts: dict[str, list[NewsEvent]] = {}
        if events is not None and len(events):
            for row in events.to_dict("records"):
                self._events_by_ts.setdefault(row["ts"], []).append(NewsEvent(**row))

        # Steps run from `window` (enough history) to len-2 (need t+1 to fill).
        first = self.window
        last = len(self.timestamps) - 1
        n_available = max(last - first, 0)
        self.n_steps = min(n_available, max_steps) if max_steps else n_available
        self.reset()

    def reset(self) -> None:
        self._step = 0
        self._pending: list[tuple[str, Order]] = []

    @property
    def done(self) -> bool:
        return self._step >= self.n_steps

    def _t_index(self) -> int:
        return self.window + self._step

    def _bar(self, symbol: str, t_index: int) -> Bar:
        return self._bars_by_symbol[symbol][t_index]

    def state(self) -> MarketState:
        t = self._t_index()
        ts = self.timestamps[t]
        window_bars = {
            s: tuple(self._bars_by_symbol[s][t - self.window + 1 : t + 1]) for s in self.symbols
        }
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
        """Advance one bar; fill pending orders at the next bar."""
        t_next = self._t_index() + 1
        fills: list[Fill] = []
        for agent_id, order in self._pending:
            nxt = self._bar(order.symbol, t_next)
            price = self._fill_price(order, nxt)
            if price is None:
                continue
            fee = abs(price * order.quantity) * self.fee_bps / 1e4
            fills.append(
                Fill(
                    agent_id, self._step, nxt.ts, order.symbol, order.side,
                    order.quantity, price, fee,
                )
            )
        self._pending = []
        self._step += 1
        return fills

    def _fill_price(self, order: Order, nxt: Bar) -> float | None:
        slip = nxt.open * self.slippage_bps / 1e4
        if order.limit_price is None:
            return nxt.open + slip if order.side == "buy" else nxt.open - slip
        # Limit order: fills if next bar trades through the limit.
        if order.side == "buy" and nxt.low <= order.limit_price:
            return min(order.limit_price, nxt.open)
        if order.side == "sell" and nxt.high >= order.limit_price:
            return max(order.limit_price, nxt.open)
        return None
