"""Parquet dataset schemas and IO helpers.

A dataset is a directory containing:
    bars.parquet    ts, symbol, open, high, low, close, volume
    events.parquet  ts, symbol, headline, sentiment      (optional)
    meta.json       builder params, instrument kinds, provenance
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BAR_COLUMNS = ["ts", "symbol", "open", "high", "low", "close", "volume"]
EVENT_COLUMNS = ["ts", "symbol", "headline", "sentiment"]


def write_dataset(
    path: Path,
    bars: pd.DataFrame,
    events: pd.DataFrame | None = None,
    meta: dict | None = None,
) -> int:
    """Write a dataset directory; returns bar row count."""
    path.mkdir(parents=True, exist_ok=True)
    bars = bars[BAR_COLUMNS].sort_values(["ts", "symbol"]).reset_index(drop=True)
    bars.to_parquet(path / "bars.parquet", index=False)
    if events is not None and len(events):
        events = events[EVENT_COLUMNS].sort_values("ts").reset_index(drop=True)
        events.to_parquet(path / "events.parquet", index=False)
    with open(path / "meta.json", "w") as f:
        json.dump(meta or {}, f, indent=2, default=str)
    return len(bars)


def read_bars(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path / "bars.parquet")[BAR_COLUMNS]


def read_events(path: Path) -> pd.DataFrame | None:
    p = path / "events.parquet"
    if not p.exists():
        return None
    return pd.read_parquet(p)[EVENT_COLUMNS]


def read_meta(path: Path) -> dict:
    p = path / "meta.json"
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)
