"""Transactional, append-only phase and provider-spend ledgers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from flock.control.models import (
    AuthorizationTier,
    BudgetEnvelopeV1,
    BudgetUsageV1,
    ExecutionFingerprintV1,
    PhaseEventV1,
    PhaseStatus,
    ProgramPhase,
    Sha256,
    SpendEventV1,
    canonical_sha256,
)
from flock.control.signing import VerifiedAuthorization

_ZERO_HASH = "0" * 64


class LedgerError(RuntimeError):
    """Base class for control-ledger failures."""


class LedgerIntegrityError(LedgerError):
    """Raised when persisted rows no longer form a valid append-only chain."""


class LedgerTransitionError(LedgerError):
    """Raised for an invalid reservation lifecycle transition."""


class BudgetExceeded(LedgerError):
    """Raised before a reservation would cross a signed cumulative envelope."""


@dataclass(frozen=True)
class LedgerVerification:
    phase_events: int
    spend_events: int
    phase_root_sha256: str | None
    spend_root_sha256: str | None
    unresolved_reservations: tuple[str, ...]
    unresolved_dispatches: tuple[str, ...]
    unresolved_unknowns: tuple[str, ...]


@dataclass
class _ReservationState:
    reserved: BudgetUsageV1
    current: BudgetUsageV1
    status: str


class ControlLedger:
    """A SQLite/WAL ledger with full hash-chain validation on every append."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS phase_events (
                    sequence INTEGER PRIMARY KEY CHECK (sequence > 0),
                    event_sha256 TEXT NOT NULL UNIQUE,
                    payload BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS spend_events (
                    sequence INTEGER PRIMARY KEY CHECK (sequence > 0),
                    event_sha256 TEXT NOT NULL UNIQUE,
                    authorization_id TEXT NOT NULL,
                    reservation_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload BLOB NOT NULL
                );
                CREATE INDEX IF NOT EXISTS spend_events_authorization
                    ON spend_events (authorization_id, reservation_id, sequence);
                CREATE TRIGGER IF NOT EXISTS phase_events_no_update
                    BEFORE UPDATE ON phase_events BEGIN
                        SELECT RAISE(ABORT, 'phase events are append-only');
                    END;
                CREATE TRIGGER IF NOT EXISTS phase_events_no_delete
                    BEFORE DELETE ON phase_events BEGIN
                        SELECT RAISE(ABORT, 'phase events are append-only');
                    END;
                CREATE TRIGGER IF NOT EXISTS spend_events_no_update
                    BEFORE UPDATE ON spend_events BEGIN
                        SELECT RAISE(ABORT, 'spend events are append-only');
                    END;
                CREATE TRIGGER IF NOT EXISTS spend_events_no_delete
                    BEFORE DELETE ON spend_events BEGIN
                        SELECT RAISE(ABORT, 'spend events are append-only');
                    END;
                """
            )

    @contextmanager
    def _immediate(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _load_phase(self, connection: sqlite3.Connection) -> list[PhaseEventV1]:
        rows = connection.execute(
            "SELECT sequence, event_sha256, payload FROM phase_events ORDER BY sequence"
        ).fetchall()
        events: list[PhaseEventV1] = []
        previous: str | None = None
        for expected_sequence, row in enumerate(rows, start=1):
            try:
                event = PhaseEventV1.model_validate_json(bytes(row["payload"]))
            except ValueError as error:
                raise LedgerIntegrityError("invalid phase-event payload") from error
            if (
                row["sequence"] != expected_sequence
                or event.sequence != expected_sequence
                or row["event_sha256"] != event.event_sha256
                or event.previous_event_sha256 != previous
                or bytes(row["payload"]) != event.canonical_bytes()
            ):
                raise LedgerIntegrityError("phase-event sequence or hash chain is invalid")
            events.append(event)
            previous = event.event_sha256
        return events

    def _load_spend(self, connection: sqlite3.Connection) -> list[SpendEventV1]:
        rows = connection.execute(
            "SELECT sequence, event_sha256, authorization_id, reservation_id, status, payload "
            "FROM spend_events ORDER BY sequence"
        ).fetchall()
        events: list[SpendEventV1] = []
        previous: str | None = None
        for expected_sequence, row in enumerate(rows, start=1):
            try:
                event = SpendEventV1.model_validate_json(bytes(row["payload"]))
            except ValueError as error:
                raise LedgerIntegrityError("invalid spend-event payload") from error
            if (
                row["sequence"] != expected_sequence
                or event.sequence != expected_sequence
                or row["event_sha256"] != event.event_sha256
                or row["authorization_id"] != event.authorization_id
                or row["reservation_id"] != event.reservation_id
                or row["status"] != event.status
                or event.previous_event_sha256 != previous
                or bytes(row["payload"]) != event.canonical_bytes()
            ):
                raise LedgerIntegrityError("spend-event sequence or hash chain is invalid")
            events.append(event)
            previous = event.event_sha256
        self._validate_spend_lifecycles(events, persisted=True)
        return events

    def append_phase_event(
        self,
        *,
        phase: ProgramPhase,
        tier: AuthorizationTier,
        status: PhaseStatus,
        execution_fingerprint: ExecutionFingerprintV1,
        authorization: VerifiedAuthorization | None = None,
        evidence_sha256: Sha256 | None = None,
        occurred_at: datetime | None = None,
    ) -> PhaseEventV1:
        if authorization is not None:
            payload = authorization.authorization
            if (
                payload.phase != phase
                or payload.tier != tier
                or payload.execution_fingerprint.sha256() != execution_fingerprint.sha256()
            ):
                raise LedgerTransitionError("phase event does not match its verified authorization")
            if status in {"planned", "started"}:
                authorization.assert_current()
        with self._immediate() as connection:
            events = self._load_phase(connection)
            data = {
                "schema_version": 1,
                "sequence": len(events) + 1,
                "occurred_at": _event_time(occurred_at),
                "phase": phase,
                "tier": tier,
                "status": status,
                "execution_fingerprint_sha256": execution_fingerprint.sha256(),
                "authorization_sha256": (
                    authorization.record_sha256 if authorization is not None else None
                ),
                "evidence_sha256": evidence_sha256,
                "previous_event_sha256": events[-1].event_sha256 if events else None,
            }
            event = _phase_event(data)
            connection.execute(
                "INSERT INTO phase_events(sequence, event_sha256, payload) VALUES (?, ?, ?)",
                (event.sequence, event.event_sha256, event.canonical_bytes()),
            )
        return event

    def reserve(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        usage: BudgetUsageV1,
        *,
        occurred_at: datetime | None = None,
    ) -> SpendEventV1:
        authorization.assert_current()
        if usage.logical_calls < 1 or usage.wire_attempts < 1:
            raise LedgerTransitionError("a reservation must include a call and wire attempt")
        return self._append_spend(
            authorization,
            reservation_id,
            "reservation",
            usage,
            occurred_at=occurred_at,
        )

    def dispatch(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        *,
        occurred_at: datetime | None = None,
    ) -> SpendEventV1:
        authorization.assert_current()
        return self._transition_with_reserved_usage(
            authorization, reservation_id, "dispatch", occurred_at=occurred_at
        )

    def cancel(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        *,
        occurred_at: datetime | None = None,
    ) -> SpendEventV1:
        """Release a reservation only when no dispatch event has been recorded."""

        return self._append_spend(
            authorization,
            reservation_id,
            "cancelled",
            BudgetUsageV1(),
            occurred_at=occurred_at,
        )

    def succeed(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        usage: BudgetUsageV1,
        *,
        occurred_at: datetime | None = None,
    ) -> SpendEventV1:
        return self._append_spend(
            authorization,
            reservation_id,
            "succeeded",
            usage,
            occurred_at=occurred_at,
        )

    def fail(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        *,
        occurred_at: datetime | None = None,
    ) -> SpendEventV1:
        return self._transition_with_reserved_usage(
            authorization, reservation_id, "failed", occurred_at=occurred_at
        )

    def mark_unknown(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        *,
        occurred_at: datetime | None = None,
    ) -> SpendEventV1:
        return self._transition_with_reserved_usage(
            authorization, reservation_id, "unknown", occurred_at=occurred_at
        )

    def reconcile(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        usage: BudgetUsageV1,
        *,
        resolution: Literal["succeeded", "failed"],
        evidence_sha256: Sha256,
        occurred_at: datetime | None = None,
    ) -> SpendEventV1:
        return self._append_spend(
            authorization,
            reservation_id,
            "reconciled",
            usage,
            resolution=resolution,
            evidence_sha256=evidence_sha256,
            occurred_at=occurred_at,
        )

    def _transition_with_reserved_usage(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        status: Literal["dispatch", "failed", "unknown"],
        *,
        occurred_at: datetime | None,
    ) -> SpendEventV1:
        with self._immediate() as connection:
            events = self._load_spend(connection)
            state = _state_for(events, authorization.authorization.authorization_id, reservation_id)
            return self._insert_spend(
                connection,
                events,
                authorization,
                reservation_id,
                status,
                state.reserved,
                occurred_at=occurred_at,
            )

    def _append_spend(
        self,
        authorization: VerifiedAuthorization,
        reservation_id: str,
        status: Literal["reservation", "cancelled", "succeeded", "failed", "reconciled"],
        usage: BudgetUsageV1,
        *,
        resolution: Literal["succeeded", "failed"] | None = None,
        evidence_sha256: Sha256 | None = None,
        occurred_at: datetime | None,
    ) -> SpendEventV1:
        with self._immediate() as connection:
            events = self._load_spend(connection)
            return self._insert_spend(
                connection,
                events,
                authorization,
                reservation_id,
                status,
                usage,
                resolution=resolution,
                evidence_sha256=evidence_sha256,
                occurred_at=occurred_at,
            )

    def _insert_spend(
        self,
        connection: sqlite3.Connection,
        events: list[SpendEventV1],
        authorization: VerifiedAuthorization,
        reservation_id: str,
        status: str,
        usage: BudgetUsageV1,
        *,
        resolution: str | None = None,
        evidence_sha256: Sha256 | None = None,
        occurred_at: datetime | None,
    ) -> SpendEventV1:
        payload = authorization.authorization
        data = {
            "schema_version": 1,
            "sequence": len(events) + 1,
            "occurred_at": _event_time(occurred_at),
            "authorization_id": payload.authorization_id,
            "authorization_sha256": authorization.record_sha256,
            "reservation_id": reservation_id,
            "status": status,
            "budget": payload.budget,
            "usage": usage,
            "resolution": resolution,
            "reconciliation_evidence_sha256": evidence_sha256,
            "previous_event_sha256": events[-1].event_sha256 if events else None,
        }
        event = _spend_event(data)
        self._validate_spend_lifecycles([*events, event], persisted=False)
        connection.execute(
            "INSERT INTO spend_events("
            "sequence, event_sha256, authorization_id, reservation_id, status, payload"
            ") VALUES (?, ?, ?, ?, ?, ?)",
            (
                event.sequence,
                event.event_sha256,
                event.authorization_id,
                event.reservation_id,
                event.status,
                event.canonical_bytes(),
            ),
        )
        return event

    def _validate_spend_lifecycles(
        self, events: list[SpendEventV1], *, persisted: bool
    ) -> None:
        states: dict[tuple[str, str], _ReservationState] = {}
        authorizations: dict[str, tuple[str, BudgetEnvelopeV1]] = {}
        error_type: type[LedgerError] = LedgerIntegrityError if persisted else LedgerTransitionError
        for event in events:
            known = authorizations.setdefault(
                event.authorization_id, (event.authorization_sha256, event.budget)
            )
            if known != (event.authorization_sha256, event.budget):
                raise error_type("authorization hash or budget changed within the ledger")
            key = (event.authorization_id, event.reservation_id)
            state = states.get(key)
            if event.status == "reservation":
                if (
                    state is not None
                    or event.usage.logical_calls < 1
                    or event.usage.wire_attempts < 1
                ):
                    raise error_type("duplicate or empty reservation")
                state = _ReservationState(event.usage, event.usage, event.status)
                states[key] = state
            else:
                if state is None:
                    raise error_type("spend transition has no reservation")
                expected = {
                    "cancelled": "reservation",
                    "dispatch": "reservation",
                    "succeeded": "dispatch",
                    "failed": "dispatch",
                    "unknown": "dispatch",
                    "reconciled": "unknown",
                }[event.status]
                if state.status != expected:
                    raise error_type(f"invalid spend transition {state.status} -> {event.status}")
                if event.status == "cancelled" and event.usage != BudgetUsageV1():
                    raise error_type("cancelled reservations must release their full usage")
                if event.status in {"dispatch", "unknown"} and event.usage != state.reserved:
                    raise error_type(f"{event.status} must retain the full reservation")
                if event.status in {"succeeded", "failed", "reconciled"}:
                    _validate_terminal_usage(state.reserved, event.usage, error_type)
                state.current = event.usage
                state.status = event.status
            totals: dict[str, BudgetUsageV1] = {}
            for (authorization_id, _), item in states.items():
                totals[authorization_id] = totals.get(
                    authorization_id, BudgetUsageV1()
                ).plus(item.current)
            for authorization_id, total in totals.items():
                budget = authorizations[authorization_id][1]
                violations = budget.violations(total)
                if violations:
                    if persisted:
                        raise LedgerIntegrityError("persisted spend exceeds its signed budget")
                    raise BudgetExceeded(
                        "signed cumulative budget exceeded: " + ", ".join(violations)
                    )

    def spend_usage(self, authorization_id: str) -> BudgetUsageV1:
        with self._connect() as connection:
            events = self._load_spend(connection)
        states = _states_from_valid_events(events)
        total = BudgetUsageV1()
        for (event_authorization_id, _), state in states.items():
            if event_authorization_id == authorization_id:
                total = total.plus(state.current)
        return total

    def verify(self) -> LedgerVerification:
        with self._connect() as connection:
            phase = self._load_phase(connection)
            spend = self._load_spend(connection)
        states = _states_from_valid_events(spend)
        return LedgerVerification(
            phase_events=len(phase),
            spend_events=len(spend),
            phase_root_sha256=phase[-1].event_sha256 if phase else None,
            spend_root_sha256=spend[-1].event_sha256 if spend else None,
            unresolved_reservations=_reservations_with_status(states, "reservation"),
            unresolved_dispatches=_reservations_with_status(states, "dispatch"),
            unresolved_unknowns=_reservations_with_status(states, "unknown"),
        )


def _event_time(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None or current.utcoffset() is None:
        raise LedgerTransitionError("event time must include a UTC offset")
    return current.astimezone(UTC)


def _phase_event(data: dict[str, object]) -> PhaseEventV1:
    draft = PhaseEventV1.model_construct(**cast(Any, data), event_sha256=_ZERO_HASH)
    digest = canonical_sha256(draft.model_dump(mode="json", exclude={"event_sha256"}))
    return PhaseEventV1.model_validate({**data, "event_sha256": digest})


def _spend_event(data: dict[str, object]) -> SpendEventV1:
    draft = SpendEventV1.model_construct(**cast(Any, data), event_sha256=_ZERO_HASH)
    digest = canonical_sha256(draft.model_dump(mode="json", exclude={"event_sha256"}))
    return SpendEventV1.model_validate({**data, "event_sha256": digest})


def _state_for(
    events: list[SpendEventV1], authorization_id: str, reservation_id: str
) -> _ReservationState:
    states = _states_from_valid_events(events)
    try:
        return states[(authorization_id, reservation_id)]
    except KeyError as error:
        raise LedgerTransitionError("unknown reservation") from error


def _states_from_valid_events(
    events: list[SpendEventV1],
) -> dict[tuple[str, str], _ReservationState]:
    states: dict[tuple[str, str], _ReservationState] = {}
    for event in events:
        key = (event.authorization_id, event.reservation_id)
        if event.status == "reservation":
            states[key] = _ReservationState(event.usage, event.usage, event.status)
        else:
            state = states[key]
            state.current = event.usage
            state.status = event.status
    return states


def _validate_terminal_usage(
    reserved: BudgetUsageV1,
    actual: BudgetUsageV1,
    error_type: type[LedgerError],
) -> None:
    if (
        actual.logical_calls != reserved.logical_calls
        or actual.wire_attempts != reserved.wire_attempts
    ):
        raise error_type("terminal events cannot release logical calls or wire attempts")
    dimensions = (
        (actual.input_tokens, reserved.input_tokens),
        (actual.output_tokens, reserved.output_tokens),
        (actual.reasoning_tokens, reserved.reasoning_tokens),
        (actual.cost_micro_usd, reserved.cost_micro_usd),
        (actual.wall_time_seconds, reserved.wall_time_seconds),
    )
    if any(actual_value > reserved_value for actual_value, reserved_value in dimensions):
        raise error_type("terminal usage exceeds its conservative reservation")


def _reservations_with_status(
    states: dict[tuple[str, str], _ReservationState], status: str
) -> tuple[str, ...]:
    return tuple(
        sorted(
            f"{authorization_id}:{reservation_id}"
            for (authorization_id, reservation_id), state in states.items()
            if state.status == status
        )
    )
