"""Core domain types shared by agents, markets, experiments, and analysis."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

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
    instrument_context: dict[str, dict[str, Any]] = field(default_factory=dict)

    def digest_payload(self) -> str:
        """Stable serialization of the complete observation, including portfolio."""
        payload = {
            "step": self.step,
            "ts": self.ts,
            "symbols": self.symbols,
            "bars": {symbol: [asdict(bar) for bar in self.bars[symbol]] for symbol in self.symbols},
            "prices": self.prices,
            "news": [asdict(event) for event in self.news],
            "instrument_context": self.instrument_context,
            "portfolio": asdict(self.portfolio),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


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
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    visible_output_tokens: int = 0
    reasoning_tokens: int = 0
    attempts: int = 0
    request_ids: tuple[str, ...] = ()
    retry_errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class Decision:
    agent_id: str
    step: int
    orders: tuple[Order, ...]
    rationale: str = ""
    parse_ok: bool = True
    usage: Usage = field(default_factory=Usage)
    latency_s: float = 0.0
    evidence_refs: tuple[str, ...] = ()
    confidence: float | None = None
    uncertainties: tuple[str, ...] = ()
    grounding_ok: bool = True
    grounding_failures: tuple[str, ...] = ()
    prompt_hash: str = ""
    raw_response_hash: str = ""

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
