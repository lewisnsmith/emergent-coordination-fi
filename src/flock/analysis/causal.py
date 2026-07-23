"""Fail-closed causal-language gates for real-market AI attribution (H10)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CausalGate:
    passed: bool
    allowed_label: str
    failures: tuple[str, ...]


def evaluate_ai_causal_gate(
    verified_exposure: bool,
    credible_counterfactual: bool,
    pretrend_passed: bool,
    placebo_passed: bool,
    spillovers_addressed: bool,
) -> CausalGate:
    requirements = {
        "AI exposure is not verified": verified_exposure,
        "no credible assignment or counterfactual": credible_counterfactual,
        "pretrend diagnostics failed": pretrend_passed,
        "placebo diagnostics failed": placebo_passed,
        "interference or spillovers are not addressed": spillovers_addressed,
    }
    failures = tuple(message for message, passed in requirements.items() if not passed)
    if failures:
        label = "ai_like_signature" if not verified_exposure else "verified_ai_exposure"
        return CausalGate(False, label, failures)
    return CausalGate(True, "causally_verified_ai_event", ())
