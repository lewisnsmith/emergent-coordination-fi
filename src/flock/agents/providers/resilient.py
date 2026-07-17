"""Auditable bounded retries for provider transport/rate-limit failures."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from flock.agents.providers.base import ChatModel, ChatResponse


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_s: float = 0.5
    multiplier: float = 2.0


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
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                return self.inner.complete(
                    system,
                    user,
                    temperature=temperature,
                    seed=seed,
                    max_tokens=max_tokens,
                )
            except Exception:
                if attempt == self.policy.max_attempts:
                    raise
                delay = self.policy.initial_delay_s * self.policy.multiplier ** (attempt - 1)
                self.sleeper(delay)
        raise AssertionError("unreachable")
