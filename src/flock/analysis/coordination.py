"""Herding and cascade metrics (docs/research/03): LSV, Sias, cascades.

All functions consume the decisions DataFrame from a run (any market kind);
LSV/Sias are also applied to real-world panels (13F) for the H2 anchor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import pandas as pd
from scipy.stats import binom


def buy_sell_counts(decisions: pd.DataFrame, agents: list[str]) -> pd.DataFrame:
    """Per (step, symbol): number of cohort agents buying and selling.

    An agent counts once per (step, symbol) by the sign of its net clipped
    flow there — the trade-level analogue of LSV's holdings-change sign.
    """
    rows: list[dict[str, Any]] = []
    sub = cast(pd.DataFrame, decisions[decisions["agent_id"].isin(agents)])
    records = cast(list[dict[str, Any]], sub.to_dict("records"))
    for rec in records:
        net: dict[str, float] = {}
        for o in rec["orders_clipped"]:
            signed = o["quantity"] if o["side"] == "buy" else -o["quantity"]
            net[o["symbol"]] = net.get(o["symbol"], 0.0) + signed
        for symbol, flow in net.items():
            if flow:
                rows.append(
                    {
                        "step": rec["step"],
                        "symbol": symbol,
                        "buy": int(flow > 0),
                        "sell": int(flow < 0),
                    }
                )
    if not rows:
        return pd.DataFrame(columns=["step", "symbol", "buy", "sell"])
    grouped = pd.DataFrame(rows).groupby(["step", "symbol"], as_index=False)[
        ["buy", "sell"]
    ].sum()
    return cast(
        pd.DataFrame,
        grouped,
    )


def lsv_cell_statistics(counts: pd.DataFrame, min_traders: int = 3) -> pd.DataFrame:
    """Return auditable LSV cell terms using each period's expected buy fraction."""
    active = cast(pd.DataFrame, counts[(counts["buy"] + counts["sell"]) > 0].copy())
    active["n"] = active["buy"] + active["sell"]
    period_totals = cast(
        pd.DataFrame, active.groupby("step")[["buy", "n"]].sum()
    )
    period_buy_fraction = cast(
        pd.Series,
        cast(pd.Series, period_totals["buy"])
        / cast(pd.Series, period_totals["n"]),
    )
    eligible = cast(
        pd.DataFrame,
        active[active["n"] >= min_traders].copy(),
    )
    if eligible.empty:
        return pd.DataFrame(
            columns=["step", "symbol", "n", "buy_fraction", "expected_buy_fraction", "af", "h"]
        )
    rows: list[dict[str, Any]] = []
    for record in cast(list[dict[str, Any]], eligible.to_dict("records")):
        n_i = int(record["n"])
        buy_fraction = float(record["buy"]) / n_i
        expected = float(period_buy_fraction.loc[record["step"]])
        possible_buys = np.arange(n_i + 1)
        adjustment = float(
            np.sum(
                binom.pmf(possible_buys, n_i, expected)
                * np.abs(possible_buys / n_i - expected)
            )
        )
        rows.append(
            {
                "step": record["step"],
                "symbol": record["symbol"],
                "n": n_i,
                "buy_fraction": buy_fraction,
                "expected_buy_fraction": expected,
                "af": adjustment,
                "h": abs(buy_fraction - expected) - adjustment,
            }
        )
    return pd.DataFrame(rows)


def lsv_herding(counts: pd.DataFrame, min_traders: int = 3) -> float:
    """Lakonishok–Shleifer–Vishny herding statistic.

    H(t,s) = |p(t,s) − p̄(t)| − AF(t,s), averaged over cells with enough active
    traders. AF is the expected deviation under a binomial null at the
    contemporaneous market-wide buy fraction p̄(t), as in the canonical LSV
    construction. A pooled all-period fraction would confound market direction
    with cross-sectional herding.
    Positive values indicate herding beyond chance.
    """
    cells = lsv_cell_statistics(counts, min_traders=min_traders)
    if cells.empty:
        return float("nan")
    return float(cast(pd.Series, cells["h"]).mean())


@dataclass(frozen=True)
class SiasDecomposition:
    full: float
    following_own: float
    following_others: float
    period_pairs: int


