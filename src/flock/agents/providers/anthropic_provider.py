"""Anthropic adapter. Requires `uv sync --extra providers` and ANTHROPIC_API_KEY."""

from __future__ import annotations

from flock.agents.providers.base import ChatResponse
from flock.agents.providers.pricing import cost_usd
from flock.core.config import ModelSpec


def _text_content(block: object) -> str:
    """Extract only Anthropic text blocks across evolving SDK union types."""
    if getattr(block, "type", None) != "text":
        return ""
    value = getattr(block, "text", None)
    return value if isinstance(value, str) else ""


class AnthropicChatModel:
    def __init__(self, model_key: str, spec: ModelSpec, client=None):
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        # Anthropic has no seed parameter; determinism comes from the response cache.
        msg = self._get_client().messages.create(
            model=self.model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(_text_content(block) for block in msg.content)
        return ChatResponse(
            text=text,
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
            cost_usd=cost_usd(self.model_id, msg.usage.input_tokens, msg.usage.output_tokens),
        )
