"""Run analysis report: metrics tables + figures + headline contrast.

`analyze_run` writes results/<run>/report/ (report.md + PNGs); with
paper=True it also exports figures and a LaTeX table to paper/.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from flock.analysis import convergence, coordination, strategy
from flock.analysis.stats import permutation_test
from flock.data.registry import Registry
from flock.logging_.decisions import RESULTS_DIR, resolve_run_dir

# Cohort colors: validated categorical palette, fixed by role (dataviz relief
# rule: sub-3:1 slots require the direct value labels below + md tables).
COHORT_COLORS = {"llm": "#2a78d6", "baseline": "#1baf7a", "null": "#eda100"}
_EXTRA_COLORS = ["#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
INK, MUTED, GRID = "#0b0b0b", "#898781", "#e1e0d9"

PRIMARY_CONTRAST = ("llm", "baseline")  # pre-registered H1 cohorts


def cohort_color(name: str, fallback_idx: int) -> str:
    return COHORT_COLORS.get(name, _EXTRA_COLORS[fallback_idx % len(_EXTRA_COLORS)])


def _style_axes(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def analyze_run(run_id: str, paper: bool = False, results_root: Path = RESULTS_DIR) -> Path:
    run_dir = resolve_run_dir(run_id, results_root)
    run = convergence.load_run(run_dir)
    report_dir = run_dir / "report"
    report_dir.mkdir(exist_ok=True)

    manifest = run["manifest"]
    cohorts = [c["name"] for c in manifest["config"]["cohorts"]]
    dataset_dir = Registry().dataset_dir(manifest["dataset"]["name"])

    metrics = {c: convergence.cohort_metrics(run, c) for c in cohorts}
    for c in cohorts:
        metrics[c].update(strategy.strategy_metrics(run, c, dataset_dir))
        metrics[c].update(coordination.coordination_metrics(run["decisions"], c))
    contrast = _primary_contrast(run, cohorts)

    _fig_metrics_by_cohort(metrics, report_dir)
    _fig_kappa_heatmap(run, cohorts, report_dir)
    _fig_equity_curves(run, cohorts, report_dir)
    _write_report_md(run_dir, manifest, metrics, contrast, report_dir)

    if paper:
        from flock.analysis.paper import export_paper_assets

        export_paper_assets(manifest, metrics, contrast, report_dir)
    return report_dir


def _primary_contrast(run: dict, cohorts: list[str]) -> dict | None:
    """Δκ = κ(llm) − κ(baseline): permutation p (agent relabeling) + bootstrap CI."""
    a_name, b_name = PRIMARY_CONTRAST
    if a_name not in cohorts or b_name not in cohorts:
        return None
    decisions = run["decisions"]

    def agents_of(c: str) -> list[str]:
        return sorted(decisions.loc[decisions["cohort"] == c, "agent_id"].unique())

    a, b = agents_of(a_name), agents_of(b_name)
    kappa = convergence.pairwise_kappa_matrix(decisions, a + b)

    def stat(x: list[str], y: list[str]) -> float:
        return convergence.mean_kappa_of_multiset(
            kappa, x
        ) - convergence.mean_kappa_of_multiset(kappa, y)

    perm = permutation_test(a, b, stat, n_permutations=10_000, seed=0)

    rng = np.random.default_rng(1)
    boots = []
    for _ in range(10_000):
        ra = [a[i] for i in rng.integers(0, len(a), len(a))]
        rb = [b[i] for i in rng.integers(0, len(b), len(b))]
        boots.append(stat(ra, rb))
    lo, hi = float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))
    return {
        "name": f"kappa({a_name}) - kappa({b_name})",
        "delta_kappa": perm.observed,
        "p_permutation": perm.p_value,
        "ci95": (lo, hi),
        "n_permutations": perm.n_permutations,
    }


def _fig_metrics_by_cohort(metrics: dict, report_dir: Path) -> None:
    keys = ["kappa", "agreement", "position_cosine", "portfolio_overlap"]
    labels = ["Cohen's κ", "Agreement", "Position cosine", "Portfolio overlap"]
    cohorts = list(metrics)
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150)
    width = 0.8 / len(cohorts)
    x = np.arange(len(keys))
    for i, c in enumerate(cohorts):
        vals = [metrics[c][k] for k in keys]
        bars = ax.bar(
            x + i * width, vals, width * 0.92, label=c, color=cohort_color(c, i)
        )
        for rect, v in zip(bars, vals, strict=True):
            if np.isfinite(v):
                ax.annotate(
                    f"{v:.2f}",
                    (rect.get_x() + rect.get_width() / 2, rect.get_height()),
                    ha="center", va="bottom", fontsize=8, color=INK,
                )
    ax.set_xticks(x + width * (len(cohorts) - 1) / 2, labels)
    ax.set_ylabel("similarity", color=MUTED)
    ax.set_title("Within-cohort convergence by metric", color=INK, fontsize=11)
    ax.legend(frameon=False, fontsize=9)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(report_dir / "convergence_by_cohort.png")
    plt.close(fig)


def _fig_kappa_heatmap(run: dict, cohorts: list[str], report_dir: Path) -> None:
    decisions = run["decisions"]
    agents = []
    for c in cohorts:
        agents.extend(sorted(decisions.loc[decisions["cohort"] == c, "agent_id"].unique()))
    n = len(agents)
    kap = convergence.pairwise_kappa_matrix(decisions, agents).to_numpy().astype(float)
    np.fill_diagonal(kap, np.nan)
    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=150)
    im = ax.imshow(kap, cmap="Blues", vmin=-0.2, vmax=1.0)
    ax.set_xticks(range(n), agents, rotation=90, fontsize=6, color=MUTED)
    ax.set_yticks(range(n), agents, fontsize=6, color=MUTED)
    ax.set_title("Pairwise Cohen's κ (agents grouped by cohort)", color=INK, fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.8).ax.tick_params(labelsize=8, colors=MUTED)
    fig.tight_layout()
    fig.savefig(report_dir / "kappa_heatmap.png")
    plt.close(fig)


def _fig_equity_curves(run: dict, cohorts: list[str], report_dir: Path) -> None:
    portfolio = run["portfolio"]
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150)
    for i, c in enumerate(cohorts):
        sub = portfolio[portfolio["cohort"] == c]
        color = cohort_color(c, i)
        for _, g in sub.groupby("agent_id"):
            g = g.sort_values("step")
            ax.plot(g["step"], g["equity"], color=color, linewidth=1.2, alpha=0.75)
        ax.plot([], [], color=color, linewidth=2, label=c)  # legend entry
    ax.set_xlabel("step", color=MUTED)
    ax.set_ylabel("equity", color=MUTED)
    ax.set_title("Equity curves by agent (colored by cohort)", color=INK, fontsize=11)
    ax.legend(frameon=False, fontsize=9)
    _style_axes(ax)
    fig.tight_layout()
    fig.savefig(report_dir / "equity_curves.png")
    plt.close(fig)


def _write_report_md(
    run_dir: Path, manifest: dict, metrics: dict, contrast: dict | None, report_dir: Path
) -> None:
    lines = [
        f"# Run report — `{manifest['run_id']}`",
        "",
        f"- config hash `{manifest['config_hash']}` · git `{manifest['git_sha'][:10]}` · "
        f"dataset `{manifest['dataset']['name']}` (sha `{manifest['dataset']['sha256'][:10]}`)",
        f"- {manifest['n_agents']} agents · {manifest['n_steps']} steps · "
        f"cost ${manifest['total_cost_usd']:.4f}",
        "",
        "## Within-cohort convergence",
        "",
    ]
    df = pd.DataFrame(metrics).T.round(4)
    lines.append(df.to_markdown())
    lines.append("")
    if contrast:
        lo, hi = contrast["ci95"]
        lines += [
            "## Primary contrast (H1)",
            "",
            f"**{contrast['name']}** = {contrast['delta_kappa']:.4f} "
            f"(95% bootstrap CI [{lo:.4f}, {hi:.4f}]; "
            f"permutation p = {contrast['p_permutation']:.4f}, "
            f"{contrast['n_permutations']} permutations, agent relabeling)",
            "",
            "Positive Δκ = the LLM cohort's decisions agree more than the baseline",
            "cohort's beyond chance. See docs/research/03-metrics.md.",
            "",
        ]
    lines += [
        "## Figures",
        "",
        "![convergence](report/convergence_by_cohort.png)",
        "![kappa heatmap](report/kappa_heatmap.png)",
        "![equity](report/equity_curves.png)",
        "",
    ]
    with open(run_dir / "report.md", "w") as f:
        f.write("\n".join(lines))
