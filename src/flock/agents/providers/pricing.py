"""Runtime token pricing backed by the dated experiment pricing catalog."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

from flock.experiments.costs import PricingCatalog, load_pricing


@lru_cache(maxsize=4)
def _catalog(path: str) -> PricingCatalog:
    return load_pricing(Path(path))


def cost_usd(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    *,
    cached_input_tokens: int = 0,
    cache_write_tokens: int = 0,
    as_of: date | None = None,
    pricing_path: Path = Path("configs/budgets/pricing.yaml"),
) -> float:
    catalog = _catalog(str(pricing_path.resolve()))
    best = ""
    for prefix in catalog.api:
        if model_id.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    if not best:
        raise ValueError(f"no verified token price for metered model '{model_id}'")
    price = catalog.api[best]
    p_in, p_out = price.rates_on(as_of or date.today())
    ordinary_input = max(input_tokens - cached_input_tokens - cache_write_tokens, 0)
    cached_rate = price.cached_input_per_million_usd or p_in
    write_rate = p_in * price.cache_write_multiplier
    return (
        ordinary_input * p_in
        + cached_input_tokens * cached_rate
        + cache_write_tokens * write_rate
        + output_tokens * p_out
    ) / 1e6
