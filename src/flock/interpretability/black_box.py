"""Causal input interventions available for both APIs and local models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from flock.core.types import Observation
from flock.experiments.treatments import apply_information_policy


@dataclass(frozen=True)
class AttributionEffect:
    feature: str
    estimate: float
    paired_effects: tuple[float, ...]


def intervention_observation(obs: Observation, feature: str) -> Observation:
    """Create a preregisterable ablation while retaining a valid observation."""
    if feature == "news":
        return apply_information_policy(obs, "no-news")
    if feature.startswith("symbol_history:"):
        symbol = feature.split(":", 1)[1]
        if symbol not in obs.symbols:
            raise KeyError(f"unknown symbol {symbol}")
        bars = dict(obs.bars)
        bars[symbol] = (bars[symbol][-1],)
        return Observation(
            step=obs.step,
            ts=obs.ts,
            symbols=obs.symbols,
            bars=bars,
            prices=obs.prices,
            news=obs.news,
            portfolio=obs.portfolio,
            instrument_context=obs.instrument_context,
        )
    raise ValueError(f"unknown black-box intervention '{feature}'")


def paired_attribution(
    feature: str,
    control_scores: list[float],
    intervention_scores: list[float],
) -> AttributionEffect:
    """Estimate a within-block intervention effect; callers retain block IDs."""
    if len(control_scores) != len(intervention_scores) or len(control_scores) < 2:
        raise ValueError("paired attribution needs equal lists with at least two blocks")
    effects = np.asarray(intervention_scores) - np.asarray(control_scores)
    return AttributionEffect(feature, float(effects.mean()), tuple(float(x) for x in effects))
