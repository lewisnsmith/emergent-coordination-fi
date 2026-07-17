"""Provider adapters, tested with injected fake clients (no SDKs required)."""

from types import SimpleNamespace

import pytest

from flock.agents.providers.anthropic_provider import AnthropicChatModel
from flock.agents.providers.openai_compatible import OpenAICompatibleChatModel
from flock.agents.providers.openai_provider import OpenAIChatModel
from flock.agents.providers.pricing import cost_usd
from flock.agents.providers.resilient import ResilientChatModel, RetryPolicy
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
            content=[SimpleNamespace(type="text", text='{"orders": []}')],
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
                raise RuntimeError("temporary")
            return SimpleNamespace(text="ok")

    delays = []
    model = ResilientChatModel(
        Flaky(), RetryPolicy(max_attempts=3, initial_delay_s=0.25), sleeper=delays.append
    )
    assert model.complete("s", "u", **KW).text == "ok"
    assert delays == [0.25, 0.5]
