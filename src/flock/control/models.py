"""Strict, hash-addressed records for prompt-controlled experiment execution."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Annotated, Any, Literal, Self
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=160,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:@+-]*$",
    ),
]
ProgramPhase = Literal[
    "external-evidence-audit",
    "workstation-benchmark",
    "scoring-key-freeze",
    "local-precision-fidelity",
    "frontier-bridge",
    "mechanistic-funnel",
    "replay-discovery",
    "real-market-transport",
    "prospective-paper-trading",
    "release",
]
AuthorizationTier = Literal["plan", "mock", "canary", "pilot", "confirmatory", "release"]
SideEffect = Literal[
    "provider_generation",
    "data_acquisition",
    "paid_compute",
    "paper_order",
    "human_subject_contact",
    "registration",
    "publication",
    "remote_push",
    "paper_trading",
]


class StrictFrozenModel(BaseModel):
    """Shared configuration for records that must not accept implicit coercion."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self)

    def sha256(self) -> str:
        return canonical_sha256(self)


def canonical_json_bytes(value: Any) -> bytes:
    """Encode a model or JSON value using the repository's canonical representation."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the full lowercase SHA-256 of a canonical JSON value."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value.astimezone(UTC)


class ProviderContractV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    provider: Identifier
    endpoint: Annotated[str, StringConstraints(min_length=8, max_length=500)]
    deployment_class: Identifier
    requested_model: Annotated[str, StringConstraints(min_length=2, max_length=240)]
    resolved_model: Annotated[str, StringConstraints(min_length=2, max_length=240)]
    sdk_name: Identifier
    sdk_version: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    api_version: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    supported_parameters: tuple[Identifier, ...]
    omitted_parameters: tuple[Identifier, ...] = ()
    capability_sha256: Sha256
    pricing_sha256: Sha256

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        parsed = urlsplit(value)
        local_http = parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
        if parsed.scheme != "https" and not local_http:
            raise ValueError("endpoint must use HTTPS except for a loopback test endpoint")
        if (
            not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("endpoint must not contain credentials, a query, or a fragment")
        return value

    @model_validator(mode="after")
    def validate_parameters(self) -> Self:
        for label, values in (
            ("supported_parameters", self.supported_parameters),
            ("omitted_parameters", self.omitted_parameters),
        ):
            if len(values) != len(set(values)) or values != tuple(sorted(values)):
                raise ValueError(f"{label} must be sorted and unique")
        overlap = set(self.supported_parameters) & set(self.omitted_parameters)
        if overlap:
            raise ValueError(f"parameters cannot be both supported and omitted: {sorted(overlap)}")
        return self


class ExecutionFingerprintV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    source_sha256: Sha256
    lockfile_sha256: Sha256
    materialization_sha256: Sha256
    dataset_sha256: Sha256
    prompt_sha256: Sha256
    scoring_key_sha256: Sha256
    environment_sha256: Sha256
    split_registry_sha256: Sha256
    provider_contract: ProviderContractV1


class BudgetUsageV1(StrictFrozenModel):
    logical_calls: Annotated[int, Field(ge=0)] = 0
    wire_attempts: Annotated[int, Field(ge=0)] = 0
    input_tokens: Annotated[int, Field(ge=0)] = 0
    output_tokens: Annotated[int, Field(ge=0)] = 0
    reasoning_tokens: Annotated[int, Field(ge=0)] = 0
    cost_micro_usd: Annotated[int, Field(ge=0)] = 0
    wall_time_seconds: Annotated[int, Field(ge=0)] = 0

    def plus(self, other: BudgetUsageV1) -> BudgetUsageV1:
        return BudgetUsageV1(
            logical_calls=self.logical_calls + other.logical_calls,
            wire_attempts=self.wire_attempts + other.wire_attempts,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            cost_micro_usd=self.cost_micro_usd + other.cost_micro_usd,
            wall_time_seconds=self.wall_time_seconds + other.wall_time_seconds,
        )


class BudgetEnvelopeV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    max_logical_calls: Annotated[int, Field(ge=0)]
    max_wire_attempts: Annotated[int, Field(ge=0)]
    max_input_tokens: Annotated[int, Field(ge=0)]
    max_output_tokens: Annotated[int, Field(ge=0)]
    max_reasoning_tokens: Annotated[int, Field(ge=0)]
    max_cost_micro_usd: Annotated[int, Field(ge=0)]
    max_wall_time_seconds: Annotated[int, Field(ge=0)]

    def violations(self, usage: BudgetUsageV1) -> tuple[str, ...]:
        checks = (
            ("logical_calls", usage.logical_calls, self.max_logical_calls),
            ("wire_attempts", usage.wire_attempts, self.max_wire_attempts),
            ("input_tokens", usage.input_tokens, self.max_input_tokens),
            ("output_tokens", usage.output_tokens, self.max_output_tokens),
            ("reasoning_tokens", usage.reasoning_tokens, self.max_reasoning_tokens),
            ("cost_micro_usd", usage.cost_micro_usd, self.max_cost_micro_usd),
            ("wall_time_seconds", usage.wall_time_seconds, self.max_wall_time_seconds),
        )
        return tuple(f"{name}={actual}>{limit}" for name, actual, limit in checks if actual > limit)


class AuthorizationPayloadV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    authorization_id: Identifier
    issuer: Identifier
    issued_at: datetime
    expires_at: datetime
    phase: ProgramPhase
    tier: AuthorizationTier
    study_id: Identifier
    stage_id: Identifier
    assignment_ids: tuple[Identifier, ...] = Field(min_length=1)
    execution_fingerprint: ExecutionFingerprintV1
    output_root: Annotated[str, StringConstraints(min_length=1, max_length=1000)]
    budget: BudgetEnvelopeV1
    allowed_side_effects: tuple[SideEffect, ...] = ()
    live_money_trading: Literal[False] = False

    @field_validator("issued_at", "expires_at")
    @classmethod
    def normalize_timestamps(cls, value: datetime) -> datetime:
        return _utc(value)

    @field_validator("output_root")
    @classmethod
    def require_normalized_absolute_root(cls, value: str) -> str:
        path = PurePath(value)
        if (
            not path.is_absolute()
            or str(path) != value
            or any(part in {".", ".."} for part in path.parts)
        ):
            raise ValueError(
                "output_root must be an absolute normalized path without traversal"
            )
        return value

    @model_validator(mode="after")
    def validate_authorization(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        if len(self.assignment_ids) != len(set(self.assignment_ids)):
            raise ValueError("assignment_ids must be unique")
        if len(self.allowed_side_effects) != len(set(self.allowed_side_effects)) or (
            self.allowed_side_effects != tuple(sorted(self.allowed_side_effects))
        ):
            raise ValueError("allowed_side_effects must be sorted and unique")
        return self


class SignedAuthorizationV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    authorization: AuthorizationPayloadV1
    signer_identity: Identifier
    signature: Annotated[str, StringConstraints(min_length=64, max_length=32_768)]

    @field_validator("signature")
    @classmethod
    def require_ssh_signature_armor(cls, value: str) -> str:
        if not value.startswith("-----BEGIN SSH SIGNATURE-----") or not value.endswith(
            "-----END SSH SIGNATURE-----"
        ):
            raise ValueError("signature must be an armored OpenSSH signature")
        return value

    def signing_bytes(self) -> bytes:
        return canonical_json_bytes(
            {
                "schema_version": self.schema_version,
                "authorization": self.authorization.model_dump(mode="json"),
                "signer_identity": self.signer_identity,
            }
        )


PhaseStatus = Literal["planned", "started", "completed", "blocked", "failed"]


class PhaseEventV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    sequence: Annotated[int, Field(ge=1)]
    occurred_at: datetime
    phase: ProgramPhase
    tier: AuthorizationTier
    status: PhaseStatus
    execution_fingerprint_sha256: Sha256
    authorization_sha256: Sha256 | None = None
    evidence_sha256: Sha256 | None = None
    previous_event_sha256: Sha256 | None = None
    event_sha256: Sha256

    @field_validator("occurred_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def validate_hash(self) -> Self:
        expected = canonical_sha256(self.model_dump(mode="json", exclude={"event_sha256"}))
        if self.event_sha256 != expected:
            raise ValueError("phase event hash does not match its canonical payload")
        return self


SpendStatus = Literal[
    "reservation",
    "cancelled",
    "dispatch",
    "succeeded",
    "failed",
    "unknown",
    "reconciled",
]


class SpendEventV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    sequence: Annotated[int, Field(ge=1)]
    occurred_at: datetime
    authorization_id: Identifier
    authorization_sha256: Sha256
    reservation_id: Identifier
    status: SpendStatus
    budget: BudgetEnvelopeV1
    usage: BudgetUsageV1
    resolution: Literal["succeeded", "failed"] | None = None
    reconciliation_evidence_sha256: Sha256 | None = None
    previous_event_sha256: Sha256 | None = None
    event_sha256: Sha256

    @field_validator("occurred_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def validate_event(self) -> Self:
        if self.status == "reconciled":
            if self.resolution is None or self.reconciliation_evidence_sha256 is None:
                raise ValueError("reconciled events require a resolution and evidence hash")
        elif self.resolution is not None or self.reconciliation_evidence_sha256 is not None:
            raise ValueError("only reconciled events may include reconciliation fields")
        expected = canonical_sha256(self.model_dump(mode="json", exclude={"event_sha256"}))
        if self.event_sha256 != expected:
            raise ValueError("spend event hash does not match its canonical payload")
        return self