def _agent_direction_panel(decisions: pd.DataFrame, agents: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    selected = cast(pd.DataFrame, decisions[decisions["agent_id"].isin(agents)])
    records = cast(
        list[dict[str, Any]],
        selected.to_dict("records"),
    )
    for record in records:
        net: dict[str, float] = {}
        for order in record["orders_clipped"]:
            sign = 1.0 if order["side"] == "buy" else -1.0
            net[order["symbol"]] = net.get(order["symbol"], 0.0) + sign * float(
                order["quantity"]
            )
        for symbol, flow in net.items():
            if flow:
                rows.append(
                    {
                        "step": record["step"],
                        "symbol": symbol,
                        "agent_id": record["agent_id"],
                        "buy": float(flow > 0),
                    }
                )
    return pd.DataFrame(rows, columns=["step", "symbol", "agent_id", "buy"])


def sias_decomposition(
    decisions: pd.DataFrame, agents: list[str], min_traders: int = 2
) -> SiasDecomposition:
    """Decompose serial demand correlation into own- and other-agent terms.

    The expansion is algebraically identical to the Sias aggregate correlation:
    products where the current and lagged decision share an agent contribute to
    ``following_own``; all cross-agent products contribute to ``following_others``.
    Only active traders enter each security-period buyer ratio.
    """
    panel = _agent_direction_panel(decisions, agents)
    if panel.empty:
        return SiasDecomposition(*(float("nan"),) * 3, period_pairs=0)
    grouped: dict[tuple[int, str], pd.DataFrame] = {}
    for raw_key, group in panel.groupby(["step", "symbol"]):
        step, symbol = cast(tuple[Any, Any], raw_key)
        if len(group) >= min_traders:
            grouped[(int(step), str(symbol))] = cast(pd.DataFrame, group)
    own_terms: list[float] = []
    other_terms: list[float] = []
    pair_full: list[float] = []
    steps = sorted({key[0] for key in grouped})
    for previous_step, current_step in zip(steps[:-1], steps[1:], strict=False):
        symbols = sorted(
            {symbol for step, symbol in grouped if step == previous_step}
            & {symbol for step, symbol in grouped if step == current_step}
        )
        if len(symbols) < 3:
            continue
        previous = {symbol: grouped[(previous_step, symbol)] for symbol in symbols}
        current = {symbol: grouped[(current_step, symbol)] for symbol in symbols}
        previous_ratios = np.array(
            [float(cast(pd.Series, previous[symbol]["buy"]).mean()) for symbol in symbols]
        )
        current_ratios = np.array(
            [float(cast(pd.Series, current[symbol]["buy"]).mean()) for symbol in symbols]
        )
        previous_centered = previous_ratios - previous_ratios.mean()
        current_centered = current_ratios - current_ratios.mean()
        denominator = float(
            np.sqrt(np.sum(previous_centered**2) * np.sum(current_centered**2))
        )
        if denominator <= 0:
            continue
        own_numerator = 0.0
        other_numerator = 0.0
        for symbol in symbols:
            previous_rows = cast(
                list[dict[str, Any]], previous[symbol].to_dict("records")
            )
            current_rows = cast(list[dict[str, Any]], current[symbol].to_dict("records"))
            scale = len(previous_rows) * len(current_rows)
            for current_record in current_rows:
                current_value = float(current_record["buy"]) - current_ratios.mean()
                for previous_record in previous_rows:
                    product = current_value * (
                        float(previous_record["buy"]) - previous_ratios.mean()
                    ) / scale
                    if current_record["agent_id"] == previous_record["agent_id"]:
                        own_numerator += product
                    else:
                        other_numerator += product
        own = own_numerator / denominator
        other = other_numerator / denominator
        own_terms.append(own)
        other_terms.append(other)
        pair_full.append(own + other)
    if not pair_full:
        return SiasDecomposition(*(float("nan"),) * 3, period_pairs=0)
    return SiasDecomposition(
        full=float(np.mean(pair_full)),
        following_own=float(np.mean(own_terms)),
        following_others=float(np.mean(other_terms)),
        period_pairs=len(pair_full),
    )


def sias_herding(counts: pd.DataFrame, min_traders: int = 2) -> float:
    """Sias (2004) serial herding: cross-sectional correlation of standardized
    buyer fractions between consecutive steps, averaged over steps."""
    counts = cast(
        pd.DataFrame,
        counts[(counts["buy"] + counts["sell"]) >= min_traders].copy(),
    )
    if counts.empty:
        return float("nan")
    counts["p"] = counts["buy"] / (counts["buy"] + counts["sell"])
    wide = cast(
        pd.DataFrame,
        counts.pivot_table(index="step", columns="symbol", values="p"),
    )
    std = cast(pd.DataFrame, wide.sub(wide.mean(axis=1), axis=0))
    corrs = []
    steps = sorted(wide.index)
    for t_prev, t in zip(steps[:-1], steps[1:], strict=False):
        a = cast(pd.Series, std.loc[t_prev])
        b_ = cast(pd.Series, std.loc[t])
        mask = a.notna() & b_.notna()
        if mask.sum() >= 3 and a[mask].std() > 0 and b_[mask].std() > 0:
            corrs.append(float(np.corrcoef(a[mask], b_[mask])[0, 1]))
    return float(np.mean(corrs)) if corrs else float("nan")


def net_flow_series(decisions: pd.DataFrame, agents: list[str]) -> pd.Series:
    """Per-step signed net order flow of a cohort (sum over symbols)."""
    sub = cast(pd.DataFrame, decisions[decisions["agent_id"].isin(agents)])
    flows: dict[int, float] = {}
    records = cast(list[dict[str, Any]], sub.to_dict("records"))
    for rec in records:
        for o in rec["orders_clipped"]:
            signed = o["quantity"] if o["side"] == "buy" else -o["quantity"]
            step = cast(int, rec["step"])
            flows[step] = flows.get(step, 0.0) + signed
    steps = sorted(decisions["step"].unique())
    return pd.Series([flows.get(s, 0.0) for s in steps], index=steps)


def detect_cascades(
    flow: pd.Series, n_permutations: int = 1000, min_length: int = 3,
    active_percentile: float = 90.0, seed: int = 0,
) -> dict:
    """One-sided flow runs, calibrated by time-permutation of the series.

    "Active" steps are those with |flow| above the given percentile of the
    series' own |flow| (permutation-invariant, so observed and null use the
    same definition). A cascade is >= min_length consecutive active steps of
    same-sign flow. The null permutes the series in time — breaking serial
    structure while preserving marginals — and the p-value is the fraction
    of permutations whose longest same-sign active run reaches the observed
    maximum.
    """
    values = flow.to_numpy()
    if len(values) == 0 or np.all(values == 0):
        return {"threshold": 0.0, "n_cascades": 0, "mean_length": 0.0,
                "max_length": 0, "p_value": 1.0}
    threshold = float(np.percentile(np.abs(values), active_percentile))

    def runs(v: np.ndarray) -> list[int]:
        lengths, run, sign = [], 0, 0
        for x in v:
            s = 0 if abs(x) <= threshold else (1 if x > 0 else -1)
            if s != 0 and s == sign:
                run += 1
            else:
                if run >= min_length:
                    lengths.append(run)
                run = 1 if s != 0 else 0
                sign = s
        if run >= min_length:
            lengths.append(run)
        return lengths

    observed = runs(values)
    max_obs = max(observed) if observed else 0
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_permutations):
        perm_runs = runs(rng.permutation(values))
        if (max(perm_runs) if perm_runs else 0) >= max(max_obs, min_length):
            hits += 1
    return {
        "threshold": threshold,
        "n_cascades": len(observed),
        "mean_length": float(np.mean(observed)) if observed else 0.0,
        "max_length": max_obs,
        "p_value": (hits + 1) / (n_permutations + 1),
    }


