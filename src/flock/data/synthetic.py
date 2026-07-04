"""Regime-switching synthetic market generator (offline, seeded, free).

Price process per symbol: common factor + idiosyncratic component, with a
Markov chain over regimes {trend_up, trend_down, mean_revert, crisis}.
News events fire at regime switches with sentiment matching the new regime,
so agents that read news have a real (known) signal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REGIMES = ["trend_up", "trend_down", "mean_revert", "crisis"]

# rows: from-regime; cols: to-regime (order as REGIMES)
TRANSITION = np.array(
    [
        [0.90, 0.02, 0.06, 0.02],
        [0.04, 0.88, 0.06, 0.02],
        [0.05, 0.05, 0.86, 0.04],
        [0.10, 0.10, 0.20, 0.60],
    ]
)

# (daily drift, daily vol, mean-reversion strength kappa)
REGIME_PARAMS = {
    "trend_up": (0.0012, 0.010, 0.0),
    "trend_down": (-0.0010, 0.012, 0.0),
    "mean_revert": (0.0, 0.008, 0.08),
    "crisis": (-0.0035, 0.035, 0.0),
}

HEADLINES = {
    "trend_up": ("Analysts raise outlook as buying momentum builds", 0.6),
    "trend_down": ("Sector outlook dims on weakening demand", -0.5),
    "mean_revert": ("Markets steady as volatility subsides", 0.1),
    "crisis": ("Liquidity stress spreads; risk assets sold heavily", -0.9),
}


def generate(
    n_symbols: int = 5,
    n_steps: int = 252,
    seed: int = 42,
    start_price: float = 100.0,
    factor_load: float = 0.6,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (bars, events, meta)."""
    rng = np.random.default_rng(seed)
    symbols = [f"SYN{i}" for i in range(n_symbols)]
    dates = pd.bdate_range("2030-01-01", periods=n_steps + 1).strftime("%Y-%m-%d")

    # Regime path (market-wide).
    regime_idx = np.zeros(n_steps + 1, dtype=int)
    for t in range(1, n_steps + 1):
        regime_idx[t] = rng.choice(4, p=TRANSITION[regime_idx[t - 1]])

    # Common factor returns.
    factor = np.zeros(n_steps + 1)
    for t in range(1, n_steps + 1):
        drift, vol, _ = REGIME_PARAMS[REGIMES[regime_idx[t]]]
        factor[t] = drift + vol * rng.standard_normal()

    bar_rows, event_rows = [], []
    for s in symbols:
        anchor = start_price * float(rng.uniform(0.5, 2.0))
        prices = np.empty(n_steps + 1)
        prices[0] = anchor
        beta = factor_load * float(rng.uniform(0.7, 1.3))
        for t in range(1, n_steps + 1):
            drift, vol, kappa = REGIME_PARAMS[REGIMES[regime_idx[t]]]
            idio = drift + vol * rng.standard_normal()
            revert = kappa * (np.log(anchor) - np.log(prices[t - 1]))
            r = beta * factor[t] + idio + revert
            prices[t] = prices[t - 1] * np.exp(r)

        for t in range(1, n_steps + 1):
            o = prices[t - 1]
            c = prices[t]
            _, vol, _ = REGIME_PARAMS[REGIMES[regime_idx[t]]]
            hi = max(o, c) * (1 + abs(rng.normal(0, vol / 2)))
            lo = min(o, c) * (1 - abs(rng.normal(0, vol / 2)))
            crisis_mult = 2.0 if REGIMES[regime_idx[t]] == "crisis" else 1.0
            volume = float(rng.lognormal(11, 0.5)) * crisis_mult
            bar_rows.append(
                {
                    "ts": dates[t],
                    "symbol": s,
                    "open": round(float(o), 4),
                    "high": round(float(hi), 4),
                    "low": round(float(lo), 4),
                    "close": round(float(c), 4),
                    "volume": round(volume, 0),
                }
            )

    # Market-wide news at regime switches.
    for t in range(1, n_steps + 1):
        if regime_idx[t] != regime_idx[t - 1]:
            regime = REGIMES[regime_idx[t]]
            headline, sentiment = HEADLINES[regime]
            event_rows.append(
                {"ts": dates[t], "symbol": "", "headline": headline, "sentiment": sentiment}
            )

    bars = pd.DataFrame(bar_rows)
    events = pd.DataFrame(event_rows, columns=["ts", "symbol", "headline", "sentiment"])
    meta = {
        "builder": "synthetic",
        "seed": seed,
        "n_symbols": n_symbols,
        "n_steps": n_steps,
        "regimes": {dates[t]: REGIMES[regime_idx[t]] for t in range(1, n_steps + 1)},
        "instrument_kind": "equity",
    }
    return bars, events, meta
