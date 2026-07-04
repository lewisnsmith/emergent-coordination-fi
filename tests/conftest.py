import numpy as np
import pytest

from flock.data import synthetic
from flock.markets.replay import ReplayMarket


@pytest.fixture(scope="session")
def synthetic_data():
    bars, events, meta = synthetic.generate(n_symbols=3, n_steps=80, seed=7)
    return bars, events, meta


@pytest.fixture()
def replay_market(synthetic_data):
    bars, events, _ = synthetic_data
    return ReplayMarket(bars, events, observation_window=10, max_steps=30)


@pytest.fixture()
def rng():
    return np.random.default_rng(0)
