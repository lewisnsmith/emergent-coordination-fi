"""Per-agent portfolio accounting and order constraint enforcement.

Constraints (identical for every agent, per experimental design): long-only,
buys limited by available cash (with a fee buffer), position size capped at
max_position_per_symbol units.
"""

from __future__ import annotations

import math

from flock.core.types import Fill, Order, PortfolioView, Position

_QUANTITY_PRECISION = 4
_EPSILON = 1e-9


class Ledger:
    def __init__(self, initial_cash: float, max_position_per_symbol: float, fee_bps: float):
        self.cash = initial_cash
        self.max_position = max_position_per_symbol
        self.fee_bps = fee_bps
        self.qty: dict[str, float] = {}
        self.avg_price: dict[str, float] = {}

    def clip_orders(
        self,
        orders: tuple[Order, ...],
        prices: dict[str, float],
        existing_orders: tuple[Order, ...] = (),
    ) -> tuple[Order, ...]:
        """Enforce constraints using fill-independent reservations.

        Orders in one decision are simultaneous: an unfilled buy cannot provide
        inventory for a sell, and an unfilled sell cannot provide cash or position
        room for a buy. Persistent limits from prior steps remain reserved until
        they fill, cancel, or expire.
        """
        clipped: list[Order] = []
        reserved_cash = 0.0
        reserved_buys: dict[str, float] = {}
        reserved_sells: dict[str, float] = {}
        fee_multiplier = 1 + self.fee_bps / 1e4

        for order in existing_orders:
            reference = (
                order.limit_price
                if order.limit_price is not None
                else prices[order.symbol]
            )
            if order.side == "buy":
                reserved_cash += order.quantity * reference * fee_multiplier
                reserved_buys[order.symbol] = (
                    reserved_buys.get(order.symbol, 0.0) + order.quantity
                )
            else:
                reserved_sells[order.symbol] = (
                    reserved_sells.get(order.symbol, 0.0) + order.quantity
                )

        for o in orders:
            ref = o.limit_price if o.limit_price is not None else prices[o.symbol]
            if ref <= 0:
                continue
            if o.side == "buy":
                room = (
                    self.max_position
                    - self.qty.get(o.symbol, 0.0)
                    - reserved_buys.get(o.symbol, 0.0)
                )
                available_cash = self.cash - reserved_cash
                affordable = available_cash / (ref * fee_multiplier)
                quantity = self._floor_quantity(
                    max(0.0, min(o.quantity, room, affordable))
                )
                if quantity < _EPSILON:
                    continue
                reserved_cash += quantity * ref * fee_multiplier
                reserved_buys[o.symbol] = reserved_buys.get(o.symbol, 0.0) + quantity
                clipped.append(Order(o.symbol, "buy", quantity, o.limit_price))
            else:
                available_inventory = (
                    self.qty.get(o.symbol, 0.0) - reserved_sells.get(o.symbol, 0.0)
                )
                quantity = self._floor_quantity(
                    max(0.0, min(o.quantity, available_inventory))
                )
                if quantity < _EPSILON:
                    continue
                reserved_sells[o.symbol] = reserved_sells.get(o.symbol, 0.0) + quantity
                clipped.append(Order(o.symbol, "sell", quantity, o.limit_price))
        return tuple(clipped)

    @staticmethod
    def _floor_quantity(quantity: float) -> float:
        """Quantize without rounding above an available constraint."""
        scale = 10**_QUANTITY_PRECISION
        return math.floor((quantity + _EPSILON) * scale) / scale

    def apply(self, fill: Fill) -> None:
        """Apply one fill atomically, rejecting any portfolio invariant violation."""
        if fill.quantity < 0 or fill.fee < 0:
            raise ValueError("Fill quantity and fee must be non-negative")

        cost = fill.price * fill.quantity
        held = self.qty.get(fill.symbol, 0.0)
        if fill.side == "buy":
            new_quantity = held + fill.quantity
            new_cash = self.cash - cost - fill.fee
        else:
            new_quantity = held - fill.quantity
            new_cash = self.cash + cost - fill.fee

        if new_cash < -_EPSILON:
            raise ValueError(
                f"Fill would make cash negative: {self.cash} -> {new_cash}"
            )
        if new_quantity < -_EPSILON:
            raise ValueError(
                f"Fill would create a short position in {fill.symbol}: "
                f"{held} -> {new_quantity}"
            )
        if new_quantity > self.max_position + _EPSILON:
            raise ValueError(
                f"Fill would exceed the {fill.symbol} position cap: "
                f"{new_quantity} > {self.max_position}"
            )

        new_cash = max(new_cash, 0.0)
        new_quantity = min(max(new_quantity, 0.0), self.max_position)
        if fill.side == "buy":
            self.avg_price[fill.symbol] = (
                (self.avg_price.get(fill.symbol, 0.0) * held + cost) / new_quantity
                if new_quantity
                else 0.0
            )
        self.qty[fill.symbol] = new_quantity
        self.cash = new_cash

    def equity(self, prices: dict[str, float]) -> float:
        return self.cash + sum(q * prices.get(s, 0.0) for s, q in self.qty.items())

    def weights(self, prices: dict[str, float]) -> dict[str, float]:
        eq = self.equity(prices)
        if eq <= 0:
            return {s: 0.0 for s in self.qty}
        return {s: q * prices.get(s, 0.0) / eq for s, q in self.qty.items() if q}

    def view(self, prices: dict[str, float]) -> PortfolioView:
        positions = tuple(
            Position(s, q, self.avg_price.get(s, 0.0)) for s, q in sorted(self.qty.items()) if q
        )
        return PortfolioView(cash=self.cash, positions=positions, equity=self.equity(prices))
