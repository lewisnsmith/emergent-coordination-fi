"""End-to-end: build synthetic data -> run exp-000 -> analyze -> sanity-check
that known-convergent cohorts score above known-random cohorts."""

import json
from pathlib import Path

import pytest

from flock.analysis import convergence
from flock.analysis.report import analyze_run
from flock.core.config import load_experiment
from flock.data import builders
from flock.experiments.runner import run_experiment
from flock.logging_.decisions import RunWriter


@pytest.fixture(scope="module")
def smoke_run(tmp_path_factory, monkeypatch_module):
    workdir = tmp_path_factory.mktemp("e2e")
    monkeypatch_module.chdir(workdir)
    # mirror the repo configs the runner loads by path convention
    repo = Path(__file__).resolve().parents[1]
    (workdir / "configs").symlink_to(repo / "configs")
    builders.build("synthetic", seed=42)
    result = run_experiment(
        repo / "configs" / "experiments" / "exp-000-smoke.yaml",
        results_root=workdir / "results",
        use_cache=False,
    )
    return workdir, result


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch

    mp = MonkeyPatch()
    yield mp
    mp.undo()


def test_run_outputs_exist(smoke_run):
    _, result = smoke_run
    for name in ("decisions.jsonl", "fills.parquet", "portfolio.parquet", "manifest.json"):
        assert (result.run_dir / name).exists()
    manifest = json.loads((result.run_dir / "manifest.json").read_text())
    assert manifest["n_agents"] == 18
    assert manifest["dataset"]["sha256"]


def test_convergent_cohort_beats_null(smoke_run):
    _, result = smoke_run
    run = convergence.load_run(result.run_dir)
    llm = convergence.cohort_metrics(run, "llm")
    null = convergence.cohort_metrics(run, "null")
    assert llm["parse_failure_rate"] == 0.0
    # mock-momentum cohort must agree far above the random cohort
    assert llm["kappa"] > null["kappa"] + 0.2
    assert llm["agreement"] > null["agreement"]


def test_analyze_produces_report(smoke_run):
    workdir, result = smoke_run
    report_dir = analyze_run(result.run_id, results_root=workdir / "results")
    assert (report_dir / "convergence_by_cohort.png").exists()
    assert (report_dir / "kappa_heatmap.png").exists()
    assert (report_dir / "equity_curves.png").exists()
    report = (result.run_dir / "report.md").read_text()
    assert "Primary contrast" in report


def test_single_run_cannot_export_paper_evidence(smoke_run):
    workdir, result = smoke_run
    with pytest.raises(ValueError, match="single-run paper export is prohibited"):
        analyze_run(result.run_id, results_root=workdir / "results", paper=True)


def test_rerun_is_deterministic(smoke_run):
    workdir, result = smoke_run
    repo = Path(__file__).resolve().parents[1]
    cfg = load_experiment(repo / "configs" / "experiments" / "exp-000-smoke.yaml")
    result2 = run_experiment(
        repo / "configs" / "experiments" / "exp-000-smoke.yaml",
        results_root=workdir / "results2",
        use_cache=False,
    )
    d1 = (result.run_dir / "decisions.jsonl").read_text()
    d2 = (result2.run_dir / "decisions.jsonl").read_text()
    assert cfg.seed == 42
    # latency fields differ; compare decision-relevant fields
    for l1, l2 in zip(d1.splitlines(), d2.splitlines(), strict=True):
        r1, r2 = json.loads(l1), json.loads(l2)
        for k in ("agent_id", "step", "action", "orders", "orders_clipped"):
            assert r1[k] == r2[k]


def test_completed_run_resumes_without_rewriting_or_rebilling(smoke_run):
    workdir, result = smoke_run
    repo = Path(__file__).resolve().parents[1]
    manifest_path = result.run_dir / "manifest.json"
    before = manifest_path.read_bytes()
    resumed = run_experiment(
        repo / "configs" / "experiments" / "exp-000-smoke.yaml",
        results_root=workdir / "results",
        use_cache=False,
    )
    assert resumed == result
    assert manifest_path.read_bytes() == before
    assert json.loads(before)["status"] == "complete"


def test_failed_attempt_preserves_terminal_manifest(tmp_path):
    writer = RunWriter("interrupted-run", tmp_path)
    writer.checkpoint(0, 0.0)
    writer.fail(RuntimeError("provider interrupted"))
    failure = json.loads((writer.work_dir / "failure.json").read_text())
    assert failure["status"] == "failed"
    assert failure["error_type"] == "RuntimeError"
    assert not (writer.run_dir / "manifest.json").exists()
