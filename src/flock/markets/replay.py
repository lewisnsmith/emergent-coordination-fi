"""Phase-1 replay market: agents trade replayed data with no interaction.

No price impact. Orders submitted at step t fill at bar t+1's open (no
lookahead) adjusted by slippage, plus fees. Limit orders fill only if the
next bar's range crosses the limit. A market buy that gaps above its
submission reference receives fewer shares so its executed notional does not
exceed the amount the ledger reserved at submission.
"""

from __future__ import annotations

from typing import Any, cast

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
        instrument_context: dict[str, dict[str, Any]] | None = None,
    ):
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.window = observation_window
        self.instrument_context = instrument_context or {}

        duplicate_rows = bars.duplicated(["symbol", "ts"], keep=False)
        if duplicate_rows.any():
            duplicate_keys = (
                bars.loc[duplicate_rows, ["symbol", "ts"]]
                .drop_duplicates()
                .sort_values(["symbol", "ts"])
                .to_dict("records")
            )
            raise ValueError(
                "Replay bars contain duplicate (symbol, ts) rows: "
                f"{duplicate_keys}"
            )

        bars = bars.sort_values(["ts", "symbol"])
        symbols = cast(list[str], bars["symbol"].unique().tolist())
        self.symbols: tuple[str, ...] = tuple(sorted(symbols))
        timestamp_sets = [
            set(cast(list[str], group["ts"].tolist()))
            for _, group in bars.groupby("symbol")
        ]
        common_timestamps = set.intersection(*timestamp_sets) if timestamp_sets else set()
        self.timestamps: list[str] = sorted(common_timestamps)

        required_bars = self.window + 2
        if len(self.timestamps) < required_bars:
            raise ValueError(
                "ReplayMarket requires at least "
                f"observation_window + 2 ({required_bars}) timestamps common to every symbol; "
                f"found {len(self.timestamps)}"
            )

        bars = cast(
            pd.DataFrame, bars.loc[bars["ts"].isin(list(common_timestamps)), :]
        )
        self._bars_by_symbol: dict[str, list[Bar]] = {
            cast(str, s): [Bar(**row) for row in g.to_dict("records")]
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
        self._pending: list[tuple[str, Order, float]] = []

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
            instrument_context={
                symbol: self.instrument_context[symbol]
                for symbol in self.symbols
                if symbol in self.instrument_context
            },
        )

    def submit(self, agent_id: str, orders: tuple[Order, ...]) -> None:
        t = self._t_index()
        self._pending.extend(
            (agent_id, order, self._bar(order.symbol, t).close) for order in orders
        )

    def step(self) -> list[Fill]:
        """Advance one bar; fill pending orders at the next bar."""
        t_next = self._t_index() + 1
        fills: list[Fill] = []
        for agent_id, order, submission_reference in self._pending:
            nxt = self._bar(order.symbol, t_next)
            price = self._fill_price(order, nxt)
            if price is None:
                continue
            quantity = order.quantity
            if (
                order.side == "buy"
                and order.limit_price is None
                and price > submission_reference
            ):
                quantity *= submission_reference / price
            fee = abs(price * quantity) * self.fee_bps / 1e4
            fills.append(
                Fill(
                    agent_id, self._step, nxt.ts, order.symbol, order.side,
                    quantity, price, fee,
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
