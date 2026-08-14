from __future__ import annotations

import shutil
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from pydantic import ValidationError

from flock.control import (
    AuthorizationPayloadV1,
    AuthorizationVerificationError,
    BudgetEnvelopeV1,
    BudgetExceeded,
    BudgetUsageV1,
    ControlLedger,
    ExecutionFingerprintV1,
    LedgerIntegrityError,
    LedgerTransitionError,
    ProviderContractV1,
    SignedAuthorizationV1,
    canonical_json_bytes,
    verify_authorization,
)


def _digest(character: str) -> str:
    return character * 64


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _fingerprint(source: str = "a") -> ExecutionFingerprintV1:
    return ExecutionFingerprintV1(
        source_sha256=_digest(source),
        lockfile_sha256=_digest("b"),
        materialization_sha256=_digest("c"),
        dataset_sha256=_digest("d"),
        prompt_sha256=_digest("e"),
        scoring_key_sha256=_digest("f"),
        environment_sha256=_digest("1"),
        split_registry_sha256=_digest("2"),
        provider_contract=ProviderContractV1(
            provider="fake-provider",
            endpoint="http://127.0.0.1:8765/v1",
            deployment_class="test",
            requested_model="fake-model-2026-08-14",
            resolved_model="fake-model-2026-08-14-r1",
            sdk_name="fake-sdk",
            sdk_version="1.2.3",
            api_version="2026-08-14",
            supported_parameters=("max_tokens", "seed"),
            omitted_parameters=("temperature",),
            capability_sha256=_digest("3"),
            pricing_sha256=_digest("4"),
        ),
    )


def _budget(
    *,
    calls: int = 2,
    attempts: int = 2,
    cost_micro_usd: int = 100,
) -> BudgetEnvelopeV1:
    return BudgetEnvelopeV1(
        max_logical_calls=calls,
        max_wire_attempts=attempts,
        max_input_tokens=1_000,
        max_output_tokens=1_000,
        max_reasoning_tokens=1_000,
        max_cost_micro_usd=cost_micro_usd,
        max_wall_time_seconds=1_000,
    )


def _payload(
    tmp_path: Path,
    *,
    now: datetime,
    fingerprint: ExecutionFingerprintV1 | None = None,
    budget: BudgetEnvelopeV1 | None = None,
) -> AuthorizationPayloadV1:
    return AuthorizationPayloadV1(
        authorization_id="auth-test",
        issuer="test-operator",
        issued_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(minutes=10),
        phase="frontier-bridge",
        tier="canary",
        study_id="paper-core-v1",
        stage_id="frontier-canary",
        assignment_ids=("assignment-a", "assignment-b"),
        execution_fingerprint=fingerprint or _fingerprint(),
        output_root=str(tmp_path / "results"),
        budget=budget or _budget(),
        allowed_side_effects=("provider_generation",),
        live_money_trading=False,
    )


def _key_material(tmp_path: Path) -> tuple[Path, Path]:
    executable = shutil.which("ssh-keygen")
    if executable is None:
        pytest.skip("ssh-keygen is not available")
    private_key = tmp_path / "ephemeral-test-key"
    generated = subprocess.run(
        [executable, "-q", "-t", "ed25519", "-N", "", "-f", str(private_key)],
        capture_output=True,
        check=False,
    )
    if generated.returncode != 0:
        pytest.skip("ssh-keygen cannot create an ephemeral test key")
    public_parts = private_key.with_suffix(".pub").read_text().split()
    allowed_signers = tmp_path / "allowed_signers"
    allowed_signers.write_text(
        f'test-signer namespaces="flock-authorization" '
        f"{public_parts[0]} {public_parts[1]}\n"
    )
    return private_key, allowed_signers


def _signed_record(
    tmp_path: Path,
    payload: AuthorizationPayloadV1,
    private_key: Path,
) -> SignedAuthorizationV1:
    unsigned_path = tmp_path / f"authorization-{payload.sha256()}.json"
    unsigned_path.write_bytes(
        canonical_json_bytes(
            {
                "schema_version": 1,
                "authorization": payload.model_dump(mode="json"),
                "signer_identity": "test-signer",
            }
        )
    )
    executable = shutil.which("ssh-keygen")
    assert executable is not None
    signed = subprocess.run(
        [
            executable,
            "-Y",
            "sign",
            "-f",
            str(private_key),
            "-n",
            "flock-authorization",
            str(unsigned_path),
        ],
        capture_output=True,
        check=False,
    )
    assert signed.returncode == 0, signed.stderr.decode()
    signature = Path(f"{unsigned_path}.sig").read_text()
    return SignedAuthorizationV1(
        authorization=payload,
        signer_identity="test-signer",
        signature=signature,
    )


