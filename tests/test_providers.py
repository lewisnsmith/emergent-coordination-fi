"""Provider adapters, tested with injected fake clients (no SDKs required)."""

from types import SimpleNamespace

import pytest

from flock.agents.providers.anthropic_provider import AnthropicChatModel
from flock.agents.providers.openai_compatible import OpenAICompatibleChatModel
from flock.agents.providers.openai_provider import OpenAIChatModel
from flock.agents.providers.pricing import cost_usd
from flock.core.config import ModelSpec

KW = {"temperature": 0.5, "seed": 1, "max_tokens": 100}


def test_pricing_prefix_match():
    assert cost_usd("claude-sonnet-5", 1_000_000, 0) == 3.0
    assert cost_usd("claude-haiku-4-5-20251001", 0, 1_000_000) == 5.0
    assert cost_usd("totally-unknown", 1_000_000, 1_000_000) == 0.0


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
    assert resp.cost_usd == pytest.approx((100 * 3.0 + 20 * 15.0) / 1e6)


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


def test_openai_adapter_passes_seed():
    calls = {}
    spec = ModelSpec(provider="openai", model_id="gpt-5")
    model = OpenAIChatModel("gpt-5", spec, client=_openai_fake_client(calls))
    resp = model.complete("sys", "user", **KW)
    assert resp.text == "ok"
    assert calls["seed"] == 1
    assert calls["messages"][0]["role"] == "system"


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
