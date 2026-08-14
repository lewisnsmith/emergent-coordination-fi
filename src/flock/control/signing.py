"""Detached OpenSSH verification for experiment authorization records."""

from __future__ import annotations

import hmac
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from flock.control.models import (
    AuthorizationPayloadV1,
    AuthorizationTier,
    ExecutionFingerprintV1,
    ProgramPhase,
    SignedAuthorizationV1,
)

SIGNATURE_NAMESPACE = "flock-authorization"
_VERIFIED_TOKEN = object()


class AuthorizationVerificationError(ValueError):
    """Raised when an authorization is unsigned, stale, or bound to other inputs."""


class VerifiedAuthorization:
    """In-process capability returned only after signature and binding verification."""

    __slots__ = ("_record", "_record_sha256", "_verified_at")

    def __init__(
        self,
        record: SignedAuthorizationV1,
        verified_at: datetime,
        token: object,
    ) -> None:
        if token is not _VERIFIED_TOKEN:
            raise TypeError("VerifiedAuthorization can only be created by verify_authorization")
        self._record = record
        self._record_sha256 = record.sha256()
        self._verified_at = verified_at

    @property
    def record(self) -> SignedAuthorizationV1:
        return self._record

    @property
    def authorization(self) -> AuthorizationPayloadV1:
        return self._record.authorization

    @property
    def record_sha256(self) -> str:
        return self._record_sha256

    @property
    def verified_at(self) -> datetime:
        return self._verified_at

    def assert_current(self, now: datetime | None = None) -> None:
        current = _normalize_now(now)
        payload = self.authorization
        if current < payload.issued_at:
            raise AuthorizationVerificationError("authorization is not yet valid")
        if current >= payload.expires_at:
            raise AuthorizationVerificationError("authorization has expired")


def _normalize_now(now: datetime | None) -> datetime:
    current = now or datetime.now(UTC)
    if current.tzinfo is None or current.utcoffset() is None:
        raise AuthorizationVerificationError("verification time must include a UTC offset")
    return current.astimezone(UTC)


def verify_detached_signature(
    message: bytes,
    signature: str | bytes,
    *,
    signer_identity: str,
    allowed_signers: Path,
    namespace: str = SIGNATURE_NAMESPACE,
) -> None:
    """Verify an armored detached signature with the system OpenSSH verifier."""

    executable = shutil.which("ssh-keygen")
    if executable is None:
        raise AuthorizationVerificationError(
            "ssh-keygen is required for authorization verification"
        )
    if not allowed_signers.is_file():
        raise AuthorizationVerificationError("allowed-signers file does not exist")
    if allowed_signers.stat().st_size > 1_048_576:
        raise AuthorizationVerificationError("allowed-signers file is unexpectedly large")
    signature_bytes = signature.encode("ascii") if isinstance(signature, str) else signature
    with tempfile.TemporaryDirectory(prefix="flock-signature-") as temporary:
        signature_path = Path(temporary) / "authorization.sig"
        signature_path.write_bytes(signature_bytes)
        command = [
            executable,
            "-Y",
            "verify",
            "-f",
            str(allowed_signers),
            "-I",
            signer_identity,
            "-n",
            namespace,
            "-s",
            str(signature_path),
        ]
        try:
            result = subprocess.run(
                command,
                input=message,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AuthorizationVerificationError("OpenSSH signature verification failed") from error
    if result.returncode != 0:
        raise AuthorizationVerificationError("authorization signature is not valid or allowed")


def verify_authorization(
    record: SignedAuthorizationV1,
    *,
    allowed_signers: Path,
    expected_fingerprint: ExecutionFingerprintV1,
    expected_phase: ProgramPhase,
    expected_tier: AuthorizationTier,
    expected_output_root: str,
    now: datetime | None = None,
) -> VerifiedAuthorization:
    """Verify a signature and every execution binding before returning a capability."""

    verify_detached_signature(
        record.signing_bytes(),
        record.signature,
        signer_identity=record.signer_identity,
        allowed_signers=allowed_signers,
    )
    current = _normalize_now(now)
    payload = record.authorization
    if current < payload.issued_at:
        raise AuthorizationVerificationError("authorization is not yet valid")
    if current >= payload.expires_at:
        raise AuthorizationVerificationError("authorization has expired")
    if payload.phase != expected_phase:
        raise AuthorizationVerificationError("authorization phase does not match the request")
    if payload.tier != expected_tier:
        raise AuthorizationVerificationError("authorization tier does not match the request")
    if not hmac.compare_digest(payload.output_root, expected_output_root):
        raise AuthorizationVerificationError("authorization output root does not match the request")
    if not hmac.compare_digest(
        payload.execution_fingerprint.sha256(), expected_fingerprint.sha256()
    ):
        raise AuthorizationVerificationError("authorization fingerprint does not match the request")
    if payload.live_money_trading is not False:
        raise AuthorizationVerificationError("live-money trading is never authorized")
    return VerifiedAuthorization(record, current, _VERIFIED_TOKEN)
