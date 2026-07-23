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
    request_id: str = ""
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    visible_output_tokens: int = 0
    reasoning_tokens: int = 0
    attempts: int = 1
    retry_errors: tuple[str, ...] = ()


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

        model = AnthropicChatModel(model_key, spec)
        return _resilient(model)
    if spec.provider == "openai":
        from flock.agents.providers.openai_provider import OpenAIChatModel

        model = OpenAIChatModel(model_key, spec)
        return _resilient(model)
    if spec.provider == "google":
        from flock.agents.providers.google_provider import GoogleChatModel

        model = GoogleChatModel(model_key, spec)
        return _resilient(model)
    if spec.provider == "openai_compatible":
        from flock.agents.providers.openai_compatible import OpenAICompatibleChatModel

        model = OpenAICompatibleChatModel(model_key, spec)
        return _resilient(model)
    raise ValueError(f"unknown provider '{spec.provider}'")


def _resilient(model: ChatModel) -> ChatModel:
    from flock.agents.providers.resilient import ResilientChatModel

    return ResilientChatModel(model)
