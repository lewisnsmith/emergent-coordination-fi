"""Deterministic claim-linked figures from block-level study artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import matplotlib
import pandas as pd
from matplotlib.figure import Figure

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402


def _save(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
        metadata={"Software": "flock deterministic study exporter"},
    )
    plt.close(fig)


def experimental_topology(path: Path) -> Path:
    """Show the treatment cells and the true inferential hierarchy."""
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.axis("off")
    cells = [
        (0.29, 0.72, "LLM × homogeneous   |   LLM × heterogeneous"),
        (0.29, 0.48, "Classical × homogeneous   |   Classical × heterogeneous"),
    ]
    for x, y, label in cells:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=11,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": "#e8f1fa", "edgecolor": "#335f8a"},
        )
    ax.text(
        0.79,
        0.60,
        "One paired block effect\nper independent trajectory/window",
        ha="center",
        va="center",
        fontsize=11,
        bbox={"boxstyle": "round,pad=0.6", "facecolor": "#fff2cc", "edgecolor": "#9a7611"},
    )
    for y in (0.72, 0.48):
        ax.annotate("", xy=(0.64, 0.60), xytext=(0.52, y), arrowprops={"arrowstyle": "->"})
    ax.text(
        0.5,
        0.18,
        "Nested observations: agents • pairs • symbols • steps • prompts • calls • retries\n"
        "These improve measurement but never increase confirmatory independent n.",
        ha="center",
        va="center",
        fontsize=10,
        color="#4a4a4a",
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f3f3f3", "edgecolor": "#777777"},
    )
    ax.set_title("Experimental topology and independent-unit hierarchy", fontsize=14, pad=12)
    _save(fig, path)
    return path


def block_effect_forest(
    bundle_dir: Path,
    path: Path,
    sesoi: float = 0.10,
    *,
    estimand_id: str | None = None,
    metric: str | None = None,
) -> Path:
    """Plot every independent block plus the study mean and confidence interval."""
    blocks = pd.read_parquet(bundle_dir / "block_effects.parquet").sort_values(
        "independent_block"
    )
    effects = pd.read_parquet(bundle_dir / "effects.parquet")
    if estimand_id is not None:
        blocks = blocks.loc[blocks["estimand_id"].astype(str) == estimand_id]
        effects = effects.loc[effects["estimand_id"].astype(str) == estimand_id]
    if metric is not None:
        blocks = blocks.loc[blocks["metric"].astype(str) == metric]
        effects = effects.loc[effects["metric"].astype(str) == metric]
    if blocks.empty or len(effects) != 1:
        raise ValueError("H1 forest requires block effects and exactly one aggregate effect")
    block_names = cast(pd.Series, blocks["independent_block"]).astype(str).tolist()
    values = cast(pd.Series, blocks["effect"]).astype(float).tolist()
    aggregate = effects.iloc[0]
    mean = float(aggregate["estimate"])
    low = float(aggregate["ci95_low"])
    high = float(aggregate["ci95_high"])
    y = list(range(len(values), 0, -1))
    fig_height = max(4.2, 0.38 * len(values) + 2.0)
    fig, ax = plt.subplots(figsize=(9.5, fig_height))
    ax.axvline(0, color="#303030", linewidth=1.1, label="zero")
    ax.axvline(sesoi, color="#b24b32", linewidth=1.1, linestyle="--", label=f"SESOI = {sesoi:.2f}")
    ax.scatter(values, y, s=42, color="#356a9a", zorder=3, label="independent block")
    ax.errorbar(
        mean,
        0,
        xerr=[[mean - low], [high - mean]],
        fmt="D",
        markersize=7,
        capsize=5,
        color="#8a2d3c",
        linewidth=2,
        label="mean and 95% interval",
    )
    ax.set_yticks([*y, 0], [*block_names, "Study mean"])
    outcome = "Cohen's κ" if metric in (None, "kappa") else metric
    ax.set_xlabel(f"Independent-block contrast ({outcome})")
    ax.set_title("H1 block-level effects; each point is one independent unit")
    ax.grid(axis="x", alpha=0.2)
    ax.legend(loc="best", frameon=False)
    _save(fig, path)
    return path


def export_core_study_figures(
    bundle_dir: Path,
    *,
    sesoi: float = 0.10,
    estimand_id: str | None = None,
    metric: str | None = None,
) -> tuple[Path, Path]:
    """Render the core figures using the bundle's resolved practical threshold."""
    figures = bundle_dir / "figures"
    return (
        experimental_topology(figures / "independent-unit-topology.png"),
        block_effect_forest(
            bundle_dir,
            figures / "h1-block-effects.png",
            sesoi=sesoi,
            estimand_id=estimand_id,
            metric=metric,
        ),
    )
