"""Provider adapters, tested with injected fake clients (no SDKs required)."""

import sys
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest

from flock.agents.providers.anthropic_provider import AnthropicChatModel
from flock.agents.providers.base import (
    ProviderResponseError,
    ProviderTransportError,
    _issue_execution_lease,
    make_chat_model,
)
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
_TEST_AUTHORIZATION_DIGEST = "a" * 64


def _test_execution_lease(model_key: str, spec: ModelSpec) -> object:
    return _issue_execution_lease(
        allowed_models={model_key: spec},
        authorization_digest=_TEST_AUTHORIZATION_DIGEST,
    )


def _anthropic_model(
    model_key: str, spec: ModelSpec, client: Any = None
) -> AnthropicChatModel:
    return AnthropicChatModel(
        model_key,
        spec,
        client=client,
        execution_lease=_test_execution_lease(model_key, spec),
    )


def _openai_model(
    model_key: str, spec: ModelSpec, client: Any = None
) -> OpenAIChatModel:
    return OpenAIChatModel(
        model_key,
        spec,
        client=client,
        execution_lease=_test_execution_lease(model_key, spec),
    )


def _google_model(
    model_key: str, spec: ModelSpec, client: Any = None
) -> GoogleChatModel:
    return GoogleChatModel(
        model_key,
        spec,
        client=client,
        execution_lease=_test_execution_lease(model_key, spec),
    )


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
        "flock.agents.providers.openai_compatible",
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


def test_direct_api_adapters_require_exact_lease_before_sdk_client_construction(
    monkeypatch,
):
    client_constructions = []
    anthropic = ModuleType("anthropic")
    openai = ModuleType("openai")
    cast(Any, anthropic).Anthropic = lambda **kwargs: client_constructions.append(
        ("anthropic", kwargs)
    )
    cast(Any, openai).OpenAI = lambda **kwargs: client_constructions.append(
        ("openai", kwargs)
    )
    monkeypatch.setitem(sys.modules, "anthropic", anthropic)
    monkeypatch.setitem(sys.modules, "openai", openai)
    _install_google_types(
        monkeypatch,
        client_factory=lambda **kwargs: client_constructions.append(
            ("google", kwargs)
        ),
    )

    anthropic_spec = ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    openai_spec = ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    google_spec = ModelSpec(provider="google", model_id="gemini-3.1-pro-preview")
    for constructor, model_key, spec in (
        (AnthropicChatModel, "claude-direct", anthropic_spec),
        (OpenAIChatModel, "gpt-direct", openai_spec),
        (GoogleChatModel, "gemini-direct", google_spec),
    ):
        with pytest.raises(
            PermissionError, match="internally issued exact-model execution lease"
        ):
            constructor(model_key, spec)
        with pytest.raises(
            PermissionError, match="internally issued exact-model execution lease"
        ):
            constructor(model_key, spec, client=SimpleNamespace())

    wrong_lease = _test_execution_lease("claude-direct", anthropic_spec)
    with pytest.raises(
        PermissionError, match="internally issued exact-model execution lease"
    ):
        OpenAIChatModel(
            "gpt-direct",
            openai_spec,
            execution_lease=wrong_lease,
        )

    mislabeled_local = anthropic_spec.model_copy(update={"deployment": "local"})
    with pytest.raises(
        PermissionError, match="internally issued exact-model execution lease"
    ):
        AnthropicChatModel("claude-direct", mislabeled_local)
    for constructor, model_key in (
        (AnthropicChatModel, "claude-direct"),
        (OpenAIChatModel, "gpt-direct"),
        (GoogleChatModel, "gemini-direct"),
    ):
        mislabeled_mock = ModelSpec(provider="mock", model_id="frontier-model")
        with pytest.raises(ValueError, match="requires provider"):
            constructor(model_key, mislabeled_mock)
    assert client_constructions == []


@pytest.mark.parametrize(
    ("model_key", "spec"),
    [
        (
            "claude-direct",
            ModelSpec(provider="anthropic", model_id="claude-sonnet-5"),
        ),
        ("gpt-direct", ModelSpec(provider="openai", model_id="gpt-5.6-terra")),
        (
            "gemini-direct",
            ModelSpec(provider="google", model_id="gemini-3.1-pro-preview"),
        ),
    ],
)
def test_factory_passes_exact_lease_and_disables_outer_retries(model_key, spec):
    model = make_chat_model(
        model_key,
        spec,
        execution_lease=_test_execution_lease(model_key, spec),
    )
    assert isinstance(model, ResilientChatModel)
    assert model.policy.max_attempts == 1


def test_anthropic_adapter_parses_response():
    calls = {}

    def create(**kwargs):
        calls.update(kwargs)
        return _anthropic_response()

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    spec = ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    model = _anthropic_model("claude-sonnet", spec, client=client)
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


