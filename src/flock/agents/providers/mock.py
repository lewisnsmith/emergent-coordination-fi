"""Deterministic mock LLM for offline runs and metric calibration.

The mock reads the machine-readable observation block that LLMAgent embeds in
every prompt, applies a simple behavior rule, and answers in the same JSON
format a real model is asked for — so it exercises the full parse path.

Behaviors:
    momentum    buy the strongest recent gainer, sell held losers (convergent cohort)
    contrarian  the reverse
    random      seeded coin flips (chance-floor cohort)
    hold        never trades

`noise` flips each decision to a random one with the given probability,
deterministically per (prompt, seed).
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from flock.agents.providers.base import ChatResponse
from flock.core.config import ModelSpec

OBS_MARKER = "## OBSERVATION_JSON"


def extract_observation(user_prompt: str) -> dict:
    idx = user_prompt.find(OBS_MARKER)
    if idx < 0:
        raise ValueError("mock provider requires the OBSERVATION_JSON block in the prompt")
    payload = user_prompt[idx + len(OBS_MARKER):].strip()
    payload = payload[: payload.index("\n## ")] if "\n## " in payload else payload
    return json.loads(payload)


class MockChatModel:
    def __init__(self, model_key: str, spec: ModelSpec):
        self.model_key = model_key
        self.model_id = spec.model_id
        self.behavior = spec.behavior or "random"
        self.noise = spec.noise

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        obs = extract_observation(user)
        digest = hashlib.sha256(f"{user}|{seed}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))

        behavior = self.behavior
        if self.noise and rng.random() < self.noise:
            behavior = "random"

        orders = self._decide(behavior, obs, rng)
        text = json.dumps({"orders": orders, "rationale": f"mock {behavior} rule"})
        return ChatResponse(text=text)

    def _decide(self, behavior: str, obs: dict, rng: np.random.Generator) -> list[dict]:
        if behavior == "hold":
            return []
        prices: dict[str, float] = obs["prices"]
        returns: dict[str, float] = obs["recent_returns"]
        positions: dict[str, float] = obs["portfolio"]["positions"]
        equity: float = obs["portfolio"]["equity"]

        def qty(symbol: str, frac: float = 0.05) -> float:
            return round(equity * frac / prices[symbol], 4)

        if behavior == "random":
            orders = []
            for s in prices:
                if rng.random() < 0.4:
                    continue
                if rng.random() < 0.5:
                    orders.append({"symbol": s, "side": "buy", "quantity": qty(s)})
                elif positions.get(s, 0) > 0:
                    q = min(qty(s), positions[s])
                    orders.append({"symbol": s, "side": "sell", "quantity": q})
            return orders

        ranked = sorted(returns, key=lambda symbol: returns[symbol])  # ascending
        weakest, strongest = ranked[0], ranked[-1]
        buy, sell = (
            (strongest, weakest) if behavior == "momentum" else (weakest, strongest)
        )
        orders = [{"symbol": buy, "side": "buy", "quantity": qty(buy)}]
        if positions.get(sell, 0) > 0:
            q = min(qty(sell), positions[sell])
            orders.append({"symbol": sell, "side": "sell", "quantity": q})
        return orders
