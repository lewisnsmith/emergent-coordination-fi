"""Market protocol and the state snapshot markets expose to the runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from flock.core.types import Bar, Fill, NewsEvent, Order


@dataclass(frozen=True)
class BookLevel:
    price: float
    quantity: float


@dataclass(frozen=True)
class BookView:
    """Anonymous public order book summary (exchange markets only)."""

    bids: tuple[BookLevel, ...] = ()
    asks: tuple[BookLevel, ...] = ()


@dataclass(frozen=True)
class MarketState:
    """Market-visible snapshot at the current step (identical for all agents)."""

    step: int
    ts: str
    symbols: tuple[str, ...]
    bars: dict[str, tuple[Bar, ...]]  # trailing window per symbol, oldest first
    prices: dict[str, float]
    news: tuple[NewsEvent, ...] = ()
    books: dict[str, BookView] = field(default_factory=dict)
    instrument_context: dict[str, dict[str, Any]] = field(default_factory=dict)


class Market(Protocol):
    """Order lifecycle: submit() queues orders for the current step; step()
    advances time, executes queued orders, and returns the fills."""

    symbols: tuple[str, ...]

    def reset(self) -> None: ...

    def state(self) -> MarketState: ...

    def submit(self, agent_id: str, orders: tuple[Order, ...]) -> None: ...

    def step(self) -> list[Fill]: ...

    @property
    def done(self) -> bool: ...
