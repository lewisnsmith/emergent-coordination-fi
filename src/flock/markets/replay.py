"""Phase-1 replay market: agents trade replayed data with no interaction.

Equity panels retain the strict exact-intersection calendar. Binary prediction
contracts use a timestamp-aligned union calendar because listings and
maturities are asynchronous. Their terminal 0/1 bar is settlement data: it is
never exposed to an agent, never tradable, and is applied at the frozen
contract close after outstanding one-tick orders expire.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pandas as pd

from flock.core.types import Bar, Fill, NewsEvent, Order
from flock.markets.base import MarketState

_BINARY_PRICE_SEMANTICS = "YES probability in [0,1]"
_BINARY_REQUIRED_CONTEXT = {
    "symbol",
    "question",
    "rules",
    "open_ts",
    "close_ts",
    "resolution",
    "yes_label",
    "no_label",
    "price_semantics",
}
_AGENT_SAFE_CONTEXT = {
    "symbol",
    "question",
    "rules",
    "open_ts",
    "close_ts",
    "yes_label",
    "no_label",
    "price_semantics",
}
_EPSILON = 1e-9


def _timestamp(value: object, *, label: str) -> pd.Timestamp:
    try:
        parsed = pd.to_datetime(str(value), utc=True)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid {label}: {value!r}") from error
    if not isinstance(parsed, pd.Timestamp) or pd.isna(parsed):
        raise ValueError(f"invalid {label}: {value!r}")
    return parsed


def _display_timestamp(value: pd.Timestamp) -> str:
    if value == value.normalize():
        return value.date().isoformat()
    return value.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class _BinaryContract:
    symbol: str
    context: dict[str, Any]
    open_at: pd.Timestamp
    close_at: pd.Timestamp
    resolution: float
    tradable_bars: tuple[tuple[pd.Timestamp, Bar], ...]
    bar_index: dict[pd.Timestamp, int]


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
        binary_markers = {"resolution", "yes_label", "no_label", "price_semantics"}
        self.uses_binary_contract_lifecycle = any(
            binary_markers.intersection(context)
            for context in self.instrument_context.values()
        )

        if self.uses_binary_contract_lifecycle:
            self._initialize_binary(bars, max_steps)
        else:
            self._initialize_synchronous(bars, max_steps)

        self._events_by_ts: dict[str, list[NewsEvent]] = {}
        self._events_by_time: dict[pd.Timestamp, list[NewsEvent]] = {}
        if events is not None and len(events):
            for row in events.to_dict("records"):
                event = NewsEvent(**row)
                self._events_by_ts.setdefault(event.ts, []).append(event)
                event_time = _timestamp(event.ts, label="event timestamp")
                self._events_by_time.setdefault(event_time, []).append(event)
        self.reset()

    def _initialize_synchronous(
        self, bars: pd.DataFrame, max_steps: int | None
    ) -> None:
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

        aligned = cast(
            pd.DataFrame, bars.loc[bars["ts"].isin(list(common_timestamps)), :]
        )
        self._bars_by_symbol: dict[str, list[Bar]] = {
            cast(str, symbol): [Bar(**row) for row in group.to_dict("records")]
            for symbol, group in aligned.groupby("symbol")
        }
        first = self.window
        last = len(self.timestamps) - 1
        n_available = max(last - first, 0)
        self.n_steps = (
            min(n_available, max_steps) if max_steps is not None else n_available
        )
        self._contracts: dict[str, _BinaryContract] = {}
        self._all_binary_times: list[pd.Timestamp] = []
        self._binary_times: list[pd.Timestamp] = []
        self._binary_truncated = False

    def _initialize_binary(self, bars: pd.DataFrame, max_steps: int | None) -> None:
        if set(self.instrument_context) != set(self.symbols):
            raise ValueError(
                "binary replay requires exactly one contract definition per bar symbol"
            )
        contracts: dict[str, _BinaryContract] = {}
        decision_times: set[pd.Timestamp] = set()
        for symbol in self.symbols:
            context = self.instrument_context[symbol]
            if not _BINARY_REQUIRED_CONTEXT.issubset(context):
                raise ValueError(f"incomplete binary contract definition for {symbol}")
            if context["price_semantics"] != _BINARY_PRICE_SEMANTICS:
                raise ValueError(f"unsupported binary price semantics for {symbol}")
            if str(context["yes_label"]).strip().casefold() != "yes":
                raise ValueError(f"ambiguous YES label for {symbol}")
            if str(context["no_label"]).strip().casefold() != "no":
                raise ValueError(f"ambiguous NO label for {symbol}")
            if not str(context["question"]).strip() or not str(context["rules"]).strip():
                raise ValueError(f"binary question and rules must be nonempty for {symbol}")

            open_at = _timestamp(context["open_ts"], label=f"{symbol} open timestamp")
            close_at = _timestamp(context["close_ts"], label=f"{symbol} close timestamp")
            if open_at > close_at:
                raise ValueError(f"binary contract opens after it closes: {symbol}")
            resolution = float(context["resolution"])
            if resolution not in {0.0, 1.0}:
                raise ValueError(f"binary resolution must be zero or one for {symbol}")

            group = bars.loc[bars["symbol"] == symbol].copy()
            parsed_times = [
                _timestamp(value, label=f"{symbol} bar timestamp")
                for value in cast(list[object], group["ts"].tolist())
            ]
            if len(set(parsed_times)) != len(parsed_times):
                raise ValueError(f"duplicate normalized binary bar timestamp for {symbol}")
            rows = [Bar(**row) for row in group.to_dict("records")]
            ordered = sorted(zip(parsed_times, rows, strict=True), key=lambda item: item[0])
            if len(ordered) < self.window + 2:
                raise ValueError(
                    f"binary contract {symbol} needs at least observation_window + 2 bars"
                )
            outside_lifetime = any(
                not (open_at <= timestamp <= close_at) for timestamp, _ in ordered
            )
            if outside_lifetime:
                raise ValueError(f"binary bars fall outside the contract lifetime for {symbol}")
            for _, bar in ordered:
                prices = (bar.open, bar.high, bar.low, bar.close)
                if not all(0.0 <= price <= 1.0 for price in prices):
                    raise ValueError(f"binary YES prices must remain in [0,1] for {symbol}")
                if bar.high < max(bar.open, bar.low, bar.close) or bar.low > min(
                    bar.open, bar.high, bar.close
                ):
                    raise ValueError(f"inconsistent binary OHLC bounds for {symbol}")
            terminal_time, terminal_bar = ordered[-1]
            if abs(terminal_bar.close - resolution) > 1e-12:
                raise ValueError(
                    f"terminal binary bar must equal the resolution payout for {symbol}"
                )
            if terminal_time > close_at:
                raise ValueError(f"binary settlement bar follows contract close for {symbol}")

            # The terminal bar carries the known outcome and is settlement-only.
            tradable = tuple(ordered[:-1])
            bar_index = {timestamp: index for index, (timestamp, _) in enumerate(tradable)}
            decision_times.update(timestamp for timestamp, _ in tradable[self.window :])
            contracts[symbol] = _BinaryContract(
                symbol=symbol,
                context=dict(context),
                open_at=open_at,
                close_at=close_at,
                resolution=resolution,
                tradable_bars=tradable,
                bar_index=bar_index,
            )

        self._contracts = contracts
        self._all_binary_times = sorted(decision_times)
        if not self._all_binary_times:
            raise ValueError("binary replay has no timestamp with sufficient visible history")
        if max_steps is None:
            self._binary_times = self._all_binary_times
        else:
            self._binary_times = self._all_binary_times[:max_steps]
        if not self._binary_times:
            raise ValueError("binary replay max_steps leaves no decision timestamps")
        self._binary_truncated = len(self._binary_times) < len(self._all_binary_times)
        self.timestamps = [_display_timestamp(value) for value in self._binary_times]
        self.n_steps = len(self._binary_times)
        self._bars_by_symbol = {}

    def reset(self) -> None:
        self._step = 0
        self._pending: list[tuple[str, Order, float]] = []
        self._binary_positions: dict[tuple[str, str], float] = {}
        self._settled_contracts: set[str] = set()

    def register_position(self, agent_id: str, symbol: str, quantity: float) -> None:
        """Register a pre-run YES position so binary settlement is complete."""
        if not self.uses_binary_contract_lifecycle:
            raise ValueError("initial position registration is only used for binary replay")
        if self._step != 0 or self._pending:
            raise ValueError("initial positions must be registered before replay starts")
        if symbol not in self._contracts or quantity < 0:
            raise ValueError(f"invalid initial binary position for {symbol}")
        key = (agent_id, symbol)
        if key in self._binary_positions:
            raise ValueError(f"duplicate initial binary position for {agent_id}/{symbol}")
        self._binary_positions[key] = quantity

    @property
    def done(self) -> bool:
        return self._step >= self.n_steps

    def _t_index(self) -> int:
        return self.window + self._step

    def _bar(self, symbol: str, t_index: int) -> Bar:
        return self._bars_by_symbol[symbol][t_index]

    def state(self) -> MarketState:
        if self.uses_binary_contract_lifecycle:
            return self._binary_state()
        t = self._t_index()
        ts = self.timestamps[t]
        window_bars = {
            symbol: tuple(self._bars_by_symbol[symbol][t - self.window + 1 : t + 1])
            for symbol in self.symbols
        }
        return MarketState(
            step=self._step,
            ts=ts,
            symbols=self.symbols,
            bars=window_bars,
            prices={symbol: window_bars[symbol][-1].close for symbol in self.symbols},
            news=tuple(self._events_by_ts.get(ts, ())),
            instrument_context={
                symbol: self.instrument_context[symbol]
                for symbol in self.symbols
                if symbol in self.instrument_context
            },
        )

    def _binary_state(self) -> MarketState:
        now = self._binary_times[self._step]
        active: list[str] = []
        windows: dict[str, tuple[Bar, ...]] = {}
        prices: dict[str, float] = {}
        contexts: dict[str, dict[str, Any]] = {}
        for symbol, contract in self._contracts.items():
            index = contract.bar_index.get(now)
            if (
                index is None
                or index < self.window
                or not (contract.open_at <= now < contract.close_at)
            ):
                continue
            active.append(symbol)
            windows[symbol] = tuple(
                bar for _, bar in contract.tradable_bars[index - self.window + 1 : index + 1]
            )
            prices[symbol] = windows[symbol][-1].close
            safe_context = {
                key: value for key, value in contract.context.items() if key in _AGENT_SAFE_CONTEXT
            }
            safe_context.update(
                {
                    "contract_status": "active",
                    "tradable_side": "YES",
                    "yes_payout": "1 if the rules resolve Yes; otherwise 0",
                    "no_payout": "1 - YES payout; direct NO shares are not traded in this replay",
                }
            )
            contexts[symbol] = safe_context

        active_symbols = tuple(sorted(active))
        if not active_symbols:
            raise RuntimeError("binary replay timeline produced an empty decision state")
        news = tuple(
            event
            for event in self._events_by_time.get(now, ())
            if not event.symbol or event.symbol in active_symbols
        )
        return MarketState(
            step=self._step,
            ts=_display_timestamp(now),
            symbols=active_symbols,
            bars=windows,
            prices=prices,
            news=news,
            instrument_context=contexts,
        )

    def submit(self, agent_id: str, orders: tuple[Order, ...]) -> None:
        if self.uses_binary_contract_lifecycle:
            active = set(self.state().symbols)
            for order in orders:
                if order.symbol not in active:
                    raise ValueError(f"cannot trade inactive binary contract {order.symbol}")
                self._pending.append((agent_id, order, self.state().prices[order.symbol]))
            return
        t = self._t_index()
        self._pending.extend(
            (agent_id, order, self._bar(order.symbol, t).close) for order in orders
        )

    def step(self) -> list[Fill]:
        """Advance one timestamp and apply fills without exposing future bars."""
        if self.uses_binary_contract_lifecycle:
            return self._step_binary()
        t_next = self._t_index() + 1
        fills: list[Fill] = []
        for agent_id, order, submission_reference in self._pending:
            nxt = self._bar(order.symbol, t_next)
            fill = self._make_fill(agent_id, order, submission_reference, nxt)
            if fill is not None:
                fills.append(fill)
        self._pending = []
        self._step += 1
        return fills

    def _step_binary(self) -> list[Fill]:
        now = self._binary_times[self._step]
        final_selected_step = self._step + 1 == len(self._binary_times)
        if final_selected_step and self._binary_truncated:
            horizon = now
        elif self._step + 1 < len(self._all_binary_times):
            horizon = self._all_binary_times[self._step + 1]
        else:
            horizon = max(contract.close_at for contract in self._contracts.values())

        fills: list[Fill] = []
        for agent_id, order, submission_reference in self._pending:
            if horizon <= now:
                continue
            contract = self._contracts[order.symbol]
            index = contract.bar_index.get(horizon)
            # Orders are DAY/one-replay-tick orders. They expire rather than
            # reserve cash across another contract's intervening timestamp.
            if index is None:
                continue
            nxt = contract.tradable_bars[index][1]
            fill = self._make_fill(
                agent_id, order, submission_reference, nxt, binary=True
            )
            if fill is not None:
                self._record_binary_fill(fill)
                fills.append(fill)
        self._pending = []

        due = sorted(
            (
                contract
                for contract in self._contracts.values()
                if contract.symbol not in self._settled_contracts
                and now < contract.close_at <= horizon
            ),
            key=lambda contract: (contract.close_at, contract.symbol),
        )
        for contract in due:
            holdings = sorted(
                (
                    (agent_id, quantity)
                    for (agent_id, symbol), quantity in self._binary_positions.items()
                    if symbol == contract.symbol and quantity > _EPSILON
                ),
                key=lambda item: item[0],
            )
            for agent_id, quantity in holdings:
                fill = Fill(
                    agent_id=agent_id,
                    step=self._step,
                    ts=str(contract.context["close_ts"]),
                    symbol=contract.symbol,
                    side="sell",
                    quantity=quantity,
                    price=contract.resolution,
                    fee=0.0,
                )
                self._record_binary_fill(fill)
                fills.append(fill)
            self._settled_contracts.add(contract.symbol)

        self._step += 1
        return fills

    def _make_fill(
        self,
        agent_id: str,
        order: Order,
        submission_reference: float,
        nxt: Bar,
        *,
        binary: bool = False,
    ) -> Fill | None:
        price = self._fill_price(order, nxt, binary=binary)
        if price is None:
            return None
        quantity = order.quantity
        if order.side == "buy" and order.limit_price is None and price > submission_reference:
            quantity *= submission_reference / price
        fee = abs(price * quantity) * self.fee_bps / 1e4
        return Fill(
            agent_id,
            self._step,
            nxt.ts,
            order.symbol,
            order.side,
            quantity,
            price,
            fee,
        )

    def _record_binary_fill(self, fill: Fill) -> None:
        key = (fill.agent_id, fill.symbol)
        held = self._binary_positions.get(key, 0.0)
        quantity = held + (fill.quantity if fill.side == "buy" else -fill.quantity)
        if quantity < -_EPSILON:
            raise ValueError(
                "binary replay fill would create a short position for "
                f"{fill.agent_id}/{fill.symbol}"
            )
        self._binary_positions[key] = max(quantity, 0.0)

    def _fill_price(self, order: Order, nxt: Bar, *, binary: bool = False) -> float | None:
        slip = nxt.open * self.slippage_bps / 1e4
        if order.limit_price is None:
            price = nxt.open + slip if order.side == "buy" else nxt.open - slip
        elif order.side == "buy" and nxt.low <= order.limit_price:
            price = min(order.limit_price, nxt.open)
        elif order.side == "sell" and nxt.high >= order.limit_price:
            price = max(order.limit_price, nxt.open)
        else:
            return None
        return min(max(price, 0.0), 1.0) if binary else price
