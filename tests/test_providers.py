"""Provider adapters, tested with injected fake clients (no SDKs required)."""

import sys
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest

from flock.agents.providers.anthropic_provider import AnthropicChatModel
from flock.agents.providers.base import ProviderResponseError, ProviderTransportError
from flock.agents.providers.google_provider import GoogleChatModel
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


def _anthropic_response(**overrides):
    values = {
        "id": "msg_123",
        "model": "claude-sonnet-5",
        "stop_reason": "end_turn",
        "content": [
            SimpleNamespace(type="thinking", thinking="internal"),
            SimpleNamespace(type="text", text='{"orders": []}'),
        ],
        "usage": SimpleNamespace(
            input_tokens=100,
            output_tokens=20,
            cache_read_input_tokens=10,
            cache_creation_input_tokens=5,
            output_tokens_details=SimpleNamespace(thinking_tokens=4),
        ),
        "_request_id": "anthropic-http-123",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _responses_response(**overrides):
    values = {
        "id": "resp_123",
        "model": "gpt-5.6-terra",
        "status": "completed",
        "output_text": "ok",
        "output": [SimpleNamespace(status="completed", content=[])],
        "usage": SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            input_tokens_details=SimpleNamespace(cached_tokens=2),
            output_tokens_details=SimpleNamespace(reasoning_tokens=1),
        ),
        "_request_id": "openai-http-123",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _google_response(**overrides):
    values = {
        "text": '{"orders": []}',
        "response_id": "gemini-response-1",
        "model_version": "gemini-3.1-pro-preview",
        "prompt_feedback": SimpleNamespace(block_reason="BLOCKED_REASON_UNSPECIFIED"),
        "candidates": [SimpleNamespace(finish_reason="STOP", safety_ratings=[])],
        "usage_metadata": SimpleNamespace(
            prompt_token_count=100,
            candidates_token_count=20,
            thoughts_token_count=30,
            cached_content_token_count=10,
            total_token_count=150,
        ),
        "sdk_http_response": SimpleNamespace(headers={"x-request-id": "google-http-1"}),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture(autouse=True)
def _fake_provider_versions(monkeypatch):
    versions = {
        "anthropic": "0.test",
        "openai": "0.test",
        "google-genai": "0.test",
    }
    for module in (
        "flock.agents.providers.anthropic_provider",
        "flock.agents.providers.openai_provider",
        "flock.agents.providers.google_provider",
    ):
        monkeypatch.setattr(f"{module}.version", versions.__getitem__)


def _install_google_types(monkeypatch, *, client_factory=None):
    google = ModuleType("google")
    genai = ModuleType("google.genai")
    fake_types = ModuleType("google.genai.types")
    cast(Any, fake_types).GenerateContentConfig = lambda **kwargs: kwargs
    cast(Any, fake_types).HttpRetryOptions = lambda **kwargs: SimpleNamespace(**kwargs)
    cast(Any, fake_types).HttpOptions = lambda **kwargs: SimpleNamespace(**kwargs)
    cast(Any, genai).Client = client_factory or (lambda **_kwargs: SimpleNamespace())
    cast(Any, genai).types = fake_types
    cast(Any, google).genai = genai
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)


def test_pricing_prefix_match():
    assert cost_usd("claude-sonnet-5", 1_000_000, 0) == 2.0
    assert cost_usd("gpt-5.6-sol", 0, 1_000_000) == 30.0
    with pytest.raises(ValueError, match="no verified token price"):
        cost_usd("totally-unknown", 1_000_000, 1_000_000)


def test_anthropic_adapter_parses_response():
    calls = {}

    def create(**kwargs):
        calls.update(kwargs)
        return _anthropic_response()

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    spec = ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    model = AnthropicChatModel("claude-sonnet", spec, client=client)
    resp = model.complete("sys", "user", **KW)
    assert resp.text == '{"orders": []}'
    assert calls["system"] == "sys"
    assert "temperature" not in calls
    assert resp.omitted_parameters == ("temperature", "top_p", "top_k")
    assert resp.requested_model_id == resp.resolved_model_id == "claude-sonnet-5"
    assert resp.provider_request_id == "anthropic-http-123"
    assert resp.provider_response_id == "msg_123"
    assert resp.usage_reported and resp.safety_status == "safe"
    assert resp.visible_output_tokens == 16 and resp.reasoning_tokens == 4
    expected_cost = (85 * 2.0 + 10 * 0.2 + 5 * 2.0 + 20 * 10.0) / 1e6
    assert resp.cost_usd == pytest.approx(expected_cost)


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


def _responses_fake_client(calls: dict, response=None):
    def create(**kwargs):
        calls.update(kwargs)
        return response or _responses_response()

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def test_openai_adapter_records_complete_envelope():
    calls = {}
    spec = ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    model = OpenAIChatModel("gpt-terra-frontier", spec, client=_responses_fake_client(calls))
    resp = model.complete("sys", "user", **KW)
    assert resp.text == "ok"
    assert "seed" not in calls
    assert calls["instructions"] == "sys"
    assert calls["input"] == "user"
    assert calls["store"] is False
    assert resp.requested_model_id == resp.resolved_model_id == "gpt-5.6-terra"
    assert resp.provider_request_id == "openai-http-123"
    assert resp.provider_response_id == "resp_123"
    assert resp.cached_input_tokens == 2
    assert resp.visible_output_tokens == 4 and resp.reasoning_tokens == 1


def test_provider_clients_disable_hidden_sdk_retries(monkeypatch):
    anthropic_calls = {}
    openai_calls = {}
    google_calls = {}

    anthropic = ModuleType("anthropic")
    openai = ModuleType("openai")
    cast(Any, anthropic).Anthropic = (
        lambda **kwargs: anthropic_calls.update(kwargs) or SimpleNamespace()
    )
    cast(Any, openai).OpenAI = (
        lambda **kwargs: openai_calls.update(kwargs) or SimpleNamespace()
    )
    monkeypatch.setitem(sys.modules, "anthropic", anthropic)
    monkeypatch.setitem(sys.modules, "openai", openai)
    _install_google_types(
        monkeypatch,
        client_factory=lambda **kwargs: google_calls.update(kwargs) or SimpleNamespace(),
    )

    AnthropicChatModel(
        "claude", ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    )._get_client()
    OpenAIChatModel(
        "gpt", ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    )._get_client()
    GoogleChatModel(
        "gemini", ModelSpec(provider="google", model_id="gemini-3.1-pro-preview")
    )._get_client()

    assert anthropic_calls == {"max_retries": 0}
    assert openai_calls == {"max_retries": 0}
    assert google_calls["http_options"].retry_options.attempts == 1


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (_responses_response(usage=None), "missing usage"),
        (_responses_response(model="gpt-5.6-sol"), "model resolution drift"),
        (_responses_response(status="incomplete"), "nonterminal response state"),
        (
            _responses_response(
                output=[
                    SimpleNamespace(
                        status="completed",
                        content=[SimpleNamespace(type="refusal", refusal="private payload")],
                    )
                ]
            ),
            "refusal",
        ),
    ],
)
def test_openai_quarantines_incomplete_or_unapproved_responses(response, reason):
    spec = ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    model = OpenAIChatModel("gpt", spec, client=_responses_fake_client({}, response))
    with pytest.raises(ProviderResponseError, match=reason) as captured:
        model.complete("sys", "user", **KW)
    assert "private payload" not in str(captured.value)


