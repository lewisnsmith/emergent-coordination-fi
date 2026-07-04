"""Generic OpenAI-compatible endpoint adapter (Ollama, vLLM, OpenRouter, ...).

Configure via OPENAI_COMPATIBLE_BASE_URL / OPENAI_COMPATIBLE_API_KEY.
"""

from __future__ import annotations

import os

from flock.agents.providers.base import ChatResponse
from flock.core.config import ModelSpec


class OpenAICompatibleChatModel:
    def __init__(self, model_key: str, spec: ModelSpec, client=None):
        self.model_key = model_key
        self.model_id = spec.model_id
        self._client = client

    def _get_client(self):
        if self._client is None:
            base_url = os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
            if not base_url:
                raise RuntimeError(
                    "set OPENAI_COMPATIBLE_BASE_URL (e.g. http://localhost:11434/v1 for Ollama)"
                )
            from openai import OpenAI

            self._client = OpenAI(
                base_url=base_url,
                api_key=os.environ.get("OPENAI_COMPATIBLE_API_KEY", "none"),
            )
        return self._client

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        resp = self._get_client().chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
        )
        usage = resp.usage
        return ChatResponse(
            text=resp.choices[0].message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            cost_usd=0.0,  # local/self-hosted endpoints: no metered price
        )
