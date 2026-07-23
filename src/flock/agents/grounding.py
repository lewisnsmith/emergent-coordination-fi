"""Deterministic evidence catalog and grounding checks for LLM decisions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from flock.core.types import Observation

INJECTION_PATTERNS = (
    re.compile(r"ignore (?:all |the )?(?:previous|prior) instructions", re.I),
    re.compile(r"(?:reveal|print|repeat).{0,20}(?:system prompt|hidden instructions)", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"developer message", re.I),
)
NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?%?")


@dataclass(frozen=True)
class GroundingVerdict:
    ok: bool
    valid_refs: tuple[str, ...]
    failures: tuple[str, ...]
    injection_evidence: tuple[str, ...]


def evidence_catalog(obs: Observation) -> dict[str, str | float]:
    catalog: dict[str, str | float] = {
        "portfolio:cash": obs.portfolio.cash,
        "portfolio:equity": obs.portfolio.equity,
    }
    for symbol in obs.symbols:
        catalog[f"price:{symbol}"] = obs.prices[symbol]
        for bar in obs.bars[symbol]:
            catalog[f"bar:{symbol}:{bar.ts}:close"] = bar.close
            catalog[f"bar:{symbol}:{bar.ts}:volume"] = bar.volume
    for position in obs.portfolio.positions:
        catalog[f"portfolio:position:{position.symbol}:quantity"] = position.quantity
        catalog[f"portfolio:position:{position.symbol}:avg_price"] = position.avg_price
    for index, event in enumerate(obs.news):
        catalog[f"news:{index}"] = event.headline
    return catalog


def injection_evidence(obs: Observation) -> tuple[str, ...]:
    flagged = []
    for index, event in enumerate(obs.news):
        if any(pattern.search(event.headline) for pattern in INJECTION_PATTERNS):
            flagged.append(f"news:{index}")
    return tuple(flagged)


def validate_grounding(
    obs: Observation,
    evidence_refs: tuple[str, ...],
    confidence: float | None,
    rationale: str,
    require_refs: bool,
) -> GroundingVerdict:
    catalog = evidence_catalog(obs)
    valid = tuple(ref for ref in evidence_refs if ref in catalog)
    invalid = sorted(set(evidence_refs) - set(catalog))
    failures = [f"unknown evidence reference: {ref}" for ref in invalid]
    if require_refs and not evidence_refs:
        failures.append("no evidence references supplied")
    if confidence is not None and not 0 <= confidence <= 1:
        failures.append("confidence must be between 0 and 1")

    # Numeric statements in rationales must be traceable to an observed value.
    observed_numbers = {
        round(float(value), 8)
        for value in catalog.values()
        if isinstance(value, (int, float))
    }
    for token in NUMBER.findall(rationale):
        is_percent = token.endswith("%")
        number = float(token.rstrip("%"))
        candidates = {round(number, 8)}
        if is_percent:
            candidates.add(round(number / 100, 8))
        if not candidates & observed_numbers:
            failures.append(f"unsupported numeric claim: {token}")

    injected = injection_evidence(obs)
    if injected:
        failures.append(f"untrusted prompt-injection-like evidence: {','.join(injected)}")
    return GroundingVerdict(not failures, valid, tuple(failures), injected)
