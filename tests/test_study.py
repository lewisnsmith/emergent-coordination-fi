from pathlib import Path

import pytest

from flock.analysis.report import analyze_run
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


def test_response_seeds_do_not_create_independent_market_blocks(monkeypatch):
    runs = iter(
        [
            {"manifest": {"config": {"independent_block": "trajectory-1", "seed": 1}}},
            {"manifest": {"config": {"independent_block": "trajectory-1", "seed": 2}}},
        ]
    )
    monkeypatch.setattr("flock.analysis.study.convergence.load_run", lambda _: next(runs))
    monkeypatch.setattr(
        "flock.analysis.study.convergence.cohort_metrics",
        lambda _run, cohort: {"kappa": 0.5 if cohort == "llm" else 0.2},
    )
    with pytest.raises(ValueError, match="duplicate independent block"):
        analyze_h1_study([Path("seed-1"), Path("seed-2")])


def test_study_rejects_shared_dependence_cluster(monkeypatch):
    runs = iter(
        [
            {
                "manifest": {
                    "config": {
                        "independent_block": "window-a",
                        "dependence_cluster": "2025-q1",
                    }
                }
            },
            {
                "manifest": {
                    "config": {
                        "independent_block": "window-b",
                        "dependence_cluster": "2025-q1",
                    }
                }
            },
        ]
    )
    monkeypatch.setattr("flock.analysis.study.convergence.load_run", lambda _: next(runs))
    monkeypatch.setattr(
        "flock.analysis.study.convergence.cohort_metrics",
        lambda _run, cohort: {"kappa": 0.5 if cohort == "llm" else 0.2},
    )
    with pytest.raises(ValueError, match="duplicate dependence cluster"):
        analyze_h1_study([Path("a"), Path("b")])


def test_study_rejects_placeholder_block(monkeypatch):
    run = {"manifest": {"config": {"independent_block": "equities-window-config-required"}}}
    monkeypatch.setattr("flock.analysis.study.convergence.load_run", lambda _: run)
    with pytest.raises(ValueError, match="invalid independent block"):
        analyze_h1_study([Path("a"), Path("b")])


def test_single_run_can_never_export_paper_assets():
    with pytest.raises(ValueError, match="single-run paper export is prohibited"):
        analyze_run("anything", paper=True)
