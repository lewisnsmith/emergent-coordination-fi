"""Classical baseline strategy agents (the internal control cohort).

Each baseline draws its hyperparameters from a per-instance RNG (derived from
the run seed) unless pinned in config, so the baseline cohort has within-family
heterogeneity comparable to real algo populations.
"""

from flock.agents.baselines.strategies import (
    BuyHoldAgent,
    MarketMakerAgent,
    MeanReversionAgent,
    MomentumAgent,
    RandomAgent,
    make_baseline,
)

__all__ = [
    "BuyHoldAgent",
    "MarketMakerAgent",
    "MeanReversionAgent",
    "MomentumAgent",
    "RandomAgent",
    "make_baseline",
]
