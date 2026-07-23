"""Google Gemini adapter. Requires `uv sync --extra providers` and GEMINI_API_KEY."""

from __future__ import annotations

import importlib

from flock.agents.providers.base import ChatResponse
from flock.agents.providers.pricing import cost_usd
from flock.core.config import ModelSpec


class GoogleChatModel:
    def __init__(self, model_key: str, spec: ModelSpec, client=None):
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client

    def _get_client(self):
        if self._client is None:
            client_type = importlib.import_module("google.genai").Client
            self._client = client_type()
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        from google.genai import types

        resp = self._get_client().models.generate_content(
            model=self.model_id,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
                seed=seed,
            ),
        )
        usage = resp.usage_metadata
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        visible_output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        reasoning_tokens = getattr(usage, "thoughts_token_count", 0) or 0
        output_tokens = visible_output_tokens + reasoning_tokens
        return ChatResponse(
            text=resp.text or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd(self.model_id, input_tokens, output_tokens),
            request_id=str(getattr(resp, "response_id", "") or ""),
            visible_output_tokens=visible_output_tokens,
            reasoning_tokens=reasoning_tokens,
        )
