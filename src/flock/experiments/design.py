"""Deterministic generators for the MPHIQ and prompt-pressure designs."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

MPHIQ_FACTORS = ("model", "profile", "harness", "information", "prompt")


@dataclass(frozen=True)
class MPHIQScheme:
    code: str
    assignments: dict[str, bool]

    @property
    def same_factors(self) -> tuple[str, ...]:
        return tuple(name for name, same in self.assignments.items() if same)

    @property
    def different_factors(self) -> tuple[str, ...]:
        return tuple(name for name, same in self.assignments.items() if not same)


@dataclass(frozen=True)
class PressureCell:
    code: str
    stakes: str
    urgent: bool
    distressed: bool
    forced_action: bool


def generate_mphiq_schemes() -> list[MPHIQScheme]:
    """Return all 32 schemes in binary order; one means same, zero different."""
    schemes = []
    for value in range(32):
        code = f"{value:05b}"
        schemes.append(
            MPHIQScheme(
                code=code,
                assignments={
                    name: bit == "1"
                    for name, bit in zip(MPHIQ_FACTORS, code, strict=True)
                },
            )
        )
    return schemes


def generate_pressure_cells() -> list[PressureCell]:
    """Full 3×2×2×2 H12 decomposition (24 treatment cells)."""
    cells = []
    for stakes, urgent, distressed, forced in itertools.product(
        ("ordinary", "high_financial", "fictional_life_or_death"),
        (False, True),
        (False, True),
        (False, True),
    ):
        code = f"{stakes}__u{int(urgent)}e{int(distressed)}f{int(forced)}"
        cells.append(PressureCell(code, stakes, urgent, distressed, forced))
    return cells


def balanced_levels(levels: list[str], n_units: int, offset: int = 0) -> list[str]:
    """Allocate levels deterministically with cell counts differing by at most one."""
    if not levels:
        raise ValueError("at least one level is required")
    if n_units < 1:
        raise ValueError("n_units must be positive")
    return [levels[(index + offset) % len(levels)] for index in range(n_units)]


def validate_mphiq_catalog(codes: list[str]) -> list[str]:
    errors = []
    expected = {scheme.code for scheme in generate_mphiq_schemes()}
    actual = set(codes)
    if len(codes) != len(actual):
        errors.append("MPHIQ catalog contains duplicate codes")
    if actual != expected:
        errors.append(
            f"MPHIQ codes differ: missing={sorted(expected-actual)}, "
            f"extra={sorted(actual-expected)}"
        )
    return errors
