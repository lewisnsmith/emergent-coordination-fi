"""LLM trading agent: prompt assembly, response parsing, retry discipline.

Parse rule (pre-registered, see docs/research/06-preregistration.md): a
malformed response is retried once with a format reminder; if still malformed
the step is scored as hold with parse_ok=False.
"""

from __future__ import annotations

import json
import time

from flock.agents.cache import ResponseCache
from flock.agents.providers.base import ChatModel, ChatResponse
from flock.agents.providers.mock import OBS_MARKER
from flock.core.config import PersonaConfig
from flock.core.types import Decision, Observation, Order, Usage

TASK_FRAME = """
You are a trading agent managing a portfolio. Each step you receive current
market data and your portfolio, and you decide what to trade. You may buy or
sell any listed symbol, or do nothing. Be decisive but manage risk according
to your mandate. Long-only: you cannot sell more than you hold.
"""

RESPONSE_INSTRUCTIONS = """
## RESPONSE FORMAT
Respond with ONLY a JSON object, no other text:
{"orders": [{"symbol": "...", "side": "buy"|"sell", "quantity": <number>,
"limit_price": <number or null>}], "rationale": "<one or two sentences>"}
An empty orders list means hold.
"""

RETRY_REMINDER = (
    "\nYour previous reply was not valid JSON in the required format. "
    "Reply with ONLY the JSON object."
)


def render_observation_json(obs: Observation) -> str:
    """Compact machine-readable block embedded in every prompt (also what the
    deterministic mock provider reads)."""
    lookback = 5
    payload = {
        "ts": obs.ts,
        "prices": {s: obs.prices[s] for s in obs.symbols},
        "recent_returns": {
            s: round(
                obs.bars[s][-1].close
                / obs.bars[s][max(-len(obs.bars[s]), -1 - lookback)].close
                - 1,
                6,
            )
            for s in obs.symbols
        },
        "history_closes": {s: [b.close for b in obs.bars[s]] for s in obs.symbols},
        "news": [
            {"symbol": n.symbol or "MARKET", "headline": n.headline} for n in obs.news
        ],
        "portfolio": {
            "cash": round(obs.portfolio.cash, 2),
            "equity": round(obs.portfolio.equity, 2),
            "positions": {
                p.symbol: p.quantity for p in obs.portfolio.positions if p.quantity
            },
        },
    }
    return json.dumps(payload)


def render_user_prompt(obs: Observation) -> str:
    lines = [f"Date: {obs.ts}", "", "Market snapshot:"]
    for s in obs.symbols:
        last = obs.bars[s][-1]
        lines.append(f"  {s}: close {last.close}, volume {last.volume:.0f}")
    if obs.news:
        lines.append("News:")
        lines.extend(f"  - [{n.symbol or 'MARKET'}] {n.headline}" for n in obs.news)
    lines.append(f"Cash: {obs.portfolio.cash:.2f}  Equity: {obs.portfolio.equity:.2f}")
    if obs.portfolio.positions:
        lines.append("Positions:")
        lines.extend(
            f"  {p.symbol}: {p.quantity} @ avg {p.avg_price:.2f}"
            for p in obs.portfolio.positions
        )
    lines.append("")
    lines.append(OBS_MARKER)
    lines.append(render_observation_json(obs))
    lines.append(RESPONSE_INSTRUCTIONS)
    return "\n".join(lines)


def parse_response(
    text: str, valid_symbols: tuple[str, ...]
) -> tuple[tuple[Order, ...], str] | None:
    """Return (orders, rationale) or None if malformed."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.index("{"):] if "{" in text else text
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
        orders = []
        for o in payload.get("orders", []):
            symbol, side = o["symbol"], o["side"]
            quantity = float(o["quantity"])
            limit = o.get("limit_price")
            if symbol not in valid_symbols or side not in ("buy", "sell") or quantity <= 0:
                return None
            orders.append(
                Order(symbol, side, quantity, float(limit) if limit is not None else None)
            )
        return tuple(orders), str(payload.get("rationale", ""))
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return None


class LLMAgent:
    kind = "llm"

    def __init__(
        self,
        agent_id: str,
        cohort: str,
        chat_model: ChatModel,
        persona: PersonaConfig,
        temperature: float = 0.7,
        seed: int = 0,
        max_tokens: int = 1024,
        memory: bool = False,
        cache: ResponseCache | None = None,
    ):
        self.agent_id = agent_id
        self.cohort = cohort
        self.chat_model = chat_model
        self.persona = persona
        self.temperature = temperature
        self.seed = seed
        self.max_tokens = max_tokens
        self.memory = memory
        self.cache = cache
        self._memory_log: list[str] = []

    def describe(self) -> dict:
        return {
            "kind": self.kind,
            "model": self.chat_model.model_key,
            "model_id": self.chat_model.model_id,
            "persona": self.persona.name,
            "temperature": self.temperature,
            "memory": self.memory,
            "seed": self.seed,
        }

    @property
    def system_prompt(self) -> str:
        return f"{self.persona.system_prompt.strip()}\n{TASK_FRAME.strip()}"

    def _complete(self, user: str) -> ChatResponse:
        if self.cache is not None:
            key = ResponseCache.key(
                self.chat_model.model_key, self.chat_model.model_id, self.temperature,
                self.seed, self.max_tokens, self.system_prompt, user,
            )
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        response = self.chat_model.complete(
            self.system_prompt, user,
            temperature=self.temperature, seed=self.seed, max_tokens=self.max_tokens,
        )
        if self.cache is not None:
            self.cache.put(key, response)
        return response

    def decide(self, obs: Observation) -> Decision:
        user = render_user_prompt(obs)
        if self.memory and self._memory_log:
            recent = "\n".join(self._memory_log[-5:])
            user = f"Your recent decisions:\n{recent}\n\n{user}"

        t0 = time.perf_counter()
        response = self._complete(user)
        parsed = parse_response(response.text, obs.symbols)
        usage = Usage(response.input_tokens, response.output_tokens, response.cost_usd)

        if parsed is None:
            retry = self._complete(user + RETRY_REMINDER)
            usage = Usage(
                usage.input_tokens + retry.input_tokens,
                usage.output_tokens + retry.output_tokens,
                usage.cost_usd + retry.cost_usd,
            )
            parsed = parse_response(retry.text, obs.symbols)

        latency = time.perf_counter() - t0
        if parsed is None:
            return Decision(
                self.agent_id, obs.step, (), rationale="", parse_ok=False,
                usage=usage, latency_s=latency,
            )
        orders, rationale = parsed
        if self.memory:
            summary = ", ".join(f"{o.side} {o.quantity} {o.symbol}" for o in orders) or "hold"
            self._memory_log.append(f"[{obs.ts}] {summary}")
        return Decision(
            self.agent_id, obs.step, orders, rationale=rationale,
            usage=usage, latency_s=latency,
        )