def _verified(
    tmp_path: Path,
    *,
    now: datetime,
    budget: BudgetEnvelopeV1 | None = None,
):
    private_key, allowed_signers = _key_material(tmp_path)
    payload = _payload(tmp_path, now=now, budget=budget)
    record = _signed_record(tmp_path, payload, private_key)
    verified = verify_authorization(
        record,
        allowed_signers=allowed_signers,
        expected_fingerprint=payload.execution_fingerprint,
        expected_phase=payload.phase,
        expected_tier=payload.tier,
        expected_output_root=payload.output_root,
        now=now,
    )
    return verified, record, allowed_signers


def _usage(*, cost: int, input_tokens: int = 100) -> BudgetUsageV1:
    return BudgetUsageV1(
        logical_calls=1,
        wire_attempts=1,
        input_tokens=input_tokens,
        output_tokens=50,
        reasoning_tokens=10,
        cost_micro_usd=cost,
        wall_time_seconds=10,
    )


def test_models_are_strict_and_hash_canonical_content(tmp_path: Path) -> None:
    fingerprint = _fingerprint()
    assert len(fingerprint.sha256()) == 64
    assert fingerprint.sha256() == fingerprint.model_validate_json(
        fingerprint.canonical_bytes()
    ).sha256()
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ProviderContractV1.model_validate(
            {**fingerprint.provider_contract.model_dump(), "unbound": "field"}
        )
    with pytest.raises(ValidationError, match="sorted and unique"):
        ProviderContractV1.model_validate(
            {
                **fingerprint.provider_contract.model_dump(),
                "supported_parameters": ("seed", "max_tokens"),
            }
        )
    payload = _payload(tmp_path, now=_now())
    with pytest.raises(ValidationError, match="sorted and unique"):
        AuthorizationPayloadV1.model_validate(
            {
                **payload.model_dump(),
                "allowed_side_effects": ("provider_generation", "provider_generation"),
            }
        )
    with pytest.raises(ValidationError, match="without traversal"):
        AuthorizationPayloadV1.model_validate(
            {**payload.model_dump(), "output_root": str(tmp_path / "nested" / ".." / "escape")}
        )


def test_signature_verification_rejects_tamper_expiry_and_binding_drift(tmp_path: Path) -> None:
    now = _now()
    verified, record, allowed_signers = _verified(tmp_path, now=now)
    assert verified.authorization.authorization_id == "auth-test"

    tampered = record.model_copy(
        update={
            "authorization": record.authorization.model_copy(update={"stage_id": "other-stage"})
        }
    )
    with pytest.raises(AuthorizationVerificationError, match="signature"):
        verify_authorization(
            tampered,
            allowed_signers=allowed_signers,
            expected_fingerprint=record.authorization.execution_fingerprint,
            expected_phase="frontier-bridge",
            expected_tier="canary",
            expected_output_root=record.authorization.output_root,
            now=now,
        )
    with pytest.raises(AuthorizationVerificationError, match="expired"):
        verify_authorization(
            record,
            allowed_signers=allowed_signers,
            expected_fingerprint=record.authorization.execution_fingerprint,
            expected_phase="frontier-bridge",
            expected_tier="canary",
            expected_output_root=record.authorization.output_root,
            now=now + timedelta(hours=1),
        )
    with pytest.raises(AuthorizationVerificationError, match="fingerprint"):
        verify_authorization(
            record,
            allowed_signers=allowed_signers,
            expected_fingerprint=_fingerprint("9"),
            expected_phase="frontier-bridge",
            expected_tier="canary",
            expected_output_root=record.authorization.output_root,
            now=now,
        )
    with pytest.raises(AuthorizationVerificationError, match="output root"):
        verify_authorization(
            record,
            allowed_signers=allowed_signers,
            expected_fingerprint=record.authorization.execution_fingerprint,
            expected_phase="frontier-bridge",
            expected_tier="canary",
            expected_output_root=str(tmp_path / "wrong-root"),
            now=now,
        )


