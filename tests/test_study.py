from pathlib import Path

import pytest

from flock.analysis.study import analyze_h1_study


def test_study_requires_multiple_independent_blocks():
    with pytest.raises(ValueError, match="at least two independent blocks"):
        analyze_h1_study([])


def test_study_rejects_duplicate_independent_blocks(monkeypatch):
    run = {
        "manifest": {"config": {"independent_block": "w1", "seed": 1}},
        "decisions": None,
        "portfolio": None,
    }
    monkeypatch.setattr("flock.analysis.study.convergence.load_run", lambda _: run)
    monkeypatch.setattr(
        "flock.analysis.study.convergence.cohort_metrics",
        lambda _run, cohort: {"kappa": 0.5 if cohort == "llm" else 0.2},
    )
    with pytest.raises(ValueError, match="duplicate independent block"):
        analyze_h1_study([Path("a"), Path("b")])
