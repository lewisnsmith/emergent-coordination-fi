"""Per-agent portfolio accounting and order constraint enforcement.

Constraints (identical for every agent, per experimental design): long-only,
buys limited by available cash (with a fee buffer), position size capped at
max_position_per_symbol units.
"""

from __future__ import annotations

from flock.core.types import Fill, Order, PortfolioView, Position


class Ledger:
    def __init__(self, initial_cash: float, max_position_per_symbol: float, fee_bps: float):
        self.cash = initial_cash
        self.max_position = max_position_per_symbol
        self.fee_bps = fee_bps
        self.qty: dict[str, float] = {}
        self.avg_price: dict[str, float] = {}

    def clip_orders(self, orders: tuple[Order, ...], prices: dict[str, float]) -> tuple[Order, ...]:
        """Enforce cash / long-only / position-cap constraints, preserving order."""
        clipped: list[Order] = []
        cash = self.cash
        qty = dict(self.qty)
        for o in orders:
            ref = o.limit_price if o.limit_price is not None else prices[o.symbol]
            if ref <= 0:
                continue
            if o.side == "buy":
                room = self.max_position - qty.get(o.symbol, 0.0)
                affordable = cash / (ref * (1 + self.fee_bps / 1e4))
                q = max(0.0, min(o.quantity, room, affordable))
                if q < 1e-9:
                    continue
                cash -= q * ref * (1 + self.fee_bps / 1e4)
                qty[o.symbol] = qty.get(o.symbol, 0.0) + q
                clipped.append(Order(o.symbol, "buy", round(q, 4), o.limit_price))
            else:
                q = min(o.quantity, qty.get(o.symbol, 0.0))
                if q < 1e-9:
                    continue
                qty[o.symbol] = qty.get(o.symbol, 0.0) - q
                clipped.append(Order(o.symbol, "sell", round(q, 4), o.limit_price))
        return tuple(clipped)

    def apply(self, fill: Fill) -> None:
        cost = fill.price * fill.quantity
        if fill.side == "buy":
            held = self.qty.get(fill.symbol, 0.0)
            total = held + fill.quantity
            self.avg_price[fill.symbol] = (
                (self.avg_price.get(fill.symbol, 0.0) * held + cost) / total if total else 0.0
            )
            self.qty[fill.symbol] = total
            self.cash -= cost + fill.fee
        else:
            self.qty[fill.symbol] = self.qty.get(fill.symbol, 0.0) - fill.quantity
            self.cash += cost - fill.fee

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
