"""Independent-block estimators for the first-paper H1/H3/H4 design.

This module consumes already-aggregated experimental outputs and deliberately
keeps agents, pairs, steps, calls, retries, prompts, and response seeds below
the inferential unit.  Every reported test is performed on one effect per
independent trajectory/window block.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np
import pandas as pd

from flock.analysis.stats import bootstrap_ci, holm_bonferroni, paired_sign_flip_test

Technology = Literal["llm", "classical"]
Ecology = Literal["homogeneous", "heterogeneous"]

H1_CONTRASTS = (
    "H1.technology.homogeneous",
    "H1.technology.heterogeneous",
    "H1.technology_x_ecology",
)
H3_CONTRASTS = (
    "H3.same_model_vs_cross_provider",
    "H3.same_provider_vs_cross_provider",
)
H4_COMPONENTS = ("M", "P", "H", "I", "Q")
H4_CONTRASTS = (
    *(f"H4.mphiq.{component}" for component in H4_COMPONENTS),
    "H4.information_vs_profile",
    "H4.information_vs_question",
)

_IDENTITY_COLUMNS = (
    "independent_block",
    "dependence_cluster",
    "trajectory_id",
)
_NESTED_COLUMNS = {
    "agent_id",
    "agent_seed",
    "call_id",
    "model_seed",
    "pair_id",
    "prompt_id",
    "prompt_variant",
    "response_seed",
    "retry_id",
    "step",
    "step_id",
}
_PLACEHOLDER_IDENTIFIERS = {"", "none", "null", "unspecified", "unknown"}


@dataclass(frozen=True)
class FirstPaperEstimands:
    """Paper estimands and their independent-block audit trail."""

    block_values: pd.DataFrame
    block_effects: pd.DataFrame
    effects: pd.DataFrame
    multiplicity: dict[str, Any]


def _records(frame: pd.DataFrame, required: set[str], source: str) -> list[dict[str, Any]]:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing required columns: {missing}")
    if frame.empty:
        raise ValueError(f"{source} cannot be empty")
    return cast(list[dict[str, Any]], frame.to_dict("records"))


def _text(value: Any, column: str, source: str) -> str:
    result = str(value).strip()
    if result.lower() in _PLACEHOLDER_IDENTIFIERS or "config-required" in result.lower():
        raise ValueError(f"{source} has invalid {column} identifier {result!r}")
    return result


def _number(value: Any, column: str, source: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{source} {column} must be numeric") from error
    if not np.isfinite(result):
        raise ValueError(f"{source} {column} must be finite")
    return result


def _validate_identities(
    records: list[dict[str, Any]], source: str
) -> dict[str, tuple[str, str]]:
    """Validate the one-to-one block, dependence-cluster, trajectory mapping."""
    identities: dict[str, tuple[str, str]] = {}
    cluster_to_block: dict[str, str] = {}
    trajectory_to_block: dict[str, str] = {}
    for record in records:
        block = _text(record["independent_block"], "independent_block", source)
        cluster = _text(record["dependence_cluster"], "dependence_cluster", source)
        trajectory = _text(record["trajectory_id"], "trajectory_id", source)
        identity = (cluster, trajectory)
        if block in identities and identities[block] != identity:
            raise ValueError(f"{source} maps independent block {block!r} to multiple identities")
        prior_cluster_block = cluster_to_block.get(cluster)
        if prior_cluster_block is not None and prior_cluster_block != block:
            raise ValueError(
                f"{source} reuses dependence cluster {cluster!r} across independent blocks"
            )
        prior_trajectory_block = trajectory_to_block.get(trajectory)
        if prior_trajectory_block is not None and prior_trajectory_block != block:
            raise ValueError(
                f"{source} reuses trajectory {trajectory!r} across independent blocks"
            )
        identities[block] = identity
        cluster_to_block[cluster] = block
        trajectory_to_block[trajectory] = block
    if len(identities) < 2:
        raise ValueError(f"{source} requires at least two independent blocks")
    return identities


def _require_frozen_metrics(
    records: list[dict[str, Any]], metrics: tuple[str, ...], source: str
) -> None:
    observed = {_text(record["metric"], "metric", source) for record in records}
    expected = set(metrics)
    if observed != expected:
        raise ValueError(
            f"{source} metrics do not match the frozen family: "
            f"missing={sorted(expected - observed)}, unexpected={sorted(observed - expected)}"
        )


def _normalized_metrics(confirmatory_metrics: Sequence[str]) -> tuple[str, ...]:
    metrics = tuple(str(metric).strip() for metric in confirmatory_metrics)
    if not metrics or any(not metric for metric in metrics) or len(metrics) != len(set(metrics)):
        raise ValueError("confirmatory_metrics must be nonempty and unique")
    return metrics


def _crossed_block_values(
    frame: pd.DataFrame, metrics: tuple[str, ...]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, tuple[str, str]]]:
    source = "crossed rows"
    nested = sorted(column for column in _NESTED_COLUMNS if column in frame.columns)
    if nested and any(frame[column].notna().any() for column in nested):
        raise ValueError(
            "crossed rows must contain family-level aggregates, not nested observations: "
            f"{nested}"
        )
    required = set(_IDENTITY_COLUMNS) | {
        "metric",
        "technology",
        "ecology",
        "family",
        "value",
    }
    records = _records(frame, required, source)
    identities = _validate_identities(records, source)
    _require_frozen_metrics(records, metrics, source)

    rows: dict[tuple[str, str, str, str, str], tuple[float, float]] = {}
    for record in records:
        block = _text(record["independent_block"], "independent_block", source)
        metric = _text(record["metric"], "metric", source)
        technology = _text(record["technology"], "technology", source)
        ecology = _text(record["ecology"], "ecology", source)
        family = _text(record["family"], "family", source)
        if technology not in {"llm", "classical"}:
            raise ValueError(f"crossed rows has unknown technology {technology!r}")
        if ecology not in {"homogeneous", "heterogeneous"}:
            raise ValueError(f"crossed rows has unknown ecology {ecology!r}")
        value = _number(record["value"], "value", source)
        weight = _number(record.get("family_weight", 1.0), "family_weight", source)
        if weight <= 0:
            raise ValueError("crossed rows family_weight must be positive")
        key = (block, metric, technology, ecology, family)
        if key in rows:
            raise ValueError(f"duplicate crossed family row {key}")
        rows[key] = (value, weight)

    expected_families: dict[tuple[str, str], dict[str, float]] = {}
    for technology in ("llm", "classical"):
        for ecology in ("homogeneous", "heterogeneous"):
            definitions: list[dict[str, float]] = []
            for block in sorted(identities):
                for metric in metrics:
                    definition = {
                        family: weight
                        for (row_block, row_metric, row_technology, row_ecology, family), (
                            _value,
                            weight,
                        ) in rows.items()
                        if (row_block, row_metric, row_technology, row_ecology)
                        == (block, metric, technology, ecology)
                    }
                    if not definition:
                        raise ValueError(
                            "crossed rows is missing a complete technology x ecology cell: "
                            f"{(block, metric, technology, ecology)}"
                        )
                    definitions.append(definition)
            reference = definitions[0]
            for definition in definitions[1:]:
                if definition != reference:
                    raise ValueError(
                        "crossed rows changes the frozen family set or weights "
                        "across blocks/metrics: "
                        f"{(technology, ecology)}"
                    )
            expected_families[(technology, ecology)] = reference
    for technology in ("llm", "classical"):
        homogeneous = expected_families[(technology, "homogeneous")]
        heterogeneous = expected_families[(technology, "heterogeneous")]
        if homogeneous != heterogeneous:
            raise ValueError(
                "crossed rows changes the frozen family composition across ecologies for "
                f"{technology}"
            )

    block_values: list[dict[str, Any]] = []
    cell_values: dict[tuple[str, str, str, str], float] = {}
    for block in sorted(identities):
        cluster, trajectory = identities[block]
        for metric in metrics:
            for technology in ("llm", "classical"):
                for ecology in ("homogeneous", "heterogeneous"):
                    families = expected_families[(technology, ecology)]
                    total_weight = sum(families.values())
                    value = sum(
                        rows[(block, metric, technology, ecology, family)][0] * weight
                        for family, weight in families.items()
                    ) / total_weight
                    cell_values[(block, metric, technology, ecology)] = value
                    block_values.append(
                        {
                            "source": "H1-crossed",
                            "independent_block": block,
                            "dependence_cluster": cluster,
                            "trajectory_id": trajectory,
                            "metric": metric,
                            "condition": f"{technology}.{ecology}",
                            "value": value,
                            "family_count": len(families),
                            "nested_observations": 0,
                        }
                    )

    effects: list[dict[str, Any]] = []
    for block in sorted(identities):
        cluster, trajectory = identities[block]
        for metric in metrics:
            llm_h = cell_values[(block, metric, "llm", "homogeneous")]
            classical_h = cell_values[(block, metric, "classical", "homogeneous")]
            llm_x = cell_values[(block, metric, "llm", "heterogeneous")]
            classical_x = cell_values[(block, metric, "classical", "heterogeneous")]
            contrasts = {
                H1_CONTRASTS[0]: llm_h - classical_h,
                H1_CONTRASTS[1]: llm_x - classical_x,
                H1_CONTRASTS[2]: (llm_x - classical_x) - (llm_h - classical_h),
            }
            for estimand_id, effect in contrasts.items():
                nested_count = sum(
                    1
                    for row_block, row_metric, _technology, _ecology, _family in rows
                    if (row_block, row_metric) == (block, metric)
                )
                effects.append(
                    {
                        "hypothesis": "H1",
                        "estimand_id": estimand_id,
                        "independent_block": block,
                        "dependence_cluster": cluster,
                        "trajectory_id": trajectory,
                        "metric": metric,
                        "effect": effect,
                        "nested_observations_aggregated": nested_count,
                    }
                )
    return block_values, effects, identities


def _lineage_effects(
    frame: pd.DataFrame,
    metrics: tuple[str, ...],
    expected_identities: dict[str, tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source = "lineage rows"
    required = set(_IDENTITY_COLUMNS) | {
        "metric",
        "relationship",
        "family_stratum",
        "pair_id",
        "value",
    }
    records = _records(frame, required, source)
    identities = _validate_identities(records, source)
    if identities != expected_identities:
        raise ValueError("lineage rows must use exactly the crossed-design independent blocks")
    _require_frozen_metrics(records, metrics, source)
    relationships = ("same_model", "same_provider", "cross_provider")
    values: dict[tuple[str, str, str, str, str], float] = {}
    for record in records:
        block = _text(record["independent_block"], "independent_block", source)
        metric = _text(record["metric"], "metric", source)
        relationship = _text(record["relationship"], "relationship", source)
        stratum = _text(record["family_stratum"], "family_stratum", source)
        pair = _text(record["pair_id"], "pair_id", source)
        if relationship not in relationships:
            raise ValueError(f"lineage rows has unknown relationship {relationship!r}")
        key = (block, metric, relationship, stratum, pair)
        if key in values:
            raise ValueError(f"duplicate lineage pair row {key}")
        values[key] = _number(record["value"], "value", source)

    expected_strata: dict[str, set[str]] = {}
    for relationship in relationships:
        definitions: list[set[str]] = []
        for block in sorted(identities):
            for metric in metrics:
                strata = {
                    stratum
                    for row_block, row_metric, row_relationship, stratum, _pair in values
                    if (row_block, row_metric, row_relationship)
                    == (block, metric, relationship)
                }
                if not strata:
                    raise ValueError(
                        f"lineage rows is missing {(block, metric, relationship)}"
                    )
                definitions.append(strata)
        if any(definition != definitions[0] for definition in definitions[1:]):
            raise ValueError(
                f"lineage rows changes provider strata across blocks for {relationship}"
            )
        expected_strata[relationship] = definitions[0]

    block_values: list[dict[str, Any]] = []
    relationship_values: dict[tuple[str, str, str], float] = {}
    nested_counts: dict[tuple[str, str, str], int] = {}
    for block in sorted(identities):
        cluster, trajectory = identities[block]
        for metric in metrics:
            for relationship in relationships:
                stratum_means: list[float] = []
                nested_count = 0
                for stratum in sorted(expected_strata[relationship]):
                    pair_values = [
                        value
                        for (row_block, row_metric, row_relationship, row_stratum, _pair), value
                        in values.items()
                        if (row_block, row_metric, row_relationship, row_stratum)
                        == (block, metric, relationship, stratum)
                    ]
                    nested_count += len(pair_values)
                    stratum_means.append(float(np.mean(pair_values)))
                value = float(np.mean(stratum_means))
                relationship_values[(block, metric, relationship)] = value
                nested_counts[(block, metric, relationship)] = nested_count
                block_values.append(
                    {
                        "source": "H3-lineage",
                        "independent_block": block,
                        "dependence_cluster": cluster,
                        "trajectory_id": trajectory,
                        "metric": metric,
                        "condition": relationship,
                        "value": value,
                        "family_count": len(stratum_means),
                        "nested_observations": nested_count,
                    }
                )

    effects: list[dict[str, Any]] = []
    for block in sorted(identities):
        cluster, trajectory = identities[block]
        for metric in metrics:
            cross = relationship_values[(block, metric, "cross_provider")]
            contrasts = {
                H3_CONTRASTS[0]: relationship_values[(block, metric, "same_model")] - cross,
                H3_CONTRASTS[1]: relationship_values[(block, metric, "same_provider")] - cross,
            }
            for estimand_id, effect in contrasts.items():
                effects.append(
                    {
                        "hypothesis": "H3",
                        "estimand_id": estimand_id,
                        "independent_block": block,
                        "dependence_cluster": cluster,
                        "trajectory_id": trajectory,
                        "metric": metric,
                        "effect": effect,
                        "nested_observations_aggregated": sum(
                            nested_counts[(block, metric, relationship)]
                            for relationship in relationships
                        ),
                    }
                )
    return block_values, effects


def _mphiq_effects(
    frame: pd.DataFrame,
    metrics: tuple[str, ...],
    expected_identities: dict[str, tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source = "MPHIQ rows"
    required = set(_IDENTITY_COLUMNS) | {
        "metric",
        "component",
        "pair_id",
        "code_same",
        "code_different",
        "value_same",
        "value_different",
    }
    records = _records(frame, required, source)
    identities = _validate_identities(records, source)
    if identities != expected_identities:
        raise ValueError("MPHIQ rows must use exactly the crossed-design independent blocks")
    _require_frozen_metrics(records, metrics, source)
    pair_effects: dict[tuple[str, str, str, str], float] = {}
    for record in records:
        block = _text(record["independent_block"], "independent_block", source)
        metric = _text(record["metric"], "metric", source)
        component = _text(record["component"], "component", source).upper()
        pair = _text(record["pair_id"], "pair_id", source)
        same = str(record["code_same"]).strip()
        different = str(record["code_different"]).strip()
        if component not in H4_COMPONENTS:
            raise ValueError(f"MPHIQ rows has unknown component {component!r}")
        if len(same) != 5 or len(different) != 5 or set(same + different) - {"0", "1"}:
            raise ValueError("MPHIQ codes must be five binary MPHIQ bits")
        changed = [
            index
            for index, bits in enumerate(zip(same, different, strict=True))
            if bits[0] != bits[1]
        ]
        component_index = H4_COMPONENTS.index(component)
        oriented_same_to_different = (
            same[component_index] == "1" and different[component_index] == "0"
        )
        if changed != [component_index] or not oriented_same_to_different:
            raise ValueError(
                "MPHIQ rows must be Hamming-one pairs oriented from same (1) to different (0)"
            )
        key = (block, metric, component, pair)
        if key in pair_effects:
            raise ValueError(f"duplicate MPHIQ pair row {key}")
        pair_effects[key] = _number(
            record["value_different"], "value_different", source
        ) - _number(record["value_same"], "value_same", source)

    block_values: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []
    component_effects: dict[tuple[str, str, str], float] = {}
    for block in sorted(identities):
        cluster, trajectory = identities[block]
        for metric in metrics:
            for component in H4_COMPONENTS:
                nested = [
                    value
                    for (row_block, row_metric, row_component, _pair), value
                    in pair_effects.items()
                    if (row_block, row_metric, row_component) == (block, metric, component)
                ]
                if not nested:
                    raise ValueError(f"MPHIQ rows is missing {(block, metric, component)}")
                effect = float(np.mean(nested))
                component_effects[(block, metric, component)] = effect
                block_values.append(
                    {
                        "source": "H4-MPHIQ",
                        "independent_block": block,
                        "dependence_cluster": cluster,
                        "trajectory_id": trajectory,
                        "metric": metric,
                        "condition": component,
                        "value": effect,
                        "family_count": 0,
                        "nested_observations": len(nested),
                    }
                )
                effects.append(
                    {
                        "hypothesis": "H4",
                        "estimand_id": f"H4.mphiq.{component}",
                        "independent_block": block,
                        "dependence_cluster": cluster,
                        "trajectory_id": trajectory,
                        "metric": metric,
                        "effect": effect,
                        "nested_observations_aggregated": len(nested),
                    }
                )
            comparisons = {
                "H4.information_vs_profile": (
                    component_effects[(block, metric, "I")]
                    - component_effects[(block, metric, "P")]
                ),
                "H4.information_vs_question": (
                    component_effects[(block, metric, "I")]
                    - component_effects[(block, metric, "Q")]
                ),
            }
            for estimand_id, effect in comparisons.items():
                effects.append(
                    {
                        "hypothesis": "H4",
                        "estimand_id": estimand_id,
                        "independent_block": block,
                        "dependence_cluster": cluster,
                        "trajectory_id": trajectory,
                        "metric": metric,
                        "effect": effect,
                        "nested_observations_aggregated": sum(
                            1
                            for row_block, row_metric, _component, _pair in pair_effects
                            if (row_block, row_metric) == (block, metric)
                        ),
                    }
                )
    return block_values, effects


def _contrast_seed(seed: int, contrast_key: str, purpose: str) -> int:
    encoded = f"{seed}:{purpose}:{contrast_key}".encode()
    return int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big")


def analyze_first_paper_estimands(
    crossed_rows: pd.DataFrame,
    *,
    confirmatory_metrics: Sequence[str],
    lineage_rows: pd.DataFrame | None = None,
    mphiq_rows: pd.DataFrame | None = None,
    alpha: float = 0.05,
    seed: int = 0,
    n_bootstrap: int = 10_000,
) -> FirstPaperEstimands:
    """Estimate frozen H1 and optional H3/H4 contrasts over independent blocks.

    H1 uses a family-weighted value for each technology-by-ecology cell.  H3
    first averages nested pairs within provider/family strata and then gives
    each stratum equal weight.  H4 averages audited Hamming-one pair effects
    within block and component.  Only the resulting block effects enter the
    bootstrap, sign-flip tests, and Holm family.
    """
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    if n_bootstrap < 1:
        raise ValueError("n_bootstrap must be positive")
    metrics = _normalized_metrics(confirmatory_metrics)
    block_values, block_effects, identities = _crossed_block_values(crossed_rows, metrics)
    if lineage_rows is not None:
        values, effects = _lineage_effects(lineage_rows, metrics, identities)
        block_values.extend(values)
        block_effects.extend(effects)
    if mphiq_rows is not None:
        values, effects = _mphiq_effects(mphiq_rows, metrics, identities)
        block_values.extend(values)
        block_effects.extend(effects)

    grouped: dict[tuple[str, str, str], list[float]] = {}
    for row in block_effects:
        key = (str(row["hypothesis"]), str(row["estimand_id"]), str(row["metric"]))
        grouped.setdefault(key, []).append(float(row["effect"]))

    raw: dict[str, float] = {}
    summaries: list[dict[str, Any]] = []
    for (hypothesis, estimand_id, metric), values in sorted(grouped.items()):
        contrast_key = f"{estimand_id}::{metric}"
        inference = paired_sign_flip_test(
            values,
            seed=_contrast_seed(seed, contrast_key, "sign-flip"),
        )
        interval = bootstrap_ci(
            values,
            lambda sample: float(np.mean(sample)),
            n_resamples=n_bootstrap,
            seed=_contrast_seed(seed, contrast_key, "bootstrap"),
        )
        raw[contrast_key] = inference.p_value
        summaries.append(
            {
                "hypothesis": hypothesis,
                "estimand_id": estimand_id,
                "metric": metric,
                "estimate": float(np.mean(values)),
                "ci95_low": interval.low,
                "ci95_high": interval.high,
                "p_value": inference.p_value,
                "exact": inference.exact,
                "randomizations": inference.n_randomizations,
                "independent_n": len(values),
                "method": "paired sign-flip test over independent block effects",
            }
        )

    adjusted = holm_bonferroni(raw, alpha=alpha)
    for row in summaries:
        key = f"{row['estimand_id']}::{row['metric']}"
        row["p_adjusted"] = adjusted[key]["p_adjusted"]
        row["reject"] = adjusted[key]["reject"]

    hypotheses = {
        key: {
            "raw_p": raw[key],
            "adjusted_p": adjusted[key]["p_adjusted"],
            "reject": adjusted[key]["reject"],
        }
        for key in sorted(raw)
    }
    multiplicity = {
        "family": "confirmatory-H1-H3-H4",
        "method": "Holm-Bonferroni",
        "alpha": alpha,
        "frozen_contrasts": sorted(raw),
        "hypotheses": hypotheses,
        "independent_unit": "trajectory/window block",
        "nested_units_not_counted": [
            "agent",
            "pair",
            "step",
            "call",
            "retry",
            "prompt variant",
            "response seed",
        ],
    }
    return FirstPaperEstimands(
        block_values=pd.DataFrame(block_values),
        block_effects=pd.DataFrame(block_effects),
        effects=pd.DataFrame(summaries),
        multiplicity=multiplicity,
    )
