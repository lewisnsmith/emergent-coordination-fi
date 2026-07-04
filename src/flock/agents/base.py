"""TradingAgent protocol: the single interface markets and runners depend on."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flock.core.types import Decision, Observation


@runtime_checkable
class TradingAgent(Protocol):
    agent_id: str
    cohort: str

    def decide(self, obs: Observation) -> Decision:
        """Return a Decision (possibly zero orders) for this observation."""
        ...

    def describe(self) -> dict:
        """Static parameterization for the decision log (kind, model, persona, ...)."""
        ...
