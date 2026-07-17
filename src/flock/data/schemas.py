"""Parquet dataset schemas and IO helpers.

A dataset is a directory containing:
    bars.parquet    ts, symbol, open, high, low, close, volume
    events.parquet  ts, symbol, headline, sentiment      (optional)
    meta.json       builder params, instrument kinds, provenance
"""

from __future__ import annotations

import json
from collections.abc import Hashable
from pathlib import Path
from typing import cast

import numpy as np
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
    bar_columns = cast(list[Hashable], BAR_COLUMNS)
    sort_columns = cast(list[Hashable], ["ts", "symbol"])
    bars = cast(pd.DataFrame, bars.loc[:, bar_columns])
    bars = bars.sort_values(by=sort_columns).reset_index(drop=True)
    if bars.duplicated(["ts", "symbol"]).any():
        raise ValueError("bars contain duplicate (ts, symbol) rows")
    prices = bars[["open", "high", "low", "close"]]
    if not np.isfinite(prices.to_numpy()).all() or not (prices > 0).all().all():
        raise ValueError("bar prices must be finite and positive")
    if not (
        (bars["high"] >= prices[["open", "close", "low"]].max(axis=1))
        & (bars["low"] <= prices[["open", "close", "high"]].min(axis=1))
    ).all():
        raise ValueError("bar OHLC bounds are inconsistent")
    bars.to_parquet(path / "bars.parquet", index=False)
    if events is not None and len(events):
        event_columns = cast(list[Hashable], EVENT_COLUMNS)
        events = cast(pd.DataFrame, events.loc[:, event_columns])
        events = events.sort_values(by="ts").reset_index(drop=True)
        if events.isna().any().any():
            raise ValueError("events contain missing required values")
        events.to_parquet(path / "events.parquet", index=False)
    with open(path / "meta.json", "w") as f:
        json.dump(meta or {}, f, indent=2, default=str)
    return len(bars)


def read_bars(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path / "bars.parquet")
    return cast(pd.DataFrame, frame.loc[:, cast(list[Hashable], BAR_COLUMNS)])


def read_events(path: Path) -> pd.DataFrame | None:
    p = path / "events.parquet"
    if not p.exists():
        return None
    frame = pd.read_parquet(p)
    return cast(pd.DataFrame, frame.loc[:, cast(list[Hashable], EVENT_COLUMNS)])


def read_meta(path: Path) -> dict:
    p = path / "meta.json"
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)
