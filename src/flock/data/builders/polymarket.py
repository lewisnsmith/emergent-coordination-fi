"""Polymarket resolved binary markets -> daily bar datasets.

Uses the public Gamma API for market metadata and the CLOB prices-history
endpoint for the YES-token price path. By convention (see markets/instruments)
the final bar closes at the resolution payout.
"""

from __future__ import annotations

import json

import httpx
import pandas as pd

GAMMA_URL = "https://gamma-api.polymarket.com/markets"
CLOB_HISTORY_URL = "https://clob.polymarket.com/prices-history"


def build_polymarket(limit: int = 20) -> tuple[pd.DataFrame, pd.DataFrame | None, dict]:
    with httpx.Client(timeout=30) as client:
        markets = client.get(
            GAMMA_URL,
            params={
                "closed": "true",
                "limit": limit * 3,  # some markets lack usable histories
                "order": "volumeNum",
                "ascending": "false",
            },
        ).json()
        frames, contracts = [], []
        for m in markets:
            parsed = parse_market(m)
            if parsed is None:
                continue
            symbol, token_id, resolution = parsed
            hist = client.get(
                CLOB_HISTORY_URL,
                params={"market": token_id, "interval": "max", "fidelity": 1440},
            ).json()
            bars = history_to_bars(hist.get("history", []), symbol, resolution)
            if bars is None or len(bars) < 15:
                continue
            frames.append(bars)
            contracts.append(
                {"symbol": symbol, "question": m.get("question", ""), "resolution": resolution}
            )
            if len(frames) >= limit:
                break
    if not frames:
        raise RuntimeError("no usable resolved Polymarket markets found")
    meta = {
        "builder": "polymarket",
        "instrument_kind": "binary",
        "contracts": contracts,
        "source": "Polymarket Gamma/CLOB public APIs",
    }
    return pd.concat(frames, ignore_index=True), None, meta


def parse_market(m: dict) -> tuple[str, str, float] | None:
    """Pure transform: Gamma market record -> (symbol, yes_token_id, resolution)."""
    try:
        outcomes = json.loads(m["outcomes"]) if isinstance(m["outcomes"], str) else m["outcomes"]
        prices = (
            json.loads(m["outcomePrices"])
            if isinstance(m["outcomePrices"], str)
            else m["outcomePrices"]
        )
        tokens = (
            json.loads(m["clobTokenIds"])
            if isinstance(m["clobTokenIds"], str)
            else m["clobTokenIds"]
        )
    except (KeyError, json.JSONDecodeError, TypeError):
        return None
    if not (outcomes and prices and tokens) or len(outcomes) != 2:
        return None
    yes_idx = 0 if str(outcomes[0]).lower() == "yes" else 1
    resolution = round(float(prices[yes_idx]))
    slug = (m.get("slug") or m.get("question", "mkt")).strip()
    symbol = "PM-" + "".join(c for c in slug.upper() if c.isalnum() or c == "-")[:24]
    return symbol, str(tokens[yes_idx]), float(resolution)


def history_to_bars(
    history: list[dict], symbol: str, resolution: float
) -> pd.DataFrame | None:
    """Pure transform: CLOB {t, p} points -> daily bars ending at resolution."""
    if not history:
        return None
    df = pd.DataFrame(history)
    if not {"t", "p"}.issubset(df.columns):
        return None
    df["ts"] = pd.to_datetime(df["t"], unit="s").dt.strftime("%Y-%m-%d")
    daily = df.groupby("ts")["p"].agg(["first", "max", "min", "last"]).reset_index()
    bars = pd.DataFrame(
        {
            "ts": daily["ts"],
            "symbol": symbol,
            "open": daily["first"].astype(float),
            "high": daily["max"].astype(float),
            "low": daily["min"].astype(float),
            "close": daily["last"].astype(float),
            "volume": 0.0,
        }
    )
    # settle: final close snaps to the resolution payout
    bars.loc[bars.index[-1], ["close"]] = resolution
    bars.loc[bars.index[-1], "high"] = max(bars.iloc[-1]["high"], resolution)
    bars.loc[bars.index[-1], "low"] = min(bars.iloc[-1]["low"], resolution)
    return bars
