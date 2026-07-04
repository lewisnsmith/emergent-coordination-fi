"""Instrument kinds traded in flock markets.

Convention for binary prediction contracts: the price path is in (0, 1) and the
dataset's final bar closes at the resolution payout (0.0 or 1.0), so settlement
is implicit in replay — marking to the last close settles the contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

InstrumentKind = Literal["equity", "binary"]


@dataclass(frozen=True)
class Instrument:
    symbol: str
    kind: InstrumentKind = "equity"
    description: str = ""
    # binary contracts
    resolution: float | None = None  # 0.0 or 1.0 once resolved
    resolution_ts: str | None = None

    def clamp_price(self, price: float) -> float:
        if self.kind == "binary":
            return min(max(price, 0.001), 0.999)
        return max(price, 0.0)
