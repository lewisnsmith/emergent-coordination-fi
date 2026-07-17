"""US equities daily bars via yfinance (`uv sync --extra data`)."""

from __future__ import annotations

from collections.abc import Hashable
from datetime import date, datetime
from typing import SupportsFloat, cast

import pandas as pd

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM"]


def build_equities(
    symbols: list[str] | None, start: str | None, end: str | None
) -> tuple[pd.DataFrame, pd.DataFrame | None, dict]:
    import yfinance as yf

    symbols = symbols or DEFAULT_SYMBOLS
    if not (start and end):
        raise ValueError("equities builder requires --start and --end (YYYY-MM-DD)")
    raw = yf.download(
        symbols, start=start, end=end, auto_adjust=True, group_by="ticker", progress=False
    )
    bars = flatten_yfinance(raw, symbols)
    meta = {
        "builder": "equities",
        "symbols": symbols,
        "start": start,
        "end": end,
        "instrument_kind": "equity",
        "source": "yfinance (research use; raw vendor data not redistributed)",
    }
    return bars, None, meta


def flatten_yfinance(raw: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    """Pure transform: yfinance multi-ticker frame -> flock bar schema."""
    rows = []
    for s in symbols:
        df = cast(pd.DataFrame, raw[s]) if len(symbols) > 1 else raw
        required = cast(list[Hashable], ["Open", "High", "Low", "Close"])
        df = df.dropna(subset=required)
        for ts, r in df.iterrows():
            rows.append(
                {
                    "ts": pd.Timestamp(
                        cast(str | date | datetime | pd.Timestamp, ts)
                    ).strftime("%Y-%m-%d"),
                    "symbol": s,
                    "open": float(cast(SupportsFloat, r["Open"])),
                    "high": float(cast(SupportsFloat, r["High"])),
                    "low": float(cast(SupportsFloat, r["Low"])),
                    "close": float(cast(SupportsFloat, r["Close"])),
                    "volume": float(cast(SupportsFloat, r.get("Volume", 0.0) or 0.0)),
                }
            )
    if not rows:
        raise ValueError("yfinance returned no data for the requested symbols/window")
    return pd.DataFrame(rows)
