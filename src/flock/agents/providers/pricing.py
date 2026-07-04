"""Per-model token pricing (USD per million tokens) for cost tracking.

Best-effort: unknown models cost 0 and the run manifest still records token
counts. Update alongside provider price changes; prices are matched by the
longest model-id prefix.
"""

from __future__ import annotations

# model-id prefix -> (input $/Mtok, output $/Mtok)
PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-opus": (15.0, 75.0),
    "gpt-5": (1.25, 10.0),
    "gpt-4o": (2.5, 10.0),
    "gemini-2.5-pro": (1.25, 10.0),
    "gemini-2.5-flash": (0.30, 2.5),
}


def cost_usd(model_id: str, input_tokens: int, output_tokens: int) -> float:
    best = ""
    for prefix in PRICES:
        if model_id.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    if not best:
        return 0.0
    p_in, p_out = PRICES[best]
    return (input_tokens * p_in + output_tokens * p_out) / 1e6
