"""Held-out detector evaluation for simulation-to-real transport (H9)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import rankdata


@dataclass(frozen=True)
class DetectorEvaluation:
    n: int
    prevalence: float
    roc_auc: float
    brier_score: float
    calibration_error: float


def evaluate_detector(
    labels: list[int], probabilities: list[float], bins: int = 10
) -> DetectorEvaluation:
    y = np.asarray(labels, dtype=int)
    p = np.asarray(probabilities, dtype=float)
    if len(y) != len(p) or len(y) < 2 or set(y) - {0, 1}:
        raise ValueError("labels must be equally sized binary observations")
    if np.any((p < 0) | (p > 1)) or not (np.any(y == 0) and np.any(y == 1)):
        raise ValueError("probabilities need [0,1] values and both classes")
    ranks = rankdata(p, method="average")
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    auc = (ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)
    edges = np.linspace(0, 1, bins + 1)
    calibration = 0.0
    for lower, upper in zip(edges[:-1], edges[1:], strict=True):
        mask = (p >= lower) & (p < upper if upper < 1 else p <= upper)
        if mask.any():
            calibration += mask.mean() * abs(float(p[mask].mean() - y[mask].mean()))
    return DetectorEvaluation(
        n=len(y),
        prevalence=float(y.mean()),
        roc_auc=float(auc),
        brier_score=float(np.mean((p - y) ** 2)),
        calibration_error=float(calibration),
    )