def _openai_fake_client(
    calls: dict,
    *,
    base_url: str = "http://127.0.0.1:11434/v1",
    response: object | None = None,
):
    def create(**kwargs):
        calls.update(kwargs)
        return response or SimpleNamespace(
            id="chatcmpl-local-1",
            model="llama3.3:70b",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="ok"),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            _request_id="compatible-http-1",
        )

    return SimpleNamespace(
        base_url=base_url,
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
    )


def _responses_fake_client(calls: dict, response=None):
    def create(**kwargs):
        calls.update(kwargs)
        return response or _responses_response()

    return SimpleNamespace(responses=SimpleNamespace(create=create))


def test_openai_adapter_records_complete_envelope():
    calls = {}
    spec = ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    model = _openai_model(
        "gpt-terra-frontier", spec, client=_responses_fake_client(calls)
    )
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

    _anthropic_model(
        "claude", ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    )._get_client()
    _openai_model(
        "gpt", ModelSpec(provider="openai", model_id="gpt-5.6-terra")
    )._get_client()
    _google_model(
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
    model = _openai_model("gpt", spec, client=_responses_fake_client({}, response))
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
        _openai_model("gpt", spec, client=client).complete("sys", "user", **KW)
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
    response = _anthropic_model("claude", spec, client=client).complete("s", "u", **KW)
    assert "temperature" not in calls
    assert response.omitted_parameters == ("temperature", "top_p", "top_k")


def test_anthropic_quarantines_missing_response_metadata():
    client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_kwargs: _anthropic_response(id=""))
    )
    spec = ModelSpec(provider="anthropic", model_id="claude-sonnet-5")
    with pytest.raises(ProviderResponseError, match="missing response id"):
        _anthropic_model("claude", spec, client=client).complete("s", "u", **KW)


def test_openai_compatible_requires_base_url(monkeypatch):
    monkeypatch.delenv("OPENAI_COMPATIBLE_BASE_URL", raising=False)
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )
    with pytest.raises(RuntimeError, match="OPENAI_COMPATIBLE_BASE_URL"):
        OpenAICompatibleChatModel("local", spec)


def test_openai_compatible_with_injected_loopback_client_preserves_provenance(
    monkeypatch,
):
    base_url = "http://127.0.0.1:11434/v1"
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", base_url)
    calls = {}
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )
    model = OpenAICompatibleChatModel(
        "local",
        spec,
        client=_openai_fake_client(calls, base_url=base_url),
    )
    resp = model.complete("sys", "user", **KW)
    assert resp.text == "ok"
    assert resp.provider == "openai_compatible"
    assert resp.requested_model_id == resp.resolved_model_id == "llama3.3:70b"
    assert resp.provider_request_id == "compatible-http-1"
    assert resp.provider_response_id == "chatcmpl-local-1"
    assert resp.sdk_name == "openai" and resp.sdk_version == "0.test"
    assert resp.api_endpoint == f"{base_url}/chat/completions"
    assert resp.finish_reason == "stop"
    assert resp.usage_reported
    assert (resp.input_tokens, resp.output_tokens, resp.total_tokens) == (10, 5, 15)
    assert resp.cost_usd == 0.0


@pytest.mark.parametrize(
    "base_url",
    [
        "https://api.example.test/v1",
        "http://localhost.example.test/v1",
        "http://127.0.0.1.example.test/v1",
        "http://2130706433/v1",
        "http://user:secret@localhost:11434/v1",
        "http://localhost:11434/v1?target=remote",
        "http://localhost:11434/v1?",
        "http://localhost:11434/v1#fragment",
        "ftp://localhost:11434/v1",
        "file:///tmp/provider.sock",
        "http://[::1",
        "http://[::1%25lo0]:8000/v1",
        " http://localhost:11434/v1",
        "http://localhost\\@remote.example/v1",
    ],
)
def test_local_compatible_rejects_remote_masquerades_before_sdk_construction(
    monkeypatch, base_url
):
    sdk_constructions = []
    openai = ModuleType("openai")
    cast(Any, openai).OpenAI = lambda **kwargs: sdk_constructions.append(kwargs)
    monkeypatch.setitem(sys.modules, "openai", openai)
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", base_url)
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )

    with pytest.raises(RuntimeError, match="OPENAI_COMPATIBLE_BASE_URL"):
        OpenAICompatibleChatModel("local", spec)
    assert sdk_constructions == []


