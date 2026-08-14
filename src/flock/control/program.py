"""Canonical program phases and authorization-tier ordering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from flock.control.models import AuthorizationTier, ProgramPhase

PROGRAM_PHASES: tuple[ProgramPhase, ...] = (
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
)

AUTHORIZATION_TIERS: tuple[AuthorizationTier, ...] = (
    "plan",
    "mock",
    "canary",
    "pilot",
    "confirmatory",
    "release",
)


@dataclass(frozen=True)
class ProgramPhaseDefinition:
    """One phase and the first tier that may create an external side effect."""

    phase: ProgramPhase
    external_tier: AuthorizationTier | None


_EXTERNAL_TIERS: tuple[AuthorizationTier | None, ...] = (
    None,
    None,
    None,
    None,
    "canary",
    None,
    "canary",
    "canary",
    "pilot",
    "release",
)
PHASE_DEFINITIONS: tuple[ProgramPhaseDefinition, ...] = tuple(
    ProgramPhaseDefinition(phase, external_tier)
    for phase, external_tier in zip(PROGRAM_PHASES, _EXTERNAL_TIERS, strict=True)
)

_TIER_INDEX = {tier: index for index, tier in enumerate(AUTHORIZATION_TIERS)}


def parse_phase(value: str) -> ProgramPhase:
    """Return a canonical phase or fail without guessing."""

    if value not in PROGRAM_PHASES:
        raise ValueError(f"unknown program phase {value!r}; choose {list(PROGRAM_PHASES)}")
    return cast(ProgramPhase, value)


def parse_tier(value: str) -> AuthorizationTier:
    """Return a canonical tier or fail without guessing."""

    if value not in AUTHORIZATION_TIERS:
        raise ValueError(
            f"unknown authorization tier {value!r}; choose {list(AUTHORIZATION_TIERS)}"
        )
    return cast(AuthorizationTier, value)


def tier_at_least(value: AuthorizationTier, threshold: AuthorizationTier) -> bool:
    """Compare tiers using the sole canonical ordering."""

    return _TIER_INDEX[value] >= _TIER_INDEX[threshold]
