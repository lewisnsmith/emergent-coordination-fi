"""Conditional adoption-to-market-impact threshold projections (H7)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ThresholdForecast:
    threshold: float
    years: tuple[int, ...]
    crossing_probability: tuple[float, ...]
    median_share: tuple[float, ...]


def threshold_forecast(
    adoption_draws: np.ndarray,
    years: list[int],
    impact_threshold: float,
) -> ThresholdForecast:
    """Summarize externally supplied adoption draws; never invent adoption evidence."""
    draws = np.asarray(adoption_draws, dtype=float)
    if draws.ndim != 2 or draws.shape[1] != len(years):
        raise ValueError("adoption_draws must be draws × years")
    if not 0 <= impact_threshold <= 1 or np.any((draws < 0) | (draws > 1)):
        raise ValueError("shares and threshold must lie in [0,1]")
    return ThresholdForecast(
        threshold=impact_threshold,
        years=tuple(years),
        crossing_probability=tuple(float(x) for x in (draws >= impact_threshold).mean(axis=0)),
        median_share=tuple(float(x) for x in np.median(draws, axis=0)),
    )
