"""Core domain types shared by agents, markets, experiments, and analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Side = Literal["buy", "sell"]


@dataclass(frozen=True)
class Bar:
    ts: str  # ISO date/datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class NewsEvent:
    ts: str
    symbol: str  # "" for market-wide events
    headline: str
    sentiment: float  # [-1, 1]


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    avg_price: float


@dataclass(frozen=True)
class PortfolioView:
    cash: float
    positions: tuple[Position, ...]
    equity: float

    def weight(self, symbol: str, price: float) -> float:
        for p in self.positions:
            if p.symbol == symbol and self.equity:
                return p.quantity * price / self.equity
        return 0.0


@dataclass(frozen=True)
class Observation:
    """Everything an agent sees at one decision step.

    In replay mode the market fields are identical across agents (identical
    information sets); only `portfolio` differs once positions diverge.
    """

    step: int
    ts: str
    symbols: tuple[str, ...]
    bars: dict[str, tuple[Bar, ...]]  # symbol -> trailing window, oldest first
    prices: dict[str, float]  # symbol -> current reference price
    news: tuple[NewsEvent, ...]
    portfolio: PortfolioView

    def digest_payload(self) -> str:
        """Stable string of the market-visible part (excludes portfolio)."""
        parts = [self.ts]
        for s in self.symbols:
            last = self.bars[s][-1]
            parts.append(f"{s}:{last.close:.6f}:{len(self.bars[s])}")
        parts.extend(f"{n.ts}|{n.symbol}|{n.headline}" for n in self.news)
        return ";".join(parts)


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: float
    limit_price: float | None = None  # None = market order


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass(frozen=True)
class Decision:
    agent_id: str
    step: int
    orders: tuple[Order, ...]
    rationale: str = ""
    parse_ok: bool = True
    usage: Usage = field(default_factory=Usage)
    latency_s: float = 0.0

    @property
    def action(self) -> str:
        """Net action label used by decision-level metrics: buy/sell/hold."""
        net = sum(o.quantity if o.side == "buy" else -o.quantity for o in self.orders)
        if net > 0:
            return "buy"
        if net < 0:
            return "sell"
        return "hold"


@dataclass(frozen=True)
class Fill:
    agent_id: str
    step: int
    ts: str
    symbol: str
    side: Side
    quantity: float
    price: float
    fee: float