def test_sdk_error_text_is_sanitized_before_retry_logging():
    class SecretError(Exception):
        status_code = 429
        response = SimpleNamespace(
            headers={"retry-after": "1.25", "authorization": "secret-token"}
        )

    client = SimpleNamespace(
        responses=SimpleNamespace(
            create=lambda **_kwargs: (_ for _ in ()).throw(SecretError("secret-token"))
        )
    )
    spec = ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    with pytest.raises(ProviderTransportError, match="openai request failed") as captured:
        OpenAIChatModel("gpt", spec, client=client).complete("sys", "user", **KW)
    assert "secret-token" not in str(captured.value)
    assert captured.value.status_code == 429
    assert captured.value.response.headers == {"retry-after": "1.25"}


@pytest.mark.parametrize(
    "model_id",
    ["claude-opus-4-7", "claude-opus-4-8", "claude-opus-4-9-20990101"],
)
def test_current_anthropic_models_omit_unsupported_sampling(monkeypatch, model_id):
    monkeypatch.setattr(
        "flock.agents.providers.anthropic_provider.cost_usd", lambda *_args, **_kwargs: 0.0
    )
    calls = {}
    response = _anthropic_response(model=model_id)
    client = SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kwargs: calls.update(kwargs) or response
        )
    )
    spec = ModelSpec(provider="anthropic", model_id=model_id)
    response = AnthropicChatModel("claude", spec, client=client).complete("s", "u", **KW)
    assert "temperature" not in calls
    assert response.omitted_parameters == ("temperature", "top_p", "top_k")


def test_anthropic_quarantines_missing_response_metadata():
    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_kwargs: _anthropic_response(id=""))
    )
    spec = ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    with pytest.raises(ProviderResponseError, match="missing response id"):
        AnthropicChatModel("claude", spec, client=client).complete("s", "u", **KW)


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
    class Models:
        def generate_content(self, **_kwargs):
            return _google_response()

    _install_google_types(monkeypatch)
    client = SimpleNamespace(models=Models())
    spec = ModelSpec(provider="google", model_id="gemini-3.1-pro-preview")
    response = GoogleChatModel("gemini", spec, client=client).complete("s", "u", **KW)
    assert response.visible_output_tokens == 20
    assert response.reasoning_tokens == 30
    assert response.output_tokens == 50
    assert response.request_id == "gemini-response-1"
    assert response.provider_request_id == "google-http-1"
    assert response.resolved_model_id == "gemini-3.1-pro-preview"
    expected_cost = (90 * 2.0 + 10 * 0.2 + 50 * 12.0) / 1e6
    assert response.cost_usd == pytest.approx(expected_cost)


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (_google_response(usage_metadata=None), "missing usage"),
        (_google_response(model_version="gemini-drifted"), "model resolution drift"),
        (
            _google_response(
                prompt_feedback=SimpleNamespace(block_reason="SAFETY")
            ),
            "blocked prompt",
        ),
        (
            _google_response(
                candidates=[SimpleNamespace(finish_reason="SAFETY", safety_ratings=[])]
            ),
            "unsafe or nonterminal result",
        ),
    ],
)
def test_google_quarantines_drift_blocking_and_missing_usage(
    monkeypatch, response, reason
):
    _install_google_types(monkeypatch)
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **_kwargs: response)
    )
    spec = ModelSpec(provider="google", model_id="gemini-3.1-pro-preview")
    with pytest.raises(ProviderResponseError, match=reason):
        GoogleChatModel("gemini", spec, client=client).complete("s", "u", **KW)
