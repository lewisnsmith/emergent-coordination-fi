"""Atomic, fail-closed runtime budgets around substantive model calls."""

from __future__ import annotations

import threading
import uuid
from dataclasses import asdict, dataclass

from flock.agents.providers.base import ChatResponse
from flock.core.config import RuntimeBudget


class BudgetExceeded(RuntimeError):
    """Raised before a request whose conservative envelope crosses a cap."""


@dataclass(frozen=True)
class RequestReservation:
    reservation_id: str
    requests: int
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass(frozen=True)
class BudgetSnapshot:
    requests: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    pending_reservations: int


class RuntimeBudgetGuard:
    """Reserve a worst-case envelope before each provider call.

    Successful responses replace their reservation with actual billed usage.
    Failed requests retain the conservative reservation because providers can
    bill failed or retried attempts without returning complete usage metadata.
    The lock makes check-and-reserve atomic for future concurrent runners.
    """

    def __init__(self, cap: RuntimeBudget):
        self.cap = cap
        self._lock = threading.RLock()
        self._requests = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._cost_usd = 0.0
        self._pending: dict[str, RequestReservation] = {}

    def before_request(
        self,
        system: str,
        user: str,
        max_tokens: int,
        max_attempts: int,
    ) -> RequestReservation:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        # UTF-8 bytes are a deliberately conservative tokenizer-independent
        # upper bound for ordinary provider tokenizers.
        input_ceiling = len(f"{system}\n{user}".encode()) * max_attempts
        reservation = RequestReservation(
            reservation_id=uuid.uuid4().hex,
            requests=max_attempts,
            input_tokens=input_ceiling,
            output_tokens=max_tokens * max_attempts,
            cost_usd=self.cap.request_cost_reserve_usd,
        )
        with self._lock:
            pending = self._pending_total()
            proposed = BudgetSnapshot(
                requests=self._requests + pending.requests + reservation.requests,
                input_tokens=(
                    self._input_tokens + pending.input_tokens + reservation.input_tokens
                ),
                output_tokens=(
                    self._output_tokens + pending.output_tokens + reservation.output_tokens
                ),
                cost_usd=self._cost_usd + pending.cost_usd + reservation.cost_usd,
                pending_reservations=len(self._pending) + 1,
            )
            self._assert_within_cap(proposed)
            self._pending[reservation.reservation_id] = reservation
        return reservation

    def record_response(
        self, reservation: RequestReservation, response: ChatResponse
    ) -> None:
        with self._lock:
            self._take_pending(reservation)
            self._requests += max(response.attempts, 1)
            self._input_tokens += response.input_tokens
            self._output_tokens += response.output_tokens
            self._cost_usd += response.cost_usd
            self._assert_within_cap(self.snapshot())

    def record_failure(self, reservation: RequestReservation) -> None:
        """Conservatively treat an unmetered failed envelope as consumed."""
        with self._lock:
            self._take_pending(reservation)
            self._requests += reservation.requests
            self._input_tokens += reservation.input_tokens
            self._output_tokens += reservation.output_tokens
            self._cost_usd += reservation.cost_usd

    def snapshot(self) -> BudgetSnapshot:
        with self._lock:
            return BudgetSnapshot(
                requests=self._requests,
                input_tokens=self._input_tokens,
                output_tokens=self._output_tokens,
                cost_usd=self._cost_usd,
                pending_reservations=len(self._pending),
            )

    def manifest_payload(self) -> dict:
        return {"cap": self.cap.model_dump(), "actual": asdict(self.snapshot())}

    def _pending_total(self) -> RequestReservation:
        return RequestReservation(
            reservation_id="pending-total",
            requests=sum(item.requests for item in self._pending.values()),
            input_tokens=sum(item.input_tokens for item in self._pending.values()),
            output_tokens=sum(item.output_tokens for item in self._pending.values()),
            cost_usd=sum(item.cost_usd for item in self._pending.values()),
        )

    def _take_pending(self, reservation: RequestReservation) -> None:
        if self._pending.pop(reservation.reservation_id, None) is None:
            raise ValueError("unknown or already resolved budget reservation")

    def _assert_within_cap(self, usage: BudgetSnapshot) -> None:
        checks = (
            ("requests", usage.requests, self.cap.max_requests),
            ("input tokens", usage.input_tokens, self.cap.max_input_tokens),
            ("output tokens", usage.output_tokens, self.cap.max_output_tokens),
            ("cost USD", usage.cost_usd, self.cap.max_cost_usd),
        )
        for label, value, limit in checks:
            if value > limit:
                raise BudgetExceeded(f"runtime {label} cap exceeded: {value} > {limit}")
