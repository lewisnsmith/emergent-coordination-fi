"""US equities daily bars via yfinance (`uv sync --extra data`)."""

from __future__ import annotations

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
        df = raw[s] if len(symbols) > 1 else raw
        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        for ts, r in df.iterrows():
            rows.append(
                {
                    "ts": pd.Timestamp(ts).strftime("%Y-%m-%d"),
                    "symbol": s,
                    "open": float(r["Open"]),
                    "high": float(r["High"]),
                    "low": float(r["Low"]),
                    "close": float(r["Close"]),
                    "volume": float(r.get("Volume", 0.0) or 0.0),
                }
            )
    if not rows:
        raise ValueError("yfinance returned no data for the requested symbols/window")
    return pd.DataFrame(rows)
