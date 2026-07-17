"""Per-model token pricing (USD per million tokens) for cost tracking.

Best-effort: unknown models cost 0 and the run manifest still records token
counts. Update alongside provider price changes; prices are matched by the
longest model-id prefix.
"""

from __future__ import annotations

# Synchronous standard-tier prices verified against official provider pages on
# 2026-07-13. Preflight estimates use configs/budgets/pricing.yaml. Unknown
# metered models fail closed instead of silently being recorded as free.
# model-id prefix -> (input $/Mtok, output $/Mtok)
PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "gpt-5.6-sol": (5.0, 30.0),
    "gpt-5.6-terra": (2.5, 15.0),
    "gemini-3.1-pro-preview": (2.0, 12.0),
}


def cost_usd(model_id: str, input_tokens: int, output_tokens: int) -> float:
    best = ""
    for prefix in PRICES:
        if model_id.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    if not best:
        raise ValueError(f"no verified token price for metered model '{model_id}'")
    p_in, p_out = PRICES[best]
    return (input_tokens * p_in + output_tokens * p_out) / 1e6