def test_unknown_reservation_is_held_until_evidenced_reconciliation(tmp_path: Path) -> None:
    now = _now()
    authorization, _, _ = _verified(tmp_path, now=now)
    ledger = ControlLedger(tmp_path / "control.sqlite3")

    ledger.reserve(authorization, "request-a", _usage(cost=100), occurred_at=now)
    ledger.dispatch(authorization, "request-a", occurred_at=now)
    ledger.mark_unknown(authorization, "request-a", occurred_at=now)
    assert ledger.verify().unresolved_unknowns == ("auth-test:request-a",)
    with pytest.raises(BudgetExceeded, match="cost_micro_usd"):
        ledger.reserve(authorization, "request-b", _usage(cost=1), occurred_at=now)

    ledger.reconcile(
        authorization,
        "request-a",
        _usage(cost=20, input_tokens=20),
        resolution="succeeded",
        evidence_sha256=_digest("7"),
        occurred_at=now,
    )
    ledger.reserve(authorization, "request-b", _usage(cost=80), occurred_at=now)
    assert ledger.spend_usage("auth-test").cost_micro_usd == 100
    verification = ledger.verify()
    assert verification.spend_events == 5
    assert verification.spend_root_sha256 is not None
    assert verification.unresolved_unknowns == ()


def test_spend_transitions_fail_closed(tmp_path: Path) -> None:
    now = _now()
    authorization, _, _ = _verified(tmp_path, now=now)
    ledger = ControlLedger(tmp_path / "control.sqlite3")
    with pytest.raises(LedgerTransitionError, match="unknown reservation"):
        ledger.dispatch(authorization, "missing", occurred_at=now)
    ledger.reserve(authorization, "request-a", _usage(cost=50), occurred_at=now)
    with pytest.raises(LedgerTransitionError, match="invalid spend transition"):
        ledger.succeed(authorization, "request-a", _usage(cost=10), occurred_at=now)
    ledger.dispatch(authorization, "request-a", occurred_at=now)
    assert ledger.verify().unresolved_dispatches == ("auth-test:request-a",)
    ledger.fail(authorization, "request-a", occurred_at=now)
    assert ledger.spend_usage("auth-test").cost_micro_usd == 50


def test_pre_dispatch_cancellation_safely_releases_reservation(tmp_path: Path) -> None:
    now = _now()
    authorization, _, _ = _verified(
        tmp_path,
        now=now,
        budget=_budget(calls=1, attempts=1, cost_micro_usd=50),
    )
    ledger = ControlLedger(tmp_path / "control.sqlite3")
    ledger.reserve(authorization, "request-a", _usage(cost=50), occurred_at=now)
    assert ledger.verify().unresolved_reservations == ("auth-test:request-a",)
    ledger.cancel(authorization, "request-a", occurred_at=now)
    assert ledger.verify().unresolved_reservations == ()
    assert ledger.spend_usage("auth-test") == BudgetUsageV1()
    ledger.reserve(authorization, "request-b", _usage(cost=50), occurred_at=now)
    with pytest.raises(LedgerTransitionError, match="invalid spend transition"):
        ledger.cancel(authorization, "request-a", occurred_at=now)


def test_concurrent_reservations_cannot_cross_last_budget_slot(tmp_path: Path) -> None:
    now = _now()
    authorization, _, _ = _verified(
        tmp_path,
        now=now,
        budget=_budget(calls=1, attempts=1, cost_micro_usd=50),
    )
    ledger = ControlLedger(tmp_path / "control.sqlite3")
    barrier = Barrier(2)

    def attempt(identifier: str):
        barrier.wait()
        try:
            return ledger.reserve(
                authorization, identifier, _usage(cost=50), occurred_at=now
            )
        except BudgetExceeded as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ("request-a", "request-b")))
    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert sum(isinstance(result, BudgetExceeded) for result in results) == 1
    assert ledger.verify().spend_events == 1
    with sqlite3.connect(ledger.path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_phase_chain_detects_payload_tampering(tmp_path: Path) -> None:
    now = _now()
    authorization, _, _ = _verified(tmp_path, now=now)
    ledger = ControlLedger(tmp_path / "control.sqlite3")
    event = ledger.append_phase_event(
        phase="frontier-bridge",
        tier="canary",
        status="started",
        execution_fingerprint=authorization.authorization.execution_fingerprint,
        authorization=authorization,
        occurred_at=now,
    )
    assert event.sequence == 1
    assert ledger.verify().phase_events == 1

    with sqlite3.connect(ledger.path) as connection:
        connection.execute("DROP TRIGGER phase_events_no_update")
        payload = event.canonical_bytes().replace(b'"status":"started"', b'"status":"planned"')
        connection.execute("UPDATE phase_events SET payload = ? WHERE sequence = 1", (payload,))
    with pytest.raises(LedgerIntegrityError, match="invalid phase-event payload"):
        ledger.verify()
