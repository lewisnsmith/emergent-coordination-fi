"""Auditable bounded retries for provider transport/rate-limit failures."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, replace

from flock.agents.providers.base import ChatModel, ChatResponse


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_s: float = 0.5
    multiplier: float = 2.0


_TRANSIENT_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def is_retryable_provider_error(exc: Exception) -> bool:
    """Conservatively classify transport, throttle, and server failures.

    Authentication, validation, and other deterministic client errors must
    fail immediately rather than consume time or duplicate billable calls.
    Provider SDK errors commonly expose either ``status_code`` directly or on
    a nested response object, so neither SDK needs to be imported here.
    """
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return status in _TRANSIENT_STATUS_CODES


def retry_after_seconds(exc: Exception, fallback: float) -> float:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) or {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    try:
        return max(float(value), 0.0) if value is not None else fallback
    except (TypeError, ValueError):
        return fallback


class ResilientChatModel:
    def __init__(
        self,
        inner: ChatModel,
        policy: RetryPolicy | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        policy = policy or RetryPolicy()
        if policy.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self.inner = inner
        self.policy = policy
        self.sleeper = sleeper
        self.model_key = inner.model_key
        self.model_id = inner.model_id

    def complete(
        self, system: str, user: str, *, temperature: float, seed: int, max_tokens: int
    ) -> ChatResponse:
        failures: list[str] = []
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                response = self.inner.complete(
                    system,
                    user,
                    temperature=temperature,
                    seed=seed,
                    max_tokens=max_tokens,
                )
                return replace(
                    response,
                    attempts=attempt,
                    retry_errors=tuple(failures),
                )
            except Exception as exc:
                failures.append(f"{type(exc).__name__}: {exc}")
                if attempt == self.policy.max_attempts or not is_retryable_provider_error(exc):
                    raise
                fallback = self.policy.initial_delay_s * self.policy.multiplier ** (attempt - 1)
                delay = retry_after_seconds(exc, fallback)
                self.sleeper(delay)
        raise AssertionError("unreachable")
