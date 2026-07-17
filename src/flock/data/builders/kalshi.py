"""Kalshi settled binary markets -> daily bar datasets (public API v2)."""

from __future__ import annotations

from datetime import date, datetime
from typing import cast

import httpx
import pandas as pd

API = "https://api.elections.kalshi.com/trade-api/v2"
type TimestampInput = str | date | datetime | pd.Timestamp


def build_kalshi(
    series: list[str] | None = None, limit: int = 20
) -> tuple[pd.DataFrame, pd.DataFrame | None, dict]:
    with httpx.Client(timeout=30, headers={"accept": "application/json"}) as client:
        params: dict = {"status": "settled", "limit": 200}
        if series:
            params["series_ticker"] = series[0]
        markets = client.get(f"{API}/markets", params=params).json().get("markets", [])
        frames, contracts = [], []
        for m in markets:
            ticker = m.get("ticker", "")
            result = m.get("result", "")
            if result not in ("yes", "no"):
                continue
            candles = _fetch_candles(client, m)
            bars = candles_to_bars(candles, "KX-" + ticker, 1.0 if result == "yes" else 0.0)
            if bars is None or len(bars) < 15:
                continue
            frames.append(bars)
            contracts.append(
                {"symbol": "KX-" + ticker, "title": m.get("title", ""), "result": result}
            )
            if len(frames) >= limit:
                break
    if not frames:
        raise RuntimeError("no usable settled Kalshi markets found")
    meta = {
        "builder": "kalshi",
        "instrument_kind": "binary",
        "contracts": contracts,
        "source": "Kalshi public API v2",
    }
    return pd.concat(frames, ignore_index=True), None, meta


def _fetch_candles(client: httpx.Client, market: dict) -> list[dict]:
    series_ticker = market.get("event_ticker", "").split("-")[0]
    ticker = market["ticker"]
    open_time = cast(pd.Timestamp, pd.Timestamp(cast(TimestampInput, market["open_time"])))
    close_time = cast(
        pd.Timestamp, pd.Timestamp(cast(TimestampInput, market["close_time"]))
    )
    open_ts = int(open_time.timestamp())
    close_ts = int(close_time.timestamp())
    resp = client.get(
        f"{API}/series/{series_ticker}/markets/{ticker}/candlesticks",
        params={"start_ts": open_ts, "end_ts": close_ts, "period_interval": 1440},
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("candlesticks", [])


def candles_to_bars(
    candles: list[dict], symbol: str, resolution: float
) -> pd.DataFrame | None:
    """Pure transform: Kalshi candlesticks (cents) -> bars in (0,1), settled."""
    rows = []
    for c in candles:
        price = c.get("price", {})
        close_c = price.get("close")
        if close_c is None:
            continue
        rows.append(
            {
                "ts": pd.Timestamp(c["end_period_ts"], unit="s").strftime("%Y-%m-%d"),
                "symbol": symbol,
                "open": (price.get("open") or close_c) / 100.0,
                "high": (price.get("high") or close_c) / 100.0,
                "low": (price.get("low") or close_c) / 100.0,
                "close": close_c / 100.0,
                "volume": float(c.get("volume", 0) or 0),
            }
        )
    if not rows:
        return None
    bars = pd.DataFrame(rows).drop_duplicates(subset="ts", keep="last")
    bars.loc[bars.index[-1], "close"] = resolution
    bars.loc[bars.index[-1], "high"] = max(bars.iloc[-1]["high"], resolution)
    bars.loc[bars.index[-1], "low"] = min(bars.iloc[-1]["low"], resolution)
    return bars.reset_index(drop=True)
