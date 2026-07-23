"""OpenAI adapter. Requires `uv sync --extra providers` and OPENAI_API_KEY."""

from __future__ import annotations

from flock.agents.providers.base import ChatResponse
from flock.agents.providers.pricing import cost_usd
from flock.core.config import ModelSpec


class OpenAIChatModel:
    def __init__(self, model_key: str, spec: ModelSpec, client=None):
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI()
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        # Frontier GPT releases use the Responses API. It has no seed field;
        # reproducibility is preserved by full request hashing and response cache.
        resp = self._get_client().responses.create(
            model=self.model_id,
            instructions=system,
            input=user,
            temperature=temperature,
            max_output_tokens=max_tokens,
            store=False,
        )
        usage = resp.usage
        return ChatResponse(
            text=resp.output_text or "",
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
            cost_usd=cost_usd(
                self.model_id,
                usage.input_tokens if usage else 0,
                usage.output_tokens if usage else 0,
            ),
        )