@pytest.mark.parametrize(
    "base_url",
    [
        "http://localhost:11434/v1",
        "http://127.42.0.1:8000/v1/",
        "http://[::1]:8000/v1",
    ],
)
def test_local_compatible_loopback_client_disables_sdk_retries(
    monkeypatch, base_url
):
    sdk_constructions = []
    openai = ModuleType("openai")

    def construct(**kwargs):
        sdk_constructions.append(kwargs)
        return SimpleNamespace(base_url=kwargs["base_url"])

    cast(Any, openai).OpenAI = construct
    monkeypatch.setitem(sys.modules, "openai", openai)
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", base_url)
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )

    OpenAICompatibleChatModel("local", spec)._get_client()

    assert len(sdk_constructions) == 1
    assert sdk_constructions[0]["max_retries"] == 0
    assert sdk_constructions[0]["base_url"] == base_url.rstrip("/")


def test_local_compatible_revalidates_environment_before_client_creation(monkeypatch):
    sdk_constructions = []
    openai = ModuleType("openai")
    cast(Any, openai).OpenAI = lambda **kwargs: sdk_constructions.append(kwargs)
    monkeypatch.setitem(sys.modules, "openai", openai)
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "http://127.0.0.1:8000/v1")
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )
    model = OpenAICompatibleChatModel("local", spec)
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "http://127.0.0.1:9000/v1")

    with pytest.raises(RuntimeError, match="changed after adapter construction"):
        model._get_client()
    assert sdk_constructions == []


def test_compatible_injected_client_cannot_masquerade_as_loopback(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "http://127.0.0.1:8000/v1")
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )
    client = _openai_fake_client({}, base_url="https://remote.example.test/v1")

    with pytest.raises(RuntimeError, match="loopback host"):
        OpenAICompatibleChatModel("local", spec, client=client)


def test_api_compatible_requires_exact_lease_and_factory_passes_it(monkeypatch):
    base_url = "https://api.example.test/v1"
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", base_url)
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="api",
    )
    with pytest.raises(
        PermissionError, match="internally issued exact-model execution lease"
    ):
        OpenAICompatibleChatModel("compatible-api", spec)

    lease = _test_execution_lease("compatible-api", spec)
    model = OpenAICompatibleChatModel(
        "compatible-api",
        spec,
        client=_openai_fake_client({}, base_url=base_url),
        execution_lease=lease,
    )
    assert model.complete("sys", "user", **KW).api_endpoint == (
        f"{base_url}/chat/completions"
    )
    wrapped = make_chat_model("compatible-api", spec, execution_lease=lease)
    assert isinstance(wrapped, ResilientChatModel)
    assert isinstance(wrapped.inner, OpenAICompatibleChatModel)
    assert wrapped.policy.max_attempts == 1


def test_local_compatible_factory_requires_no_lease_only_for_loopback(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "http://localhost:11434/v1")
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )
    wrapped = make_chat_model("compatible-local", spec)
    assert isinstance(wrapped, ResilientChatModel)
    assert isinstance(wrapped.inner, OpenAICompatibleChatModel)


def test_compatible_transport_errors_are_sanitized(monkeypatch):
    class SecretError(Exception):
        status_code = 503

    base_url = "http://127.0.0.1:11434/v1"
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", base_url)
    client = SimpleNamespace(
        base_url=base_url,
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: (_ for _ in ()).throw(
                    SecretError("secret-compatible-token")
                )
            )
        ),
    )
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )
    with pytest.raises(
        ProviderTransportError, match="openai_compatible request failed"
    ) as captured:
        OpenAICompatibleChatModel("local", spec, client=client).complete(
            "sys", "user", **KW
        )
    assert "secret-compatible-token" not in str(captured.value)

    openai = ModuleType("openai")
    cast(Any, openai).OpenAI = lambda **_kwargs: (_ for _ in ()).throw(
        SecretError("secret-compatible-constructor-token")
    )
    monkeypatch.setitem(sys.modules, "openai", openai)
    with pytest.raises(
        ProviderTransportError, match="openai_compatible request failed"
    ) as constructor_error:
        OpenAICompatibleChatModel("local", spec)._get_client()
    assert "secret-compatible-constructor-token" not in str(constructor_error.value)


def test_compatible_does_not_invent_missing_optional_provenance(monkeypatch):
    base_url = "http://127.0.0.1:11434/v1"
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", base_url)
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
    )
    spec = ModelSpec(
        provider="openai_compatible",
        model_id="llama3.3:70b",
        deployment="local",
    )
    result = OpenAICompatibleChatModel(
        "local",
        spec,
        client=_openai_fake_client({}, base_url=base_url, response=response),
    ).complete("sys", "user", **KW)

    assert result.resolved_model_id == ""
    assert result.provider_request_id == ""
    assert result.provider_response_id == ""
    assert result.finish_reason == ""
    assert not result.usage_reported
    assert (result.input_tokens, result.output_tokens, result.total_tokens) == (0, 0, 0)


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
    response = _google_model("gemini", spec, client=client).complete("s", "u", **KW)
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
        _google_model("gemini", spec, client=client).complete("s", "u", **KW)
