"""Fail-closed records, authorization verification, and durable control ledgers."""

from flock.control.ledger import (
    BudgetExceeded,
    ControlLedger,
    LedgerError,
    LedgerIntegrityError,
    LedgerTransitionError,
    LedgerVerification,
)
from flock.control.models import (
    AuthorizationPayloadV1,
    AuthorizationTier,
    BudgetEnvelopeV1,
    BudgetUsageV1,
    ExecutionFingerprintV1,
    PhaseEventV1,
    ProgramPhase,
    ProviderContractV1,
    SignedAuthorizationV1,
    SpendEventV1,
    canonical_json_bytes,
    canonical_sha256,
)
from flock.control.science import (
    ContrastCoefficientV1,
    EstimandLockV1,
    PreregistrationReceiptV1,
    ScienceLockV1,
    load_science_lock,
)
from flock.control.signing import (
    AuthorizationVerificationError,
    VerifiedAuthorization,
    verify_authorization,
    verify_detached_signature,
)

__all__ = [
    "AuthorizationPayloadV1",
    "AuthorizationTier",
    "AuthorizationVerificationError",
    "BudgetEnvelopeV1",
    "BudgetExceeded",
    "BudgetUsageV1",
    "ControlLedger",
    "ContrastCoefficientV1",
    "EstimandLockV1",
    "ExecutionFingerprintV1",
    "LedgerError",
    "LedgerIntegrityError",
    "LedgerTransitionError",
    "LedgerVerification",
    "PhaseEventV1",
    "ProgramPhase",
    "PreregistrationReceiptV1",
    "ProviderContractV1",
    "SignedAuthorizationV1",
    "ScienceLockV1",
    "SpendEventV1",
    "VerifiedAuthorization",
    "canonical_json_bytes",
    "canonical_sha256",
    "load_science_lock",
    "verify_authorization",
    "verify_detached_signature",
]
