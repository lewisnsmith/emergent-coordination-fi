"""ChatModel interface all providers implement, plus the dispatch factory.

Provider SDKs are imported lazily inside the factory so the offline pipeline
(mock models) never needs them installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from flock.core.config import ModelSpec


@dataclass(frozen=True)
class ChatResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class ChatModel(Protocol):
    model_key: str  # key in configs/models.yaml
    model_id: str

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse: ...


def make_chat_model(model_key: str, spec: ModelSpec) -> ChatModel:
    if spec.provider == "mock":
        from flock.agents.providers.mock import MockChatModel

        return MockChatModel(model_key, spec)
    if spec.provider == "anthropic":
        from flock.agents.providers.anthropic_provider import AnthropicChatModel

        return AnthropicChatModel(model_key, spec)
    if spec.provider == "openai":
        from flock.agents.providers.openai_provider import OpenAIChatModel

        return OpenAIChatModel(model_key, spec)
    if spec.provider == "google":
        from flock.agents.providers.google_provider import GoogleChatModel

        return GoogleChatModel(model_key, spec)
    if spec.provider == "openai_compatible":
        from flock.agents.providers.openai_compatible import OpenAICompatibleChatModel

        return OpenAICompatibleChatModel(model_key, spec)
    raise ValueError(f"unknown provider '{spec.provider}'")
