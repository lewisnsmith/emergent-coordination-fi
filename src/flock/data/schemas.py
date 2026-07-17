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
BINARY_CONTRACT_FIELDS = {
    "symbol",
    "question",
    "rules",
    "open_ts",
    "close_ts",
    "resolution",
    "yes_label",
    "no_label",
    "price_semantics",
}


def validate_binary_contracts(bars: pd.DataFrame, meta: dict) -> None:
    """Require reconstructable YES-price semantics and contract lifetimes.

    The last bar for each contract is a settlement payload, not a tradable
    observation.  Replay removes that bar from the agent-visible history and
    applies its frozen binary payout at ``close_ts``.  Validating that payload
    here prevents an ambiguous terminal price from entering an experiment.
    """
    contracts = meta.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        raise ValueError("binary datasets require nonempty contract metadata")
    by_symbol: dict[str, dict] = {}
    for contract in contracts:
        if not isinstance(contract, dict) or not BINARY_CONTRACT_FIELDS.issubset(contract):
            raise ValueError("binary contract metadata is incomplete")
        symbol = str(contract["symbol"])
        if symbol in by_symbol:
            raise ValueError(f"duplicate binary contract metadata for {symbol}")
        if not str(contract["question"]).strip() or not str(contract["rules"]).strip():
            raise ValueError(f"binary question and rules must be nonempty for {symbol}")
        if str(contract["yes_label"]).strip().casefold() != "yes":
            raise ValueError(f"binary YES label is ambiguous for {symbol}")
        if str(contract["no_label"]).strip().casefold() != "no":
            raise ValueError(f"binary NO label is ambiguous for {symbol}")
        resolution = float(contract["resolution"])
        if resolution not in {0.0, 1.0}:
            raise ValueError(f"binary resolution must be zero or one for {symbol}")
        if contract["price_semantics"] != "YES probability in [0,1]":
            raise ValueError(f"unsupported binary price semantics for {symbol}")
        try:
            open_ts = pd.Timestamp(pd.to_datetime(contract["open_ts"], utc=True))
            close_ts = pd.Timestamp(pd.to_datetime(contract["close_ts"], utc=True))
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid binary contract timestamps for {symbol}") from error
        if pd.isna(open_ts) or pd.isna(close_ts):
            raise ValueError(f"invalid binary contract timestamps for {symbol}")
        open_ts = cast(pd.Timestamp, open_ts)
        close_ts = cast(pd.Timestamp, close_ts)
        if open_ts > close_ts:
            raise ValueError(f"binary contract opens after it closes: {symbol}")
        by_symbol[symbol] = contract
    symbols = set(cast(pd.Series, bars["symbol"]).astype(str))
    if symbols != set(by_symbol):
        raise ValueError("binary contract metadata must exactly match bar symbols")
    for symbol, group in bars.groupby("symbol", sort=False):
        contract = by_symbol[str(symbol)]
        try:
            bar_times = pd.to_datetime(group["ts"], utc=True)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid binary bar timestamps for {symbol}") from error
        if bar_times.isna().any():
            raise ValueError(f"invalid binary bar timestamps for {symbol}")
        open_at = cast(
            pd.Timestamp, pd.to_datetime(str(contract["open_ts"]), utc=True)
        )
        close_at = cast(
            pd.Timestamp, pd.to_datetime(str(contract["close_ts"]), utc=True)
        )
        if (bar_times < open_at).any() or (bar_times > close_at).any():
            raise ValueError(f"binary bars fall outside the contract lifetime for {symbol}")
        ordered = group.assign(_parsed_ts=bar_times).sort_values("_parsed_ts")
        terminal_close = float(ordered.iloc[-1]["close"])
        resolution = float(contract["resolution"])
        if not np.isclose(terminal_close, resolution, rtol=0.0, atol=1e-12):
            raise ValueError(
                f"terminal binary bar must equal the resolution payout for {symbol}"
            )


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
    instrument_kind = (meta or {}).get("instrument_kind")
    if not np.isfinite(prices.to_numpy()).all():
        raise ValueError("bar prices must be finite")
    if instrument_kind == "binary":
        if not ((prices >= 0) & (prices <= 1)).all().all():
            raise ValueError("binary YES prices must remain in [0,1]")
        validate_binary_contracts(bars, meta or {})
    elif not (prices > 0).all().all():
        raise ValueError("bar prices must be positive")
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
