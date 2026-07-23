"""Framework-neutral causal activation hooks for a local frontier model.

The model adapter must expose activations and patch them during a second
forward pass. OpenAI-compatible HTTP serving alone is intentionally
insufficient because it cannot provide the internal causal intervention.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


class HookableLocalModel(Protocol):
    checkpoint_hash: str

    def capture(self, prompt: str, layers: tuple[int, ...]) -> dict[int, np.ndarray]: ...

    def score_with_patch(
        self, prompt: str, patches: dict[int, np.ndarray], target: str
    ) -> float: ...


@dataclass(frozen=True)
class PatchResult:
    layer: int
    clean_score: float
    treated_score: float
    patched_score: float
    recovered_fraction: float


def activation_patch(
    model: HookableLocalModel,
    clean_prompt: str,
    treated_prompt: str,
    target: str,
    layers: tuple[int, ...],
) -> list[PatchResult]:
    """Patch one clean activation into the treated run, one layer at a time."""
    clean_cache = model.capture(clean_prompt, layers)
    clean_score = model.score_with_patch(clean_prompt, {}, target)
    treated_score = model.score_with_patch(treated_prompt, {}, target)
    denominator = clean_score - treated_score
    results = []
    for layer in layers:
        patched = model.score_with_patch(treated_prompt, {layer: clean_cache[layer]}, target)
        recovered = (patched - treated_score) / denominator if denominator else 0.0
        results.append(PatchResult(layer, clean_score, treated_score, patched, recovered))
    return results
