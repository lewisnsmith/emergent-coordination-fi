"""Strategy-level convergence: factor fingerprints and rationale similarity.

Fingerprint: regress each agent's per-(step,symbol) signed trade flow on
canonical signals computed from market data only (momentum, reversal,
MA-distance, volatility). The standardized coefficient vector is the agent's
strategy fingerprint; cohort dispersion = mean pairwise distance.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

import numpy as np
import pandas as pd

from flock.data import schemas

SIGNALS = ["momentum", "reversal", "ma_distance", "volatility"]


def compute_signals(bars: pd.DataFrame, lookback: int = 10) -> pd.DataFrame:
    """Per (ts, symbol) signal panel from bar data only."""
    frames = []
    for symbol, g in bars.sort_values("ts").groupby("symbol"):
        closes = g["close"].reset_index(drop=True)
        rets = closes.pct_change()
        df = pd.DataFrame(
            {
                "ts": g["ts"].to_numpy(),
                "symbol": symbol,
                "momentum": closes.pct_change(lookback),
                "reversal": -rets,
                "ma_distance": closes / closes.rolling(lookback).mean() - 1,
                "volatility": rets.rolling(lookback).std(),
            }
        )
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def trade_flows(decisions: pd.DataFrame) -> pd.DataFrame:
    """Per (agent, step, ts, symbol) signed order flow (clipped orders)."""
    rows = []
    for rec in decisions.itertuples():
        for o in rec.orders_clipped:
            signed = o["quantity"] if o["side"] == "buy" else -o["quantity"]
            rows.append(
                {"agent_id": rec.agent_id, "step": rec.step, "ts": rec.ts,
                 "symbol": o["symbol"], "flow": signed}
            )
    return pd.DataFrame(rows, columns=["agent_id", "step", "ts", "symbol", "flow"])


def fingerprint(
    decisions: pd.DataFrame, signals: pd.DataFrame, agents: list[str]
) -> pd.DataFrame:
    """agents x SIGNALS coefficient matrix (least squares, z-scored X and y)."""
    flows = trade_flows(decisions)
    steps = decisions[["step", "ts"]].drop_duplicates()
    symbols = sorted({s for ss in decisions["orders_clipped"] for s in
                      [o["symbol"] for o in ss]} | set(signals["symbol"].unique()))
    # full (step, symbol) grid so holds contribute zeros
    grid = steps.merge(pd.DataFrame({"symbol": symbols}), how="cross")
    grid = grid.merge(signals, on=["ts", "symbol"], how="left").dropna(subset=SIGNALS)

    out = {}
    for agent in agents:
        af = flows[flows["agent_id"] == agent][["step", "symbol", "flow"]]
        panel = grid.merge(af, on=["step", "symbol"], how="left").fillna({"flow": 0.0})
        x = panel[SIGNALS].to_numpy()
        y = panel["flow"].to_numpy()
        x = (x - x.mean(axis=0)) / np.where(x.std(axis=0) > 0, x.std(axis=0), 1.0)
        y_sd = y.std()
        y = (y - y.mean()) / (y_sd if y_sd > 0 else 1.0)
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        out[agent] = beta
    return pd.DataFrame(out, index=SIGNALS).T


def fingerprint_dispersion(fp: pd.DataFrame) -> float:
    """Mean pairwise Euclidean distance between fingerprints."""
    pairs = list(itertools.combinations(fp.index, 2))
    if not pairs:
        return float("nan")
    return float(
        np.mean([np.linalg.norm(fp.loc[a] - fp.loc[b]) for a, b in pairs])
    )


_TOKEN = re.compile(r"[a-z]{3,}")


def rationale_similarity(decisions: pd.DataFrame, agents: list[str]) -> float:
    """Mean pairwise cosine similarity of agents' rationale term vectors.

    Offline-friendly: hashing bag-of-words per agent (all rationales pooled).
    A sentence-embedding model can replace this without changing callers.
    """
    dim = 512
    vectors = {}
    for agent in agents:
        texts = decisions.loc[decisions["agent_id"] == agent, "rationale"]
        v = np.zeros(dim)
        for text in texts:
            for tok in _TOKEN.findall(str(text).lower()):
                v[hash(tok) % dim] += 1.0
        n = np.linalg.norm(v)
        vectors[agent] = v / n if n > 0 else v
    pairs = list(itertools.combinations(agents, 2))
    if not pairs:
        return float("nan")
    return float(np.mean([float(vectors[a] @ vectors[b]) for a, b in pairs]))


def strategy_metrics(run: dict, cohort: str, dataset_dir: Path) -> dict[str, float]:
    decisions = run["decisions"]
    agents = sorted(decisions.loc[decisions["cohort"] == cohort, "agent_id"].unique())
    signals = compute_signals(schemas.read_bars(dataset_dir))
    fp = fingerprint(decisions, signals, agents)
    return {
        "fingerprint_dispersion": fingerprint_dispersion(fp),
        "rationale_similarity": rationale_similarity(decisions, agents),
    }
