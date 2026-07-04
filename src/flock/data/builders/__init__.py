"""Dataset builder dispatch: `flock data build <builder>` lands here.

Network builders (equities, polymarket, kalshi, refs13f) import their
dependencies lazily so the offline pipeline never needs them.
"""

from __future__ import annotations

from pathlib import Path

from flock.data import schemas, synthetic
from flock.data.registry import DATASETS_DIR, DatasetEntry, Registry


def build(
    builder: str,
    name: str | None = None,
    seed: int = 42,
    start: str | None = None,
    end: str | None = None,
    symbols: list[str] | None = None,
) -> DatasetEntry:
    registry = Registry()

    if builder == "synthetic":
        name = name or "synthetic-equities-v1"
        bars, events, meta = synthetic.generate(seed=seed)
        params = {"seed": seed}
    elif builder == "equities":
        from flock.data.builders.equities_yfinance import build_equities

        name = name or "equities-daily"
        bars, events, meta = build_equities(symbols=symbols, start=start, end=end)
        params = {"symbols": symbols, "start": start, "end": end}
    elif builder == "polymarket":
        from flock.data.builders.polymarket import build_polymarket

        name = name or "polymarket-binary"
        bars, events, meta = build_polymarket(limit=len(symbols) if symbols else 20)
        params = {"limit": len(symbols) if symbols else 20}
    elif builder == "kalshi":
        from flock.data.builders.kalshi import build_kalshi

        name = name or "kalshi-binary"
        bars, events, meta = build_kalshi(series=symbols)
        params = {"series": symbols}
    elif builder == "refs13f":
        from flock.data.builders.real_world_refs import build_13f_panel

        name = name or "refs-13f-panel"
        return build_13f_panel(registry, name=name, quarters=4)
    else:
        raise ValueError(f"unknown builder '{builder}'")

    dataset_dir = _next_dir(name)
    schemas.write_dataset(dataset_dir, bars, events, meta)
    return registry.register(name, builder, dataset_dir, params)


def _next_dir(name: str) -> Path:
    base = DATASETS_DIR / name
    if not base.exists():
        return base
    i = 2
    while (DATASETS_DIR / f"{name}-v{i}").exists():
        i += 1
    return DATASETS_DIR / f"{name}-v{i}"