def coordination_metrics(decisions: pd.DataFrame, cohort: str) -> dict:
    agents = cast(
        list[str],
        sorted(decisions.loc[decisions["cohort"] == cohort, "agent_id"].unique()),
    )
    counts = buy_sell_counts(decisions, agents)
    sias = sias_decomposition(decisions, agents)
    flow = net_flow_series(decisions, agents)
    cascades = detect_cascades(flow)
    return {
        "lsv": lsv_herding(counts),
        "sias": sias.full,
        "sias_following_own": sias.following_own,
        "sias_following_others": sias.following_others,
        "cascade_count": cascades["n_cascades"],
        "cascade_max_length": cascades["max_length"],
    }


def overlap_13f(panel: pd.DataFrame) -> float:
    """Mean pairwise portfolio overlap among real managers, per period —
    the empirical anchor comparable to `convergence.mean_portfolio_overlap`."""
    overlaps: list[float] = []
    for _, g in panel.groupby("period"):
        weights: dict[str, pd.Series] = {}
        for manager, gm in cast(pd.DataFrame, g).groupby("manager"):
            w = cast(pd.Series, gm.groupby("cusip")["value_usd"].sum())
            total = float(w.sum())
            if total > 0:
                weights[cast(str, manager)] = cast(pd.Series, w / total)
        managers = sorted(weights)
        for i, a in enumerate(managers):
            for b_ in managers[i + 1 :]:
                joined = pd.concat([weights[a], weights[b_]], axis=1).fillna(0.0)
                overlaps.append(float(joined.min(axis=1).sum()))
    return float(np.mean(overlaps)) if overlaps else float("nan")
