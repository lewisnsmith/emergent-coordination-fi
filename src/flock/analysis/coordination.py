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


@dataclass(frozen=True)
class HoldingsChangePanel:
    """Quarterly 13F activity plus explicit coverage and exclusion records."""

    activity: pd.DataFrame
    period_coverage: pd.DataFrame
    unmatched: pd.DataFrame


def buy_sell_counts(decisions: pd.DataFrame, agents: list[str]) -> pd.DataFrame:
    """Per (step, symbol): number of cohort agents buying and selling.

    An agent counts once per (step, symbol) by the sign of its net clipped
    flow there. These are intended clipped orders, not executed fills.
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
        return pd.DataFrame(
            columns=[
                "step",
                "symbol",
                "buy",
                "sell",
                "n_active",
                "n_eligible",
                "activity_rate",
                "decision_basis",
                "execution_status",
            ]
        )
    grouped = cast(
        pd.DataFrame,
        pd.DataFrame(rows).groupby(["step", "symbol"], as_index=False)[
            ["buy", "sell"]
        ].sum(),
    )
    grouped["n_active"] = grouped["buy"] + grouped["sell"]
    grouped["n_eligible"] = len(agents)
    grouped["activity_rate"] = grouped["n_active"] / grouped["n_eligible"]
    grouped["decision_basis"] = "intended_clipped_order"
    grouped["execution_status"] = "intended_not_executed"
    return cast(
        pd.DataFrame,
        grouped,
    )


def harmonize_13f_holdings_changes(panel: pd.DataFrame) -> HoldingsChangePanel:
    """Convert consecutive 13F holdings into a herding-compatible activity panel.

    Share-count changes, rather than market-value changes, proxy realized
    position changes. Only non-option ``SH`` positions enter the activity
    panel. Missing provenance, share amounts, unsupported instruments, first
    observations, and nonconsecutive quarters are retained in ``unmatched``.
    """
    required = {
        "manager",
        "period",
        "cusip",
        "shares",
        "accession",
        "filing_date",
    }
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"13F panel missing required columns: {missing}")

    work = panel.copy()
    work["period_timestamp"] = pd.to_datetime(work["period"], errors="coerce")
    if cast(pd.Series, work["period_timestamp"]).isna().any():
        raise ValueError("13F panel contains invalid report periods")
    work["period"] = cast(pd.Series, work["period_timestamp"]).dt.strftime("%Y-%m-%d")
    work["shares"] = pd.to_numeric(work["shares"], errors="coerce")
    for column, default in (
        ("shares_type", ""),
        ("put_call", ""),
        ("acceptance_datetime", ""),
        ("source_url", ""),
        ("value_usd", 0.0),
    ):
        if column not in work:
            work[column] = default
    work["shares_type"] = (
        cast(pd.Series, work["shares_type"]).fillna("").astype(str).str.upper()
    )
    work["put_call"] = (
        cast(pd.Series, work["put_call"]).fillna("").astype(str).str.upper()
    )

    unmatched_rows: list[dict[str, Any]] = []
    valid_period_keys: set[tuple[str, str]] = set()
    for raw_key, group in work.groupby(["manager", "period"], sort=True):
        manager, period = cast(tuple[Any, Any], raw_key)
        accessions = {
            str(value)
            for value in cast(pd.Series, group["accession"]).dropna()
            if str(value)
        }
        filing_dates = {
            str(value)
            for value in cast(pd.Series, group["filing_date"]).dropna()
            if str(value)
        }
        if len(accessions) != 1 or len(filing_dates) != 1:
            unmatched_rows.append(
                {
                    "unit_type": "manager_period",
                    "manager": str(manager),
                    "period": str(period),
                    "symbol": None,
                    "reason": "missing_or_ambiguous_filing_provenance",
                }
            )
            continue
        valid_period_keys.add((str(manager), str(period)))

    invalid_provenance = [
        (str(record["manager"]), str(record["period"])) not in valid_period_keys
        for record in cast(list[dict[str, Any]], work.to_dict("records"))
    ]
    work = cast(pd.DataFrame, work.loc[~pd.Series(invalid_provenance, index=work.index)])

    missing_shares = cast(pd.DataFrame, work[work["shares"].isna()])
    excluded_keys: set[tuple[str, str, str]] = set()
    for record in cast(list[dict[str, Any]], missing_shares.to_dict("records")):
        excluded_keys.add(
            (str(record["manager"]), str(record["period"]), str(record["cusip"]))
        )
        unmatched_rows.append(
            {
                "unit_type": "manager_period_instrument",
                "manager": record["manager"],
                "period": record["period"],
                "symbol": record["cusip"],
                "reason": "missing_share_amount",
            }
        )

    unsupported = cast(
        pd.DataFrame,
        work[
            work["shares"].notna()
            & ((work["shares_type"] != "SH") | (work["put_call"] != ""))
        ],
    )
    for record in cast(list[dict[str, Any]], unsupported.to_dict("records")):
        excluded_keys.add(
            (str(record["manager"]), str(record["period"]), str(record["cusip"]))
        )
        unmatched_rows.append(
            {
                "unit_type": "manager_period_instrument",
                "manager": record["manager"],
                "period": record["period"],
                "symbol": record["cusip"],
                "reason": "unsupported_position_type",
            }
        )
    work = cast(
        pd.DataFrame,
        work[
            work["shares"].notna()
            & (work["shares_type"] == "SH")
            & (work["put_call"] == "")
        ].copy(),
    )

    activity_rows: list[dict[str, Any]] = []
    eligible_by_period: dict[str, set[str]] = {}
    for manager, manager_rows in work.groupby("manager", sort=True):
        manager_frame = cast(pd.DataFrame, manager_rows)
        periods = sorted(
            cast(list[str], manager_frame["period"].drop_duplicates().tolist())
        )
        for period_index, period in enumerate(periods):
            if period_index == 0:
                unmatched_rows.append(
                    {
                        "unit_type": "manager_period",
                        "manager": str(manager),
                        "period": period,
                        "symbol": None,
                        "reason": "missing_prior_period",
                    }
                )
                continue
            prior_period = periods[period_index - 1]
            current_quarter = cast(pd.Period, pd.Period(period, freq="Q"))
            prior_quarter = cast(pd.Period, pd.Period(prior_period, freq="Q"))
            if current_quarter.ordinal - prior_quarter.ordinal != 1:
                unmatched_rows.append(
                    {
                        "unit_type": "manager_period",
                        "manager": str(manager),
                        "period": period,
                        "symbol": None,
                        "reason": "nonconsecutive_prior_period",
                    }
                )
                continue

            prior = cast(
                pd.DataFrame,
                manager_frame[manager_frame["period"] == prior_period],
            )
            current = cast(
                pd.DataFrame,
                manager_frame[manager_frame["period"] == period],
            )
            prior_holdings = cast(pd.Series, prior.groupby("cusip")["shares"].sum())
            current_holdings = cast(pd.Series, current.groupby("cusip")["shares"].sum())
            symbols = sorted(set(prior_holdings.index) | set(current_holdings.index))
            eligible_by_period.setdefault(period, set()).add(str(manager))

            prior_provenance = cast(dict[str, Any], prior.iloc[0].to_dict())
            current_provenance = cast(dict[str, Any], current.iloc[0].to_dict())
            for symbol in symbols:
                comparison_keys = {
                    (str(manager), prior_period, str(symbol)),
                    (str(manager), period, str(symbol)),
                }
                if comparison_keys & excluded_keys:
                    unmatched_rows.append(
                        {
                            "unit_type": "manager_period_instrument_comparison",
                            "manager": str(manager),
                            "period": period,
                            "symbol": str(symbol),
                            "reason": "comparison_input_excluded",
                        }
                    )
                    continue
                previous_shares = (
                    float(prior_holdings.loc[symbol])
                    if symbol in prior_holdings.index
                    else 0.0
                )
                current_shares = (
                    float(current_holdings.loc[symbol])
                    if symbol in current_holdings.index
                    else 0.0
                )
                delta_shares = current_shares - previous_shares
                if delta_shares == 0:
                    continue
                activity_rows.append(
                    {
                        "step": period,
                        "period": period,
                        "prior_period": prior_period,
                        "symbol": str(symbol),
                        "agent_id": str(manager),
                        "manager": str(manager),
                        "buy": float(delta_shares > 0),
                        "sell": float(delta_shares < 0),
                        "previous_shares": previous_shares,
                        "current_shares": current_shares,
                        "delta_shares": delta_shares,
                        "prior_accession": prior_provenance["accession"],
                        "accession": current_provenance["accession"],
                        "prior_filing_date": prior_provenance["filing_date"],
                        "filing_date": current_provenance["filing_date"],
                        "prior_acceptance_datetime": prior_provenance[
                            "acceptance_datetime"
                        ],
                        "acceptance_datetime": current_provenance[
                            "acceptance_datetime"
                        ],
                        "prior_source_url": prior_provenance["source_url"],
                        "source_url": current_provenance["source_url"],
                        "decision_basis": "realized_holdings_change",
                        "execution_status": "realized_position_not_order_level",
                    }
                )

    coverage_rows = [
        {
            "step": period,
            "period": period,
            "n_eligible": len(managers),
            "eligible_managers": sorted(managers),
        }
        for period, managers in sorted(eligible_by_period.items())
    ]
    activity_columns = [
        "step",
        "period",
        "prior_period",
        "symbol",
        "agent_id",
        "manager",
        "buy",
        "sell",
        "previous_shares",
        "current_shares",
        "delta_shares",
        "prior_accession",
        "accession",
        "prior_filing_date",
        "filing_date",
        "prior_acceptance_datetime",
        "acceptance_datetime",
        "prior_source_url",
        "source_url",
        "decision_basis",
        "execution_status",
    ]
    unmatched_columns = ["unit_type", "manager", "period", "symbol", "reason"]
    return HoldingsChangePanel(
        activity=pd.DataFrame(activity_rows, columns=activity_columns),
        period_coverage=pd.DataFrame(
            coverage_rows,
            columns=["step", "period", "n_eligible", "eligible_managers"],
        ),
        unmatched=pd.DataFrame(unmatched_rows, columns=unmatched_columns),
    )


def holdings_change_counts(harmonized: HoldingsChangePanel) -> pd.DataFrame:
    """Aggregate realized 13F activity for canonical period-specific LSV."""
    if harmonized.activity.empty:
        return pd.DataFrame(
            columns=[
                "step",
                "symbol",
                "buy",
                "sell",
                "n_active",
                "n_eligible",
                "activity_rate",
                "decision_basis",
                "execution_status",
            ]
        )
    counts = cast(
        pd.DataFrame,
        harmonized.activity.groupby(["step", "symbol"], as_index=False)[
            ["buy", "sell"]
        ].sum(),
    )
    counts["n_active"] = counts["buy"] + counts["sell"]
    coverage = cast(
        dict[Any, Any],
        harmonized.period_coverage.set_index("step")["n_eligible"].to_dict(),
    )
    counts["n_eligible"] = counts["step"].map(lambda step: coverage[step])
    counts["activity_rate"] = counts["n_active"] / counts["n_eligible"]
    counts["decision_basis"] = "realized_holdings_change"
    counts["execution_status"] = "realized_position_not_order_level"
    return counts


def activity_match_report(
    reference_counts: pd.DataFrame,
    comparison_counts: pd.DataFrame,
    *,
    min_traders: int = 3,
    activity_rate_tolerance: float = 0.0,
    require_same_basis: bool = True,
) -> pd.DataFrame:
    """Report whether every cell has a comparable activity stratum.

    Matching requires the same active-trader count and activity rate within
    ``activity_rate_tolerance``. By default it also rejects an intended-order
    versus realized-holdings comparison rather than silently treating the two
    as executed behavior.
    """
    required = {
        "step",
        "symbol",
        "buy",
        "sell",
        "n_active",
        "n_eligible",
        "activity_rate",
        "decision_basis",
    }
    for label, frame in (
        ("reference", reference_counts),
        ("comparison", comparison_counts),
    ):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{label} counts missing activity columns: {missing}")
    if activity_rate_tolerance < 0:
        raise ValueError("activity_rate_tolerance must be nonnegative")

    rows: list[dict[str, Any]] = []
    frames = {
        "reference": reference_counts,
        "comparison": comparison_counts,
    }
    for panel_name, frame in frames.items():
        other_name = "comparison" if panel_name == "reference" else "reference"
        other = frames[other_name]
        for record in cast(list[dict[str, Any]], frame.to_dict("records")):
            n_active = int(record["n_active"])
            activity_rate = float(record["activity_rate"])
            candidates = cast(
                pd.DataFrame,
                other[
                    (other["n_active"] == n_active)
                    & (
                        (other["activity_rate"] - activity_rate).abs()
                        <= activity_rate_tolerance
                    )
                ],
            )
            activity_matched = n_active >= min_traders and not candidates.empty
            basis_matched = (
                not candidates.empty
                and cast(pd.Series, candidates["decision_basis"])
                .eq(record["decision_basis"])
                .any()
            )
            matched = activity_matched and (
                basis_matched or not require_same_basis
            )
            if n_active < min_traders:
                reason = "below_min_traders"
            elif candidates.empty:
                reason = "no_matching_activity_stratum"
            elif require_same_basis and not basis_matched:
                reason = "decision_basis_mismatch"
            else:
                reason = "matched"
            rows.append(
                {
                    "panel": panel_name,
                    "step": record["step"],
                    "symbol": record["symbol"],
                    "n_active": n_active,
                    "n_eligible": int(record["n_eligible"]),
                    "activity_rate": activity_rate,
                    "decision_basis": record["decision_basis"],
                    "activity_matched": activity_matched,
                    "basis_matched": basis_matched,
                    "matched": matched,
                    "reason": reason,
                }
            )
    return pd.DataFrame(rows)


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
            columns=[
                "step",
                "symbol",
                "n",
                "buy_fraction",
                "expected_buy_fraction",
                "af",
                "h",
                "decision_basis",
                "execution_status",
            ]
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
                "decision_basis": record.get("decision_basis", "unspecified"),
                "execution_status": record.get("execution_status", "unspecified"),
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


def sias_decomposition_from_panel(
    panel: pd.DataFrame, min_traders: int = 2
) -> SiasDecomposition:
    """Decompose serial demand correlation into own- and other-agent terms.

    The expansion is algebraically identical to the Sias aggregate correlation:
    products where the current and lagged decision share an agent contribute to
    ``following_own``; all cross-agent products contribute to ``following_others``.
    Only active traders enter each security-period buyer ratio.
    """
    if panel.empty:
        return SiasDecomposition(*(float("nan"),) * 3, period_pairs=0)
    required = {"step", "symbol", "agent_id", "buy"}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Sias activity panel missing columns: {missing}")
    grouped: dict[tuple[Any, str], pd.DataFrame] = {}
    for raw_key, group in panel.groupby(["step", "symbol"]):
        step, symbol = cast(tuple[Any, Any], raw_key)
        if len(group) >= min_traders:
            grouped[(step, str(symbol))] = cast(pd.DataFrame, group)
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


def sias_decomposition(
    decisions: pd.DataFrame, agents: list[str], min_traders: int = 2
) -> SiasDecomposition:
    """Build an intended-order direction panel and apply Sias decomposition."""
    return sias_decomposition_from_panel(
        _agent_direction_panel(decisions, agents),
        min_traders=min_traders,
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
