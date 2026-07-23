"""Provider adapters, tested with injected fake clients (no SDKs required)."""

import sys
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest

from flock.agents.providers.anthropic_provider import AnthropicChatModel
from flock.agents.providers.openai_compatible import OpenAICompatibleChatModel
from flock.agents.providers.openai_provider import OpenAIChatModel
from flock.agents.providers.pricing import cost_usd
from flock.agents.providers.resilient import (
    ResilientChatModel,
    RetryPolicy,
    is_retryable_provider_error,
)
from flock.core.config import ModelSpec

KW = {"temperature": 0.5, "seed": 1, "max_tokens": 100}


def test_pricing_prefix_match():
    assert cost_usd("claude-sonnet-5", 1_000_000, 0) == 2.0
    assert cost_usd("gpt-5.6-sol", 0, 1_000_000) == 30.0
    with pytest.raises(ValueError, match="no verified token price"):
        cost_usd("totally-unknown", 1_000_000, 1_000_000)


def test_anthropic_adapter_parses_response():
    calls = {}

    def create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(
            content=[
                SimpleNamespace(type="thinking", thinking="internal"),
                SimpleNamespace(type="text", text='{"orders": []}'),
            ],
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        )

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    spec = ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    model = AnthropicChatModel("claude-sonnet", spec, client=client)
    resp = model.complete("sys", "user", **KW)
    assert resp.text == '{"orders": []}'
    assert calls["system"] == "sys"
    assert calls["temperature"] == 0.5
    assert resp.cost_usd == pytest.approx((100 * 2.0 + 20 * 10.0) / 1e6)


def _openai_fake_client(calls: dict):
    def create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
        )

    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )


def _responses_fake_client(calls: dict):
    def create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(
            output_text="ok",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def test_openai_adapter_passes_seed():
    calls = {}
    spec = ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    model = OpenAIChatModel("gpt-terra-frontier", spec, client=_responses_fake_client(calls))
    resp = model.complete("sys", "user", **KW)
    assert resp.text == "ok"
    assert "seed" not in calls
    assert calls["instructions"] == "sys"
    assert calls["input"] == "user"
    assert calls["store"] is False


def test_openai_compatible_requires_base_url(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_BASE_URL", raising=False)
    spec = ModelSpec(provider="openai_compatible", model_id="llama3.3:70b")
    model = OpenAICompatibleChatModel("local", spec)
    with pytest.raises(RuntimeError, match="OPENAI_COMPATIBLE_BASE_URL"):
        model.complete("sys", "user", **KW)


def test_openai_compatible_with_injected_client():
    calls = {}
    spec = ModelSpec(provider="openai_compatible", model_id="llama3.3:70b")
    model = OpenAICompatibleChatModel("local", spec, client=_openai_fake_client(calls))
    resp = model.complete("sys", "user", **KW)
    assert resp.text == "ok" and resp.cost_usd == 0.0


def test_resilient_provider_retries_with_deterministic_schedule():
    calls = []

    class Flaky:
        model_key = "m"
        model_id = "mid"

        def complete(self, system, user, **kwargs):
            calls.append((system, user, kwargs))
            if len(calls) < 3:
                raise TimeoutError("temporary")
            from flock.agents.providers.base import ChatResponse

            return ChatResponse(text="ok")

    delays = []
    model = ResilientChatModel(
        Flaky(), RetryPolicy(max_attempts=3, initial_delay_s=0.25), sleeper=delays.append
    )
    response = model.complete("s", "u", **KW)
    assert response.text == "ok"
    assert response.attempts == 3
    assert len(response.retry_errors) == 2
    assert delays == [0.25, 0.5]


def test_resilient_provider_does_not_retry_deterministic_error():
    class Invalid:
        model_key = "m"
        model_id = "mid"

        def complete(self, *_args, **_kwargs):
            raise ValueError("invalid request")

    delays = []
    model = ResilientChatModel(Invalid(), sleeper=delays.append)
    with pytest.raises(ValueError, match="invalid request"):
        model.complete("s", "u", **KW)
    assert delays == []
    assert not is_retryable_provider_error(ValueError("invalid"))


def test_resilient_provider_honors_retry_after_header():
    class ThrottledError(Exception):
        status_code = 429
        response = SimpleNamespace(headers={"Retry-After": "1.75"})

    calls = 0

    class Throttled:
        model_key = "m"
        model_id = "mid"

        def complete(self, *_args, **_kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ThrottledError("slow down")
            from flock.agents.providers.base import ChatResponse

            return ChatResponse(text="ok")

    delays = []
    response = ResilientChatModel(Throttled(), sleeper=delays.append).complete(
        "s", "u", **KW
    )
    assert response.attempts == 2
    assert delays == [1.75]


def test_google_adapter_bills_thinking_tokens(monkeypatch):
    from flock.agents.providers.google_provider import GoogleChatModel

    class Models:
        def generate_content(self, **_kwargs):
            return SimpleNamespace(
                text='{"orders": []}',
                response_id="gemini-request-1",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=100,
                    candidates_token_count=20,
                    thoughts_token_count=30,
                ),
            )

    google = ModuleType("google")
    genai = ModuleType("google.genai")
    fake_types = ModuleType("google.genai.types")
    cast(Any, fake_types).GenerateContentConfig = lambda **kwargs: kwargs
    cast(Any, genai).types = fake_types
    cast(Any, google).genai = genai
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)
    client = SimpleNamespace(models=Models())
    spec = ModelSpec(provider="google", model_id="gemini-3.1-pro-preview")
    response = GoogleChatModel("gemini", spec, client=client).complete("s", "u", **KW)
    assert response.visible_output_tokens == 20
    assert response.reasoning_tokens == 30
    assert response.output_tokens == 50
    assert response.request_id == "gemini-request-1"
    assert response.cost_usd == pytest.approx((100 * 2.0 + 50 * 12.0) / 1e6)
