"""ChatModel interface all providers implement, plus the dispatch factory.

Provider SDKs are imported lazily inside the factory so the offline pipeline
(mock models) never needs them installed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType, SimpleNamespace
from typing import Protocol
from weakref import WeakSet

from flock.core.config import ModelSpec


@dataclass(frozen=True)
class ChatResponse:
    """Normalized response envelope preserved by caches, ledgers, and manifests."""

    text: str
    provider: str = ""
    requested_model_id: str = ""
    resolved_model_id: str = ""
    provider_request_id: str = ""
    provider_response_id: str = ""
    sdk_name: str = ""
    sdk_version: str = ""
    api_version: str = ""
    api_endpoint: str = ""
    terminal_state: str = ""
    finish_reason: str = ""
    stop_reason: str = ""
    refusal_reason: str = ""
    safety_status: str = "not_reported"
    block_reason: str = ""
    blocked: bool = False
    usage_reported: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    # Legacy alias for the provider response ID. New code should use the
    # explicit provider_request_id/provider_response_id fields above.
    request_id: str = ""
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    visible_output_tokens: int = 0
    reasoning_tokens: int = 0
    omitted_parameters: tuple[str, ...] = ()
    attempts: int = 1
    retry_errors: tuple[str, ...] = ()


class ProviderResponseError(RuntimeError):
    """A provider result was quarantined before it could enter the experiment."""


class ProviderTransportError(RuntimeError):
    """Sanitized SDK failure retaining only retry control metadata."""

    def __init__(
        self,
        provider: str,
        *,
        status_code: int | None = None,
        retry_after: str | None = None,
    ) -> None:
        super().__init__(f"{provider} request failed")
        self.status_code = status_code
        if retry_after is not None:
            headers = MappingProxyType({"retry-after": retry_after})
            self.response = SimpleNamespace(headers=headers)


def sanitized_provider_error(provider: str, error: Exception) -> ProviderTransportError:
    """Discard SDK error text and retain only status/retry scheduling metadata."""
    raw_status = getattr(error, "status_code", None)
    status_code = raw_status if isinstance(raw_status, int) else None
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None)
    retry_after: str | None = None
    if isinstance(headers, Mapping):
        for key, value in headers.items():
            if str(key).lower() == "retry-after":
                retry_after = str(value)
                break
    return ProviderTransportError(
        provider,
        status_code=status_code,
        retry_after=retry_after,
    )


def quarantine_provider_response(provider: str, reason: str) -> ProviderResponseError:
    """Build a deterministic error that never includes provider payload content."""
    return ProviderResponseError(f"{provider} response quarantined: {reason}")


class ChatModel(Protocol):
    model_key: str  # key in configs/models.yaml
    model_id: str

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse: ...


class _ExecutionLease:
    """Opaque capability for constructing an exact set of API-backed models."""

    __slots__ = ("_allowed_models", "_authorization_digest", "__weakref__")

    def __new__(cls) -> _ExecutionLease:
        raise TypeError("execution leases can only be issued by the control worker")

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("execution leases are immutable")


_ModelIdentity = tuple[str, str]
_ISSUED_EXECUTION_LEASES: WeakSet[_ExecutionLease] = WeakSet()


def _model_identity(model_key: str, spec: ModelSpec) -> _ModelIdentity:
    canonical_spec = json.dumps(
        spec.model_dump(mode="json", exclude_none=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    return (model_key, hashlib.sha256(canonical_spec.encode()).hexdigest())


def _issue_execution_lease(
    *, allowed_models: Mapping[str, ModelSpec], authorization_digest: str
) -> _ExecutionLease:
    """Issue a process-local lease after signed authorization verification.

    Only the control worker may call this private function. Ordinary CLI, grid,
    and ``run_config`` paths must never issue their own lease. The unfinished
    signed-control layer will supply the digest; this boundary deliberately does
    not accept an unsigned authorization record.
    """
    if len(authorization_digest) != 64 or any(
        char not in "0123456789abcdef" for char in authorization_digest
    ):
        raise ValueError("authorization_digest must be a lowercase sha-256 digest")
    identities = frozenset(
        _model_identity(model_key, spec) for model_key, spec in allowed_models.items()
    )
    if not identities:
        raise ValueError("execution lease must bind at least one exact model")

    lease = object.__new__(_ExecutionLease)
    object.__setattr__(lease, "_allowed_models", identities)
    object.__setattr__(lease, "_authorization_digest", authorization_digest)
    _ISSUED_EXECUTION_LEASES.add(lease)
    return lease


def requires_execution_lease(spec: ModelSpec) -> bool:
    """Return whether constructing this model crosses the provider boundary."""
    return spec.provider != "mock" and spec.deployment != "local"


def require_execution_lease(
    model_key: str, spec: ModelSpec, execution_lease: object | None
) -> None:
    """Fail unless an API model is covered by an internally issued exact-model lease."""
    if not requires_execution_lease(spec):
        return
    identity = _model_identity(model_key, spec)
    if (
        type(execution_lease) is not _ExecutionLease
        or execution_lease not in _ISSUED_EXECUTION_LEASES
        or identity not in execution_lease._allowed_models
    ):
        raise PermissionError(
            "provider-backed model "
            f"{model_key!r} requires an internally issued exact-model execution lease"
        )


def make_chat_model(
    model_key: str,
    spec: ModelSpec,
    *,
    execution_lease: object | None = None,
) -> ChatModel:
    require_execution_lease(model_key, spec, execution_lease)
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
