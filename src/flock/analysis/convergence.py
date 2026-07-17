"""Decision- and portfolio-level convergence metrics (docs/research/03).

All functions consume the run outputs (decisions.jsonl, portfolio.parquet)
loaded into DataFrames by `load_run`.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

ACTIONS = ("buy", "sell", "hold")


def load_run(run_dir: Path) -> dict[str, Any]:
    decisions = pd.read_json(run_dir / "decisions.jsonl", lines=True)
    portfolio = pd.read_parquet(run_dir / "portfolio.parquet")
    with open(run_dir / "manifest.json") as f:
        manifest = json.load(f)
    return {"decisions": decisions, "portfolio": portfolio, "manifest": manifest}


def action_matrix(decisions: pd.DataFrame, agents: list[str]) -> pd.DataFrame:
    """(step, symbol) × agents matrix of intended/clipped actions.

    New logs include the complete symbol universe on every row and are scored
    from ``orders_clipped``.  The fallback preserves compatibility with older
    logs that contain only one net action per step, but confirmatory runs must
    pass the run verifier, which rejects that legacy representation.
    """
    sub = cast(pd.DataFrame, decisions[decisions["agent_id"].isin(agents)])
    if "orders_clipped" not in sub.columns:
        pivoted = sub.pivot_table(
            index="step", columns="agent_id", values="action", aggfunc="first"
        )
        return cast(pd.DataFrame, cast(pd.DataFrame, pivoted)[agents])
    orders_column = cast(pd.Series, sub["orders_clipped"])
    if not any(bool(value) for value in orders_column):
        pivoted = sub.pivot_table(
            index="step", columns="agent_id", values="action", aggfunc="first"
        )
        return cast(pd.DataFrame, cast(pd.DataFrame, pivoted)[agents])

    symbols: set[str] = set()
    if "symbols" in sub.columns:
        for values in cast(pd.Series, sub["symbols"]):
            symbols.update(values)
    for orders in orders_column:
        symbols.update(order["symbol"] for order in orders)
    if not symbols:
        raise ValueError("cannot construct per-symbol actions without a symbol universe")

    rows: list[dict[str, Any]] = []
    records = cast(list[dict[str, Any]], sub.to_dict("records"))
    for rec in records:
        net = dict.fromkeys(symbols, 0.0)
        for order in rec["orders_clipped"]:
            sign = 1.0 if order["side"] == "buy" else -1.0
            net[order["symbol"]] += sign * float(order["quantity"])
        for symbol in sorted(symbols):
            value = net[symbol]
            rows.append(
                {
                    "step": rec["step"],
                    "symbol": symbol,
                    "agent_id": rec["agent_id"],
                    "action": "buy" if value > 0 else "sell" if value < 0 else "hold",
                }
            )
    long = pd.DataFrame(rows)
    pivoted = long.pivot_table(
        index=["step", "symbol"], columns="agent_id", values="action", aggfunc="first"
    )
    return cast(pd.DataFrame, cast(pd.DataFrame, pivoted)[agents])


def pairwise_agreement(mat: pd.DataFrame) -> float:
    """Mean over agent pairs of per-(step, symbol) action agreement rate."""
    pairs = list(itertools.combinations(mat.columns, 2))
    if not pairs:
        return float("nan")
    vals = [float((mat[a] == mat[b]).mean()) for a, b in pairs]
    return float(np.mean(vals))


def cohen_kappa(x: pd.Series, y: pd.Series) -> float:
    """Chance-corrected agreement for one agent pair."""
    po = float((x == y).mean())
    pe = sum(float((x == a).mean()) * float((y == a).mean()) for a in ACTIONS)
    if pe >= 1.0:
        return 0.0  # both degenerate on one action: no information beyond chance
    return (po - pe) / (1 - pe)


def mean_pairwise_kappa(mat: pd.DataFrame) -> float:
    pairs = list(itertools.combinations(mat.columns, 2))
    if not pairs:
        return float("nan")
    return float(
        np.mean(
            [
                cohen_kappa(cast(pd.Series, mat[a]), cast(pd.Series, mat[b]))
                for a, b in pairs
            ]
        )
    )


def weights_over_time(portfolio: pd.DataFrame, agents: list[str]) -> dict[str, pd.DataFrame]:
    """agent -> steps x symbols weight matrix."""
    out: dict[str, pd.DataFrame] = {}
    sub = cast(pd.DataFrame, portfolio[portfolio["agent_id"].isin(agents)])
    symbols = sorted(
        {s for w in cast(pd.Series, sub["weights"]) for s in json.loads(w)}
    )
    for agent, g in sub.groupby("agent_id"):
        sorted_g = cast(pd.DataFrame, g).sort_values(by="step")
        rows = [
            {**dict.fromkeys(symbols, 0.0), **json.loads(w)}
            for w in cast(pd.Series, sorted_g["weights"])
        ]
        out[cast(str, agent)] = pd.DataFrame(
            rows, columns=symbols, index=cast(pd.Series, sorted_g["step"])
        )
    return out


def mean_position_cosine(weights: dict[str, pd.DataFrame]) -> float:
    """Mean over pairs and steps of cosine similarity between weight vectors.

    Steps where either agent holds nothing are skipped (cosine undefined).
    """
    pairs = list(itertools.combinations(weights.keys(), 2))
    vals = []
    for a, b in pairs:
        wa, wb = weights[a].to_numpy(), weights[b].to_numpy()
        na = np.linalg.norm(wa, axis=1)
        nb = np.linalg.norm(wb, axis=1)
        mask = (na > 0) & (nb > 0)
        if not mask.any():
            continue
        cos = (wa[mask] * wb[mask]).sum(axis=1) / (na[mask] * nb[mask])
        vals.append(float(cos.mean()))
    return float(np.mean(vals)) if vals else float("nan")


def mean_portfolio_overlap(weights: dict[str, pd.DataFrame]) -> float:
    """Fund-overlap measure: sum_s min(w_i, w_j) on long weights, averaged."""
    pairs = list(itertools.combinations(weights.keys(), 2))
    vals = []
    for a, b in pairs:
        wa = np.clip(weights[a].to_numpy(), 0, None)
        wb = np.clip(weights[b].to_numpy(), 0, None)
        overlap = np.minimum(wa, wb).sum(axis=1)
        vals.append(float(overlap.mean()))
    return float(np.mean(vals)) if vals else float("nan")


def return_correlation(portfolio: pd.DataFrame, agents: list[str]) -> float:
    """Mean pairwise correlation of per-step equity returns."""
    sub = portfolio[portfolio["agent_id"].isin(agents)]
    eq = cast(
        pd.DataFrame,
        sub.pivot_table(index="step", columns="agent_id", values="equity"),
    )[agents]
    rets = cast(pd.DataFrame, eq.pct_change()).dropna()
    if len(rets) < 3:
        return float("nan")
    corr = cast(pd.DataFrame, rets.corr()).to_numpy()
    iu = np.triu_indices_from(corr, k=1)
    vals = corr[iu]
    vals = vals[~np.isnan(vals)]
    return float(vals.mean()) if len(vals) else float("nan")


def cohort_metrics(run: dict, cohort: str) -> dict[str, float]:
    """All convergence metrics for one cohort of a loaded run."""
    decisions, portfolio = run["decisions"], run["portfolio"]
    agents = cast(
        list[str],
        sorted(decisions.loc[decisions["cohort"] == cohort, "agent_id"].unique()),
    )
    mat = action_matrix(decisions, agents)
    weights = weights_over_time(portfolio, agents)
    return {
        "n_agents": len(agents),
        "agreement": pairwise_agreement(mat),
        "kappa": mean_pairwise_kappa(mat),
        "position_cosine": mean_position_cosine(weights),
        "portfolio_overlap": mean_portfolio_overlap(weights),
        "return_correlation": return_correlation(portfolio, agents),
        "parse_failure_rate": float(
            1 - decisions.loc[decisions["cohort"] == cohort, "parse_ok"].mean()
        ),
    }


def pairwise_kappa_matrix(decisions: pd.DataFrame, agents: list[str]) -> pd.DataFrame:
    """Symmetric agents x agents Cohen's kappa matrix (diagonal = 1)."""
    mat = action_matrix(decisions, agents)
    out = pd.DataFrame(np.eye(len(agents)), index=agents, columns=agents)
    for a, b in itertools.combinations(agents, 2):
        k = cohen_kappa(cast(pd.Series, mat[a]), cast(pd.Series, mat[b]))
        out.loc[a, b] = out.loc[b, a] = k
    return out


def mean_kappa_of_multiset(kappa: pd.DataFrame, agents: list[str]) -> float:
    """Mean pairwise kappa over an agent multiset (bootstrap resamples may
    repeat an agent; a self-pair scores 1 by definition)."""
    idx = kappa.index.get_indexer(agents)
    arr = kappa.to_numpy()[np.ix_(idx, idx)]
    iu = np.triu_indices(len(agents), k=1)
    return float(arr[iu].mean())


def kappa_for_agent_subset(decisions: pd.DataFrame, agents: list[str]) -> float:
    """Kappa on an arbitrary agent set — the statistic used by permutation tests."""
    return mean_pairwise_kappa(action_matrix(decisions, sorted(set(agents))))
