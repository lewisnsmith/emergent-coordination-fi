"""Deterministic observation treatments used by information-set experiments."""

from __future__ import annotations

import hashlib

from flock.core.types import Observation


def apply_information_policy(obs: Observation, policy: str) -> Observation:
    """Return a treated observation without mutating the shared market state."""
    if policy == "shared-all":
        return obs
    if policy in {"no-news", "price-only"}:
        news = ()
    elif policy in {"news-partition-a", "news-partition-b"}:
        parity = 0 if policy.endswith("a") else 1
        news = tuple(
            event
            for event in obs.news
            if hashlib.sha256(
                f"{event.ts}|{event.symbol}|{event.headline}".encode()
            ).digest()[0]
            % 2
            == parity
        )
    else:
        raise ValueError(f"unknown information policy '{policy}'")
    return Observation(
        step=obs.step,
        ts=obs.ts,
        symbols=obs.symbols,
        bars=obs.bars,
        prices=obs.prices,
        news=news,
        portfolio=obs.portfolio,
        instrument_context=obs.instrument_context,
    )
