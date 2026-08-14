"""Fail-closed study-bundle analysis for paper-grade H1 evidence.

The source contract is a JSON file that declares the complete set of expected
independent blocks and their run directories.  Analysis verifies every run,
rejects duplicate trajectories, and emits a hash-locked release bundle.  A
mock study can exercise the entire path but can never pass the paper gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from flock.analysis.crossed import (
    H1_CONTRASTS,
    H3_CONTRASTS,
    H4_CONTRASTS,
    FirstPaperEstimands,
    analyze_first_paper_estimands,
)
from flock.analysis.stats import equivalence_tost
from flock.analysis.study import StudyInference, analyze_h1_study
from flock.analysis.study_visuals import export_core_study_figures
from flock.experiments.verify import RunVerification, verify_run


class PreregistrationRef(BaseModel):
    """Immutable reference recorded before confirmatory calls."""

    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable_uri: str = Field(min_length=1)
    git_sha: str = Field(min_length=7)


class H1StatisticalContract(BaseModel):
    """Frozen practical thresholds for the primary H1 estimand."""

    model_config = ConfigDict(extra="forbid")

    estimand_id: Literal["H1-kappa-technology-contrast"] = (
        "H1-kappa-technology-contrast"
    )
    sesoi: float = Field(gt=0, le=2)
    equivalence_lower: float = Field(ge=-2, lt=0)
    equivalence_upper: float = Field(gt=0, le=2)
    noninferiority_lower: float = Field(ge=-2, lt=0)
    alpha: float = Field(gt=0, lt=0.5)

    @model_validator(mode="after")
    def validate_bounds(self) -> H1StatisticalContract:
        if self.equivalence_lower >= self.equivalence_upper:
            raise ValueError("equivalence_lower must be smaller than equivalence_upper")
        return self


class EstimandThresholds(BaseModel):
    """Frozen practical thresholds for one estimand/outcome pair."""

    model_config = ConfigDict(extra="forbid")

    sesoi: float = Field(gt=0, le=2)
    equivalence_lower: float = Field(ge=-2, lt=0)
    equivalence_upper: float = Field(gt=0, le=2)
    noninferiority_lower: float = Field(ge=-2, lt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> EstimandThresholds:
        if self.equivalence_lower >= self.equivalence_upper:
            raise ValueError("equivalence_lower must be smaller than equivalence_upper")
        return self


class FirstPaperStatisticalContract(BaseModel):
    """Candidate estimands and margins for the crossed H1/H3/H4 analysis."""

    model_config = ConfigDict(extra="forbid")

    confirmatory_metrics: list[str] = Field(min_length=1)
    estimands: dict[str, EstimandThresholds]
    alpha: float = Field(gt=0, lt=0.5)

    @model_validator(mode="after")
    def validate_analysis_family(self) -> FirstPaperStatisticalContract:
        metrics = [metric.strip() for metric in self.confirmatory_metrics]
        if any(not metric for metric in metrics) or len(metrics) != len(set(metrics)):
            raise ValueError("confirmatory_metrics must be nonempty and unique")
        expected = {
            f"{estimand_id}::{metric}"
            for metric in metrics
            for estimand_id in (*H1_CONTRASTS, *H3_CONTRASTS, *H4_CONTRASTS)
        }
        actual = set(self.estimands)
        if actual != expected:
            raise ValueError(
                "estimands must define thresholds for every H1/H3/H4 contrast and metric: "
                f"missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
            )
        self.confirmatory_metrics = metrics
        return self


class HashedPaperInput(BaseModel):
    """Content-addressed family-aggregated analysis input."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class FirstPaperInputs(BaseModel):
    """Required crossed H1, lineage H3, and Hamming-one H4 inputs."""

    model_config = ConfigDict(extra="forbid")

    crossed_rows: HashedPaperInput
    lineage_rows: HashedPaperInput
    mphiq_rows: HashedPaperInput


class StudyBundleSpec(BaseModel):
    """Strict source manifest for one complete study bundle."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(min_length=1)
    status: Literal["complete", "incomplete"]
    evidence_kind: Literal["mock", "real"]
    expected_independent_blocks: list[str] = Field(min_length=2)
    run_dirs: list[str] = Field(min_length=2)
    preregistration: PreregistrationRef | None = None
    first_paper_inputs: FirstPaperInputs | None = None
    rehearsal_contract: FirstPaperStatisticalContract | None = None

    @model_validator(mode="after")
    def validate_counts(self) -> StudyBundleSpec:
        blocks = [block.strip() for block in self.expected_independent_blocks]
        if any(not block for block in blocks) or len(blocks) != len(set(blocks)):
            raise ValueError("expected independent blocks must be nonempty and unique")
        if self.first_paper_inputs is None and len(self.run_dirs) != len(blocks):
            raise ValueError("one run directory is required per expected independent block")
        if self.first_paper_inputs is not None and len(self.run_dirs) < len(blocks):
            raise ValueError("paper studies require at least one treatment run per block")
        if self.rehearsal_contract is not None and self.evidence_kind != "mock":
            raise ValueError("rehearsal_contract is restricted to mock evidence")
        return self


class StudyBundleVerification(BaseModel):
    bundle_dir: str
    ok: bool
    paper_eligible: bool
    evidence_kind: Literal["mock", "real", "unknown"]
    independent_units: int
    errors: list[str]


CORE_ARTIFACTS = (
    "independent_units.parquet",
    "block_effects.parquet",
    "effects.parquet",
    "missingness_failures.parquet",
    "sensitivity_results.parquet",
    "multiplicity.json",
    "equivalence_noninferiority.json",
    "estimand_registry.json",
    "statistical_verification.json",
    "claims.json",
    "figures/independent-unit-topology.png",
    "figures/h1-block-effects.png",
)
RUN_INPUTS = (
    "manifest.json",
    "decisions.jsonl",
    "fills.parquet",
    "portfolio.parquet",
    "market_events.jsonl",
)
DEFAULT_H1_STATISTICAL_CONTRACT = H1StatisticalContract(
    sesoi=0.10,
    equivalence_lower=-0.05,
    equivalence_upper=0.05,
    noninferiority_lower=-0.05,
    alpha=0.05,
)


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], payload)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _is_mock_manifest(manifest: dict[str, Any]) -> bool:
    config = cast(dict[str, Any], manifest.get("config", {}))
    if config.get("model_policy") == "mock_only":
        return True
    agents = cast(dict[str, dict[str, Any]], manifest.get("agents", {}))
    llm_agents = [meta for meta in agents.values() if meta.get("kind") == "llm"]
    return bool(llm_agents) and any(
        str(meta.get("model_id", meta.get("model", ""))).startswith("mock-")
        for meta in llm_agents
    )


def _trajectory_identity(manifest: dict[str, Any]) -> str:
    """Return an ID that excludes response/model seeds by construction.

    Explicit trajectory IDs are preferred.  The conservative fallback hashes
    the dataset and market path settings while excluding generic ``seed`` and
    the user-provided block label.  Thus relabeling the same replay or changing
    only a response seed cannot manufacture another independent unit.
    """
    config = cast(dict[str, Any], manifest.get("config", {}))
    explicit = config.get("trajectory_id") or config.get("market_replica_id")
    if explicit:
        return str(explicit)
    payload = {
        "dataset_sha256": cast(dict[str, Any], manifest.get("dataset", {})).get("sha256"),
        "market": config.get("market"),
        "steps": config.get("steps"),
        "observation_window": config.get("observation_window"),
        "window_start": config.get("window_start"),
        "window_end": config.get("window_end"),
        "trajectory_start": config.get("trajectory_start"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "derived-" + hashlib.sha256(encoded.encode()).hexdigest()


def _validate_source_runs(
    spec: StudyBundleSpec, source_dir: Path
) -> tuple[list[Path], list[dict[str, Any]], list[RunVerification], Literal["mock", "real"]]:
    if spec.status != "complete":
        raise ValueError("study source is incomplete")
    run_dirs = [_resolve(source_dir, value) for value in spec.run_dirs]
    manifests: list[dict[str, Any]] = []
    verifications: list[RunVerification] = []
    run_ids: set[str] = set()
    block_identities: dict[str, tuple[str, str]] = {}
    cluster_blocks: dict[str, str] = {}
    trajectory_blocks: dict[str, str] = {}
    expected_blocks = set(spec.expected_independent_blocks)
    for run_dir in run_dirs:
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError(f"missing completed run manifest: {manifest_path}")
        manifest = _json(manifest_path)
        if manifest.get("status") != "complete":
            raise ValueError(f"run is not complete: {run_dir}")
        verification = verify_run(run_dir)
        if not verification.ok:
            raise ValueError(f"run failed verification: {run_dir}: {verification.errors}")
        run_id = str(manifest.get("run_id", "")).strip()
        if not run_id or run_id in run_ids:
            raise ValueError(f"paper source run IDs must be nonempty and unique: {run_id!r}")
        run_ids.add(run_id)
        config = cast(dict[str, Any], manifest.get("config", {}))
        block = str(config.get("independent_block", "")).strip()
        cluster = str(config.get("dependence_cluster", "")).strip()
        trajectory = _trajectory_identity(manifest)
        if block not in expected_blocks or not cluster:
            raise ValueError(f"run has invalid independent-block lineage: {run_dir}")
        identity = (cluster, trajectory)
        if block in block_identities and block_identities[block] != identity:
            raise ValueError(f"nested treatment runs disagree on lineage for block {block!r}")
        prior_cluster_block = cluster_blocks.get(cluster)
        prior_trajectory_block = trajectory_blocks.get(trajectory)
        if (
            (prior_cluster_block is not None and prior_cluster_block != block)
            or (prior_trajectory_block is not None and prior_trajectory_block != block)
        ):
            raise ValueError(
                "a trajectory or dependence cluster cannot cross independent blocks; "
                "block labels or model seeds do not create independent evidence: "
                f"{trajectory}"
            )
        block_identities[block] = identity
        cluster_blocks[cluster] = block
        trajectory_blocks[trajectory] = block
        manifests.append(manifest)
        verifications.append(verification)
    if set(block_identities) != expected_blocks:
        raise ValueError("verified runs do not cover every expected independent block")
    detected: Literal["mock", "real"] = (
        "mock" if any(_is_mock_manifest(manifest) for manifest in manifests) else "real"
    )
    if spec.evidence_kind == "real" and detected == "mock":
        raise ValueError("mock run was declared as real evidence")
    return run_dirs, manifests, verifications, detected


def _check_preregistration(spec: StudyBundleSpec, source_dir: Path) -> None:
    if spec.preregistration is None:
        raise ValueError("paper export requires an immutable preregistration")
    prereg_path = _resolve(source_dir, spec.preregistration.path)
    if not prereg_path.is_file():
        raise ValueError(f"preregistration file is missing: {prereg_path}")
    if _sha256(prereg_path) != spec.preregistration.sha256:
        raise ValueError("preregistration hash does not match the frozen reference")


def _statistical_contract(
    spec: StudyBundleSpec,
    source_dir: Path,
    *,
    require_frozen: bool,
) -> tuple[H1StatisticalContract, Literal["provisional-default", "frozen-preregistered"]]:
    """Resolve thresholds without treating an observed result as calibration data."""
    if spec.preregistration is None:
        if require_frozen:
            raise ValueError("paper export requires a preregistered statistical_contract")
        return DEFAULT_H1_STATISTICAL_CONTRACT, "provisional-default"

    _check_preregistration(spec, source_dir)
    prereg_path = _resolve(source_dir, spec.preregistration.path)
    try:
        preregistration = _json(prereg_path)
    except (json.JSONDecodeError, ValueError):
        if require_frozen:
            raise ValueError(
                "paper export requires a JSON preregistration with statistical_contract"
            ) from None
        return DEFAULT_H1_STATISTICAL_CONTRACT, "provisional-default"

    raw_contract = preregistration.get("statistical_contract")
    if raw_contract is None:
        if require_frozen:
            raise ValueError("paper export requires a preregistered statistical_contract")
        return DEFAULT_H1_STATISTICAL_CONTRACT, "provisional-default"
    contract = H1StatisticalContract.model_validate(raw_contract)
    return contract, "frozen-preregistered"


def _first_paper_contract(
    spec: StudyBundleSpec, source_dir: Path
) -> FirstPaperStatisticalContract:
    """Load the complete H1/H3/H4 contract from the immutable preregistration."""
    _check_preregistration(spec, source_dir)
    assert spec.preregistration is not None
    preregistration = _json(_resolve(source_dir, spec.preregistration.path))
    raw_contract = preregistration.get("first_paper_statistical_contract")
    if raw_contract is None:
        raise ValueError(
            "paper export requires a preregistered first_paper_statistical_contract"
        )
    return FirstPaperStatisticalContract.model_validate(raw_contract)


def _paper_input_frames(
    spec: StudyBundleSpec, source_dir: Path
) -> tuple[dict[str, Path], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Resolve and authenticate all frozen family-aggregated paper inputs."""
    if spec.first_paper_inputs is None:
        raise ValueError("paper export requires frozen first_paper_inputs")
    paths: dict[str, Path] = {}
    frames: dict[str, pd.DataFrame] = {}
    for name in ("crossed_rows", "lineage_rows", "mphiq_rows"):
        reference = cast(HashedPaperInput, getattr(spec.first_paper_inputs, name))
        path = _resolve(source_dir, reference.path)
        if not path.is_file():
            raise ValueError(f"paper analysis input is missing: {path}")
        if _sha256(path) != reference.sha256:
            raise ValueError(f"paper analysis input hash does not match: {name}")
        try:
            frame = pd.read_parquet(path)
        except Exception as error:
            raise ValueError(f"paper analysis input is not readable parquet: {name}") from error
        paths[name] = path
        frames[name] = frame
    return paths, frames["crossed_rows"], frames["lineage_rows"], frames["mphiq_rows"]


def _validate_aggregate_provenance(
    frames: dict[str, pd.DataFrame], manifests: list[dict[str, Any]]
) -> None:
    """Require exact, block-consistent run provenance for every aggregate row."""
    run_lineage: dict[str, tuple[str, str, str]] = {}
    for manifest in manifests:
        run_id = str(manifest.get("run_id", "")).strip()
        config = cast(dict[str, Any], manifest.get("config", {}))
        lineage = (
            str(config.get("independent_block", "")).strip(),
            str(config.get("dependence_cluster", "")).strip(),
            _trajectory_identity(manifest),
        )
        if not run_id or run_id in run_lineage:
            raise ValueError("aggregate provenance requires unique verified run IDs")
        run_lineage[run_id] = lineage

    cited: set[str] = set()
    for name, frame in frames.items():
        if "source_run_ids" not in frame.columns:
            raise ValueError(f"{name} requires source_run_ids on every aggregate row")
        for row_index, row in enumerate(frame.to_dict("records")):
            raw_ids = row.get("source_run_ids")
            if not isinstance(raw_ids, (list, tuple, np.ndarray)):
                raise ValueError(f"{name} row {row_index} has invalid source_run_ids")
            source_ids = [str(value).strip() for value in raw_ids]
            if not source_ids or any(not value for value in source_ids):
                raise ValueError(f"{name} row {row_index} has empty source_run_ids")
            if len(source_ids) != len(set(source_ids)):
                raise ValueError(f"{name} row {row_index} repeats a source run ID")
            row_lineage = (
                str(row.get("independent_block", "")).strip(),
                str(row.get("dependence_cluster", "")).strip(),
                str(row.get("trajectory_id", "")).strip(),
            )
            for run_id in source_ids:
                if run_id not in run_lineage:
                    raise ValueError(f"{name} cites an unverified source run ID {run_id!r}")
                if run_lineage[run_id] != row_lineage:
                    raise ValueError(
                        f"{name} row {row_index} cites a source run from another block lineage"
                    )
                cited.add(run_id)
    expected = set(run_lineage)
    if cited != expected:
        raise ValueError(
            "aggregate source_run_ids do not exactly cover verified treatment runs: "
            f"missing={sorted(expected - cited)}, unexpected={sorted(cited - expected)}"
        )


def _noninferiority_result(
    values: list[float], lower_margin: float, alpha: float
) -> dict[str, Any]:
    """One-sided test that the mean effect exceeds the adverse lower margin."""
    from scipy.stats import t

    effects = np.asarray(values, dtype=float)
    estimate = float(effects.mean())
    standard_error = float(effects.std(ddof=1) / np.sqrt(len(effects)))
    if standard_error == 0:
        p_value = 0.0 if estimate > lower_margin else 1.0
    else:
        p_value = float(t.sf((estimate - lower_margin) / standard_error, len(effects) - 1))
    return {
        "estimate": estimate,
        "adverse_lower_margin": lower_margin,
        "p_value": p_value,
        "alpha": alpha,
        "statistically_noninferior": p_value < alpha,
        "direction": "mean effect is greater than the adverse lower margin",
    }


def _sensitivity_rows(
    study_id: str,
    block_effects: dict[str, float],
    sesoi: float,
) -> list[dict[str, Any]]:
    ordered = sorted(block_effects.items())

    def row(
        specification_id: str,
        values: list[float],
        omitted_block: str | None,
        *,
        estimate: float | None = None,
    ) -> dict[str, Any]:
        estimate = float(np.mean(values)) if estimate is None else estimate
        if estimate >= sesoi:
            classification = "at-or-above-positive-sesoi"
        elif estimate <= -sesoi:
            classification = "at-or-below-negative-sesoi"
        else:
            classification = "inside-practical-null-band"
        return {
            "study_id": study_id,
            "estimand_id": "H1-kappa-technology-contrast",
            "specification_id": specification_id,
            "estimate": estimate,
            "independent_n": len(values),
            "omitted_block": omitted_block,
            "sesoi": sesoi,
            "practical_classification": classification,
            "confirmatory": specification_id == "primary-mean",
        }

    values = [effect for _, effect in ordered]
    rows = [row("primary-mean", values, None)]
    rows.append(row("block-median", values, None, estimate=float(np.median(values))))
    for omitted, _ in ordered:
        retained = [effect for block, effect in ordered if block != omitted]
        rows.append(row(f"leave-one-block-out:{omitted}", retained, omitted))
    return rows


def _crossed_sensitivity_rows(
    study_id: str,
    block_effects: pd.DataFrame,
    contract: FirstPaperStatisticalContract,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_key, group in block_effects.groupby(["estimand_id", "metric"], sort=True):
        estimand_id, metric = cast(tuple[Any, Any], group_key)
        key = f"{estimand_id}::{metric}"
        thresholds = contract.estimands[key]
        group_records = cast(list[dict[str, Any]], group.to_dict("records"))
        values_by_block = {
            str(row["independent_block"]): float(row["effect"])
            for row in group_records
        }
        for row in _sensitivity_rows(study_id, values_by_block, thresholds.sesoi):
            row["estimand_id"] = str(estimand_id)
            row["metric"] = str(metric)
            rows.append(row)
    return rows


def _emit_first_paper_bundle(
    *,
    spec: StudyBundleSpec,
    source_manifest: Path,
    output_dir: Path | None,
    run_dirs: list[Path],
    manifests: list[dict[str, Any]],
    run_checks: list[RunVerification],
    evidence_kind: Literal["mock", "real"],
    contract: FirstPaperStatisticalContract,
    paper_requested: bool,
    seed: int,
) -> Path:
    """Emit the preregistered crossed H1/H3/H4 bundle; never infer from raw agents."""
    source_dir = source_manifest.parent
    margin_status = (
        "frozen-preregistered" if paper_requested else "mock-rehearsal-only"
    )
    input_paths, crossed_rows, lineage_rows, mphiq_rows = _paper_input_frames(
        spec, source_dir
    )
    _validate_aggregate_provenance(
        {
            "crossed_rows": crossed_rows,
            "lineage_rows": lineage_rows,
            "mphiq_rows": mphiq_rows,
        },
        manifests,
    )
    result: FirstPaperEstimands = analyze_first_paper_estimands(
        crossed_rows,
        confirmatory_metrics=contract.confirmatory_metrics,
        lineage_rows=lineage_rows,
        mphiq_rows=mphiq_rows,
        alpha=contract.alpha,
        seed=seed,
    )
    if paper_requested and not (
        result.multiplicity.get("confirmatory_family_frozen") is True
        and result.multiplicity.get("paper_eligible") is True
        and bool(result.multiplicity.get("frozen_contrasts"))
    ):
        raise ValueError(
            "paper export requires a frozen confirmatory family; the current "
            "first-paper analysis is explicitly unfrozen"
        )
    expected_blocks = set(spec.expected_independent_blocks)
    observed_blocks = set(result.block_effects["independent_block"].astype(str))
    if observed_blocks != expected_blocks:
        raise ValueError(
            "crossed paper inputs do not match expected independent blocks: "
            f"missing={sorted(expected_blocks - observed_blocks)}, "
            f"unexpected={sorted(observed_blocks - expected_blocks)}"
        )

    manifest_identities: dict[str, tuple[str, str]] = {}
    runs_by_block: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for run_dir, manifest in zip(run_dirs, manifests, strict=True):
        config = cast(dict[str, Any], manifest["config"])
        block = str(config["independent_block"])
        cluster = str(config.get("dependence_cluster", "")).strip()
        trajectory = _trajectory_identity(manifest)
        if not cluster:
            raise ValueError("paper runs require an explicit dependence_cluster")
        manifest_identities[block] = (cluster, trajectory)
        runs_by_block.setdefault(block, []).append((run_dir, manifest))
    independent_rows: list[dict[str, Any]] = []
    for block in sorted(runs_by_block):
        cluster, trajectory = manifest_identities[block]
        nested_runs = runs_by_block[block]
        independent_rows.append(
            {
                "study_id": spec.study_id,
                "independent_block": block,
                "dependence_cluster": cluster,
                "trajectory_id": trajectory,
                "nested_run_ids_json": json.dumps(
                    sorted(str(manifest["run_id"]) for _, manifest in nested_runs)
                ),
                "nested_run_dirs_json": json.dumps(
                    sorted(str(run_dir) for run_dir, _ in nested_runs)
                ),
                "nested_model_seeds_json": json.dumps(
                    [
                        cast(dict[str, Any], manifest["config"]).get("seed")
                        for _, manifest in sorted(
                            nested_runs, key=lambda item: str(item[1]["run_id"])
                        )
                    ]
                ),
                "nested_treatment_runs": len(nested_runs),
                "evidence_kind": evidence_kind,
            }
        )
    identity_rows = result.block_effects[
        ["independent_block", "dependence_cluster", "trajectory_id"]
    ].drop_duplicates()
    observed_identities = {
        str(block): (str(cluster), str(trajectory))
        for block, cluster, trajectory in identity_rows.itertuples(index=False, name=None)
    }
    if observed_identities != manifest_identities:
        raise ValueError(
            "crossed paper input block, dependence-cluster, or trajectory lineage "
            "does not match verified run manifests"
        )

    destination = (output_dir or source_dir / "analysis").resolve()
    destination.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(independent_rows).sort_values("independent_block").to_parquet(
        destination / "independent_units.parquet", index=False
    )
    block_effects = result.block_effects.copy()
    block_effects.insert(0, "study_id", spec.study_id)
    block_effects["evidence_kind"] = evidence_kind
    block_effects = block_effects.sort_values(
        ["estimand_id", "metric", "independent_block"]
    ).reset_index(drop=True)
    block_effects.to_parquet(destination / "block_effects.parquet", index=False)

    effects = result.effects.copy()
    effects.insert(0, "study_id", spec.study_id)
    effects["evidence_kind"] = evidence_kind
    effects["margin_status"] = margin_status
    for index, row in effects.iterrows():
        thresholds = contract.estimands[f"{row['estimand_id']}::{row['metric']}"]
        for field, value in thresholds.model_dump().items():
            effects.at[index, field] = value
    effects = effects.sort_values(["estimand_id", "metric"]).reset_index(drop=True)
    effects.to_parquet(destination / "effects.parquet", index=False)

    checks_by_run_id = {
        str(manifest["run_id"]): check
        for manifest, check in zip(manifests, run_checks, strict=True)
    }
    missingness_rows: list[dict[str, Any]] = []
    for block in sorted(runs_by_block):
        nested_runs = runs_by_block[block]
        run_ids = sorted(str(manifest["run_id"]) for _, manifest in nested_runs)
        checks = [checks_by_run_id[run_id] for run_id in run_ids]
        missingness_rows.append(
            {
                "study_id": spec.study_id,
                "independent_block": block,
                "source_run_ids_json": json.dumps(run_ids),
                "nested_treatment_runs": len(run_ids),
                "run_complete": True,
                "verification_ok": all(check.ok for check in checks),
                "missing_independent_unit": False,
                "terminal_failure": False,
                "decision_rows": sum(check.decisions for check in checks),
                "fill_rows": sum(check.fills for check in checks),
                "portfolio_rows": sum(check.portfolio_rows for check in checks),
                "error_count": sum(len(check.errors) for check in checks),
                "warning_count": sum(len(check.warnings) for check in checks),
                "errors_json": json.dumps(
                    {run_id: checks_by_run_id[run_id].errors for run_id in run_ids},
                    sort_keys=True,
                ),
                "warnings_json": json.dumps(
                    {run_id: checks_by_run_id[run_id].warnings for run_id in run_ids},
                    sort_keys=True,
                ),
                "scope_note": "verified run-level completeness for crossed paper inputs",
            }
        )
    pd.DataFrame(missingness_rows).sort_values("independent_block").to_parquet(
        destination / "missingness_failures.parquet", index=False
    )
    pd.DataFrame(
        _crossed_sensitivity_rows(spec.study_id, block_effects, contract)
    ).sort_values(["estimand_id", "metric", "specification_id"]).to_parquet(
        destination / "sensitivity_results.parquet", index=False
    )

    equivalence_results: list[dict[str, Any]] = []
    registry: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    for effect_row in effects.to_dict("records"):
        estimand_id = str(effect_row["estimand_id"])
        metric = str(effect_row["metric"])
        key = f"{estimand_id}::{metric}"
        thresholds = contract.estimands[key]
        values = (
            block_effects.loc[
                (block_effects["estimand_id"] == estimand_id)
                & (block_effects["metric"] == metric),
                "effect",
            ]
            .astype(float)
            .tolist()
        )
        tost = equivalence_tost(
            values,
            thresholds.equivalence_lower,
            thresholds.equivalence_upper,
            alpha=contract.alpha,
        )
        noninferiority = _noninferiority_result(
            values, thresholds.noninferiority_lower, contract.alpha
        )
        equivalence_results.append(
            {
                "estimand_id": estimand_id,
                "metric": metric,
                "margin_status": margin_status,
                "equivalence": {
                    **tost.__dict__,
                    "decision_rule": "both TOST one-sided p-values must be below alpha",
                    "paper_claim_allowed": tost.equivalent and paper_requested,
                },
                "noninferiority": {
                    **noninferiority,
                    "paper_claim_allowed": bool(
                        noninferiority["statistically_noninferior"]
                    )
                    and paper_requested,
                },
            }
        )
        registry.append(
            {
                "estimand_id": estimand_id,
                "metric": metric,
                "contrast": estimand_id,
                "independent_unit": "trajectory or nonoverlapping market-window block",
                "nested_units_not_independent": [
                    "agent",
                    "pair",
                    "step",
                    "call",
                    "retry",
                    "prompt variant",
                    "response seed",
                ],
                "inference": "paired sign-flip test over independent block effects",
                **thresholds.model_dump(),
                "alpha": contract.alpha,
                "margin_status": margin_status,
                "limitations": [
                    "sampled dated model releases and classical families only",
                    "block-effect sign flips require the stated symmetry assumption",
                ],
            }
        )
        claims.append(
            {
                "claim_id": key,
                "estimand_id": estimand_id,
                "metric": metric,
                "effect_artifact": "effects.parquet",
                "estimand_artifact": "estimand_registry.json",
                "missingness_artifact": "missingness_failures.parquet",
                "sensitivity_artifact": "sensitivity_results.parquet",
                "equivalence_artifact": "equivalence_noninferiority.json",
                "figures": (
                    ["figures/h1-block-effects.png"]
                    if key == f"{H1_CONTRASTS[0]}::{contract.confirmatory_metrics[0]}"
                    else []
                ),
                "limitations": [
                    "limited to the frozen sampled releases, families, and trajectories",
                    "sign-flip inference assumes symmetric block effects",
                ],
                "verification_status": (
                    "paper-eligible" if paper_requested else "mock-rehearsal"
                ),
                "evidence_kind": evidence_kind,
                "margin_status": margin_status,
            }
        )

    _write_json(
        destination / "equivalence_noninferiority.json",
        {
            "study_id": spec.study_id,
            "margin_status": margin_status,
            "margins_provisional": not paper_requested,
            "results": equivalence_results,
            "interpretation_rule": "nonsignificance is never evidence of equivalence",
        },
    )
    _write_json(
        destination / "estimand_registry.json",
        {"study_id": spec.study_id, "estimands": registry},
    )
    _write_json(destination / "multiplicity.json", result.multiplicity)
    _write_json(
        destination / "statistical_verification.json",
        {
            "verified": True,
            "analysis_design": "crossed-H1-H3-H4",
            "independent_n": len(expected_blocks),
            "independent_unit": "trajectory or nonoverlapping market-window block",
            "nested_units_not_counted": result.multiplicity["nested_units_not_counted"],
            "inference_method": result.multiplicity["method"],
            "confirmatory_family_frozen": result.multiplicity[
                "confirmatory_family_frozen"
            ],
            "margin_status": margin_status,
            "margins_frozen_before_analysis": bool(
                result.multiplicity["confirmatory_family_frozen"]
            ),
            "run_verifications": [check.model_dump() for check in run_checks],
        },
    )
    _write_json(destination / "claims.json", {"claims": claims})
    primary_key = f"{H1_CONTRASTS[0]}::{contract.confirmatory_metrics[0]}"
    primary_thresholds = contract.estimands[primary_key]
    export_core_study_figures(
        destination,
        sesoi=primary_thresholds.sesoi,
        estimand_id=H1_CONTRASTS[0],
        metric=contract.confirmatory_metrics[0],
    )
    artifact_hashes = {name: _sha256(destination / name) for name in CORE_ARTIFACTS}
    _write_json(
        destination / "release-manifest.json",
        {
            "schema_version": 2,
            "analysis_design": "crossed-H1-H3-H4",
            "study_id": spec.study_id,
            "status": "complete",
            "evidence_kind": evidence_kind,
            "paper_requested": paper_requested,
            "analysis_seed": seed,
            "expected_independent_blocks": sorted(expected_blocks),
            "preregistration": spec.preregistration.model_dump()
            if paper_requested and spec.preregistration
            else None,
            "first_paper_statistical_contract": contract.model_dump(),
            "margin_status": margin_status,
            "source_manifest": str(source_manifest),
            "source_manifest_sha256": _sha256(source_manifest),
            "run_input_sha256": {
                str(run_dir): {name: _sha256(run_dir / name) for name in RUN_INPUTS}
                for run_dir in run_dirs
            },
            "analysis_input_sha256": {
                name: {"path": str(path), "sha256": _sha256(path)}
                for name, path in input_paths.items()
            },
            "artifact_sha256": artifact_hashes,
        },
    )
    verification = verify_study_bundle(destination, require_paper=paper_requested)
    if not verification.ok:
        raise ValueError(f"emitted study bundle failed verification: {verification.errors}")
    return destination


def analyze_study_bundle(
    source_manifest: Path,
    output_dir: Path | None = None,
    *,
    paper: bool = False,
    seed: int = 0,
) -> Path:
    """Verify source runs and emit the core hash-locked H1 study artifacts."""
    source_manifest = source_manifest.resolve()
    spec = StudyBundleSpec.model_validate(_json(source_manifest))
    run_dirs, manifests, run_checks, evidence_kind = _validate_source_runs(
        spec, source_manifest.parent
    )
    if spec.first_paper_inputs is not None:
        if paper:
            if spec.evidence_kind != "real" or evidence_kind != "real":
                raise ValueError("paper export rejects mock evidence")
            _check_preregistration(spec, source_manifest.parent)
            contract = _first_paper_contract(spec, source_manifest.parent)
        else:
            if spec.evidence_kind != "mock" or evidence_kind != "mock":
                raise ValueError(
                    "crossed first-paper inputs require --paper for real evidence"
                )
            if spec.rehearsal_contract is None:
                raise ValueError(
                    "mock crossed inputs require an explicit rehearsal_contract"
                )
            contract = spec.rehearsal_contract
        return _emit_first_paper_bundle(
            spec=spec,
            source_manifest=source_manifest,
            output_dir=output_dir,
            run_dirs=run_dirs,
            manifests=manifests,
            run_checks=run_checks,
            evidence_kind=evidence_kind,
            contract=contract,
            paper_requested=paper,
            seed=seed,
        )
    if paper:
        if spec.evidence_kind != "real" or evidence_kind != "real":
            raise ValueError("paper export rejects mock evidence")
        _check_preregistration(spec, source_manifest.parent)
        _first_paper_contract(spec, source_manifest.parent)
        raise ValueError("paper export requires frozen first_paper_inputs")
    contract, margin_status = _statistical_contract(
        spec, source_manifest.parent, require_frozen=False
    )

    inference: StudyInference = analyze_h1_study(run_dirs, seed=seed)
    actual_blocks = set(inference.block_effects)
    expected_blocks = set(spec.expected_independent_blocks)
    if actual_blocks != expected_blocks:
        raise ValueError(
            "complete-block mismatch: "
            f"missing={sorted(expected_blocks - actual_blocks)}, "
            f"unexpected={sorted(actual_blocks - expected_blocks)}"
        )

    destination = (output_dir or source_manifest.parent / "analysis").resolve()
    destination.mkdir(parents=True, exist_ok=True)
    independent_rows: list[dict[str, Any]] = []
    for run_dir, manifest in zip(run_dirs, manifests, strict=True):
        config = cast(dict[str, Any], manifest["config"])
        block = str(config["independent_block"])
        independent_rows.append(
            {
                "study_id": spec.study_id,
                "independent_block": block,
                "dependence_cluster": inference.dependence_clusters[block],
                "trajectory_id": _trajectory_identity(manifest),
                "run_id": str(manifest.get("run_id", run_dir.name)),
                "run_dir": str(run_dir),
                "nested_model_seed": config.get("seed"),
                "evidence_kind": evidence_kind,
            }
        )
    pd.DataFrame(independent_rows).to_parquet(
        destination / "independent_units.parquet", index=False
    )
    pd.DataFrame(
        [
            {
                "study_id": spec.study_id,
                "estimand_id": "H1-kappa-technology-contrast",
                "independent_block": block,
                "dependence_cluster": inference.dependence_clusters[block],
                "effect": effect,
            }
            for block, effect in inference.block_effects.items()
        ]
    ).to_parquet(destination / "block_effects.parquet", index=False)
    pd.DataFrame(
        [
            {
                "study_id": spec.study_id,
                "estimand_id": "H1-kappa-technology-contrast",
                "estimate": inference.mean_effect,
                "ci95_low": inference.ci95[0],
                "ci95_high": inference.ci95[1],
                "p_value": inference.p_sign_flip,
                "p_adjusted": inference.p_holm,
                "reject": inference.reject,
                "independent_n": inference.n_blocks,
                "evidence_kind": evidence_kind,
                "sesoi": contract.sesoi,
                "equivalence_lower": contract.equivalence_lower,
                "equivalence_upper": contract.equivalence_upper,
                "noninferiority_lower": contract.noninferiority_lower,
                "margin_status": margin_status,
            }
        ]
    ).to_parquet(destination / "effects.parquet", index=False)
    missingness_rows: list[dict[str, Any]] = []
    for run_dir, manifest, check in zip(run_dirs, manifests, run_checks, strict=True):
        config = cast(dict[str, Any], manifest["config"])
        missingness_rows.append(
            {
                "study_id": spec.study_id,
                "independent_block": str(config["independent_block"]),
                "run_id": str(manifest.get("run_id", run_dir.name)),
                "run_complete": manifest.get("status") == "complete",
                "verification_ok": check.ok,
                "missing_independent_unit": False,
                "terminal_failure": False,
                "decision_rows": check.decisions,
                "fill_rows": check.fills,
                "portfolio_rows": check.portfolio_rows,
                "error_count": len(check.errors),
                "warning_count": len(check.warnings),
                "errors_json": json.dumps(check.errors, sort_keys=True),
                "warnings_json": json.dumps(check.warnings, sort_keys=True),
                "scope_note": (
                    "run-level completeness; parse and provider failure states remain in "
                    "the hash-locked run inputs"
                ),
            }
        )
    pd.DataFrame(missingness_rows).to_parquet(
        destination / "missingness_failures.parquet", index=False
    )
    pd.DataFrame(
        _sensitivity_rows(spec.study_id, inference.block_effects, contract.sesoi)
    ).to_parquet(destination / "sensitivity_results.parquet", index=False)

    ordered_effects = [inference.block_effects[block] for block in sorted(inference.block_effects)]
    tost = equivalence_tost(
        ordered_effects,
        contract.equivalence_lower,
        contract.equivalence_upper,
        alpha=contract.alpha,
    )
    noninferiority = _noninferiority_result(
        ordered_effects, contract.noninferiority_lower, contract.alpha
    )
    margins_provisional = margin_status == "provisional-default"
    _write_json(
        destination / "equivalence_noninferiority.json",
        {
            "study_id": spec.study_id,
            "estimand_id": contract.estimand_id,
            "margin_status": margin_status,
            "margins_provisional": margins_provisional,
            "equivalence": {
                **tost.__dict__,
                "decision_rule": "both TOST one-sided p-values must be below alpha",
                "paper_claim_allowed": tost.equivalent and not margins_provisional,
            },
            "noninferiority": {
                **noninferiority,
                "paper_claim_allowed": (
                    bool(noninferiority["statistically_noninferior"])
                    and not margins_provisional
                ),
            },
            "interpretation_rule": (
                "nonsignificance is never evidence of equivalence; provisional margins "
                "cannot support paper claims"
            ),
        },
    )
    _write_json(
        destination / "estimand_registry.json",
        {
            "study_id": spec.study_id,
            "estimands": [
                {
                    "estimand_id": contract.estimand_id,
                    "question": (
                        "How much does matched LLM technology change Cohen's kappa relative "
                        "to matched classical technology within the frozen ecology contrast?"
                    ),
                    "outcome": "Cohen's kappa",
                    "contrast": "LLM minus matched classical block effect",
                    "independent_unit": (
                        "independently generated market trajectory or nonoverlapping "
                        "historical market-window cluster"
                    ),
                    "nested_units_not_independent": [
                        "model seed",
                        "agent",
                        "pair",
                        "step",
                        "call",
                        "retry",
                    ],
                    "inference": inference.method,
                    "sesoi": contract.sesoi,
                    "equivalence_bounds": [
                        contract.equivalence_lower,
                        contract.equivalence_upper,
                    ],
                    "noninferiority_lower": contract.noninferiority_lower,
                    "alpha": contract.alpha,
                    "margin_status": margin_status,
                    "margins_provisional": margins_provisional,
                    "limitations": [
                        "sampled dated model releases and classical families only",
                        "block-effect sign flips require the stated symmetry assumption",
                    ],
                }
            ],
        },
    )
    _write_json(
        destination / "multiplicity.json",
        {
            "family": "confirmatory-H1",
            "method": "Holm-Bonferroni",
            "hypotheses": {"H1": {"raw_p": inference.p_sign_flip, "adjusted_p": inference.p_holm}},
        },
    )
    _write_json(
        destination / "statistical_verification.json",
        {
            "verified": True,
            "independent_n": inference.n_blocks,
            "independent_unit": "market trajectory or nonoverlapping window cluster",
            "nested_units_not_counted": ["model seed", "agent", "pair", "step", "call", "retry"],
            "inference_method": inference.method,
            "margin_status": margin_status,
            "margins_frozen_before_analysis": not margins_provisional,
            "required_statistical_artifacts": [
                "estimand_registry.json",
                "equivalence_noninferiority.json",
                "missingness_failures.parquet",
                "sensitivity_results.parquet",
            ],
            "run_verifications": [check.model_dump() for check in run_checks],
        },
    )
    _write_json(
        destination / "claims.json",
        {
            "claims": [
                {
                    "claim_id": "H1-result",
                    "estimand_id": "H1-kappa-technology-contrast",
                    "effect_artifact": "effects.parquet",
                    "estimand_artifact": "estimand_registry.json",
                    "missingness_artifact": "missingness_failures.parquet",
                    "sensitivity_artifact": "sensitivity_results.parquet",
                    "equivalence_artifact": "equivalence_noninferiority.json",
                    "figures": ["figures/h1-block-effects.png"],
                    "limitations": [
                        "inference is limited to the sampled dated models and classical families",
                        "the sign-flip test assumes symmetric/exchangeable block effects",
                    ],
                    "verification_status": (
                        "paper-eligible" if paper else "verified-diagnostic"
                    ),
                    "evidence_kind": evidence_kind,
                    "margin_status": margin_status,
                }
            ]
        },
    )
    export_core_study_figures(destination, sesoi=contract.sesoi)
    artifact_hashes = {name: _sha256(destination / name) for name in CORE_ARTIFACTS}
    run_input_hashes = {
        str(run_dir): {name: _sha256(run_dir / name) for name in RUN_INPUTS}
        for run_dir in run_dirs
    }
    preregistration = spec.preregistration.model_dump() if spec.preregistration else None
    _write_json(
        destination / "release-manifest.json",
        {
            "schema_version": 2,
            "study_id": spec.study_id,
            "status": "complete",
            "evidence_kind": evidence_kind,
            "paper_requested": paper,
            "analysis_seed": seed,
            "expected_independent_blocks": sorted(expected_blocks),
            "preregistration": preregistration,
            "statistical_contract": contract.model_dump(),
            "margin_status": margin_status,
            "source_manifest": str(source_manifest),
            "source_manifest_sha256": _sha256(source_manifest),
            "run_input_sha256": run_input_hashes,
            "artifact_sha256": artifact_hashes,
        },
    )
    verification = verify_study_bundle(destination, require_paper=paper)
    if not verification.ok:
        raise ValueError(f"emitted study bundle failed verification: {verification.errors}")
    return destination


def _verify_crossed_artifacts(
    bundle_dir: Path,
    release: dict[str, Any],
    contract: FirstPaperStatisticalContract | None,
    independent_n: int,
) -> list[str]:
    errors: list[str] = []
    if contract is None:
        return ["release manifest lacks a valid first-paper statistical contract"]
    paper_requested = bool(release.get("paper_requested"))
    effects_path = bundle_dir / "effects.parquet"
    blocks_path = bundle_dir / "block_effects.parquet"
    if not effects_path.is_file() or not blocks_path.is_file():
        return errors
    effects = pd.read_parquet(effects_path)
    blocks = pd.read_parquet(blocks_path)
    analysis_inputs = cast(
        dict[str, dict[str, str]], release.get("analysis_input_sha256", {})
    )
    recomputed: FirstPaperEstimands | None = None
    if set(analysis_inputs) == {"crossed_rows", "lineage_rows", "mphiq_rows"}:
        try:
            input_frames = {
                name: pd.read_parquet(reference["path"])
                for name, reference in analysis_inputs.items()
            }
            run_manifests = [
                _json(Path(run_dir) / "manifest.json")
                for run_dir in cast(dict[str, Any], release.get("run_input_sha256", {}))
            ]
            _validate_aggregate_provenance(input_frames, run_manifests)
            recomputed = analyze_first_paper_estimands(
                input_frames["crossed_rows"],
                confirmatory_metrics=contract.confirmatory_metrics,
                lineage_rows=input_frames["lineage_rows"],
                mphiq_rows=input_frames["mphiq_rows"],
                alpha=contract.alpha,
                seed=int(release.get("analysis_seed", 0)),
            )
            block_columns = list(recomputed.block_effects.columns)
            effect_columns = list(recomputed.effects.columns)
            pd.testing.assert_frame_equal(
                blocks.sort_values(["estimand_id", "metric", "independent_block"])[
                    block_columns
                ].reset_index(drop=True),
                recomputed.block_effects.sort_values(
                    ["estimand_id", "metric", "independent_block"]
                )[block_columns].reset_index(drop=True),
                check_dtype=False,
            )
            pd.testing.assert_frame_equal(
                effects.sort_values(["estimand_id", "metric"])[effect_columns].reset_index(
                    drop=True
                ),
                recomputed.effects.sort_values(["estimand_id", "metric"])[
                    effect_columns
                ].reset_index(drop=True),
                check_dtype=False,
            )
        except (AssertionError, KeyError, OSError, ValueError):
            errors.append("crossed effects do not reproduce from frozen analysis inputs")
    effect_keys = {
        f"{row['estimand_id']}::{row['metric']}" for row in effects.to_dict("records")
    }
    if len(effects) != len(effect_keys) or effect_keys != set(contract.estimands):
        errors.append("crossed effects do not exactly match the frozen estimand family")
    expected_blocks = set(cast(list[str], release.get("expected_independent_blocks", [])))
    for key in sorted(effect_keys):
        estimand_id, metric = key.rsplit("::", 1)
        group = blocks.loc[
            (blocks["estimand_id"].astype(str) == estimand_id)
            & (blocks["metric"].astype(str) == metric)
        ]
        if (
            len(group) != independent_n
            or set(group["independent_block"].astype(str)) != expected_blocks
        ):
            errors.append(f"crossed block effects are incomplete for {key}")

    multiplicity_path = bundle_dir / "multiplicity.json"
    frozen_contrasts: set[str] = set()
    if multiplicity_path.is_file():
        multiplicity = _json(multiplicity_path)
        raw_hypotheses = multiplicity.get("hypotheses", {})
        hypotheses = (
            cast(dict[str, dict[str, Any]], raw_hypotheses)
            if isinstance(raw_hypotheses, dict)
            else {}
        )
        partitions: dict[str, set[str]] = {}
        for field in (
            "frozen_contrasts",
            "provisional_contrasts",
            "sensitivity_contrasts",
        ):
            raw_values = multiplicity.get(field)
            if not isinstance(raw_values, list) or any(
                not isinstance(value, str) for value in raw_values
            ):
                errors.append(f"multiplicity artifact has invalid {field}")
                partitions[field] = set()
            else:
                values = cast(list[str], raw_values)
                if len(values) != len(set(values)):
                    errors.append(f"multiplicity artifact repeats {field}")
                partitions[field] = set(values)
        frozen_contrasts = partitions["frozen_contrasts"]
        provisional_contrasts = partitions["provisional_contrasts"]
        sensitivity_contrasts = partitions["sensitivity_contrasts"]
        partition_union = (
            frozen_contrasts | provisional_contrasts | sensitivity_contrasts
        )
        partition_total = sum(
            len(values)
            for values in (
                frozen_contrasts,
                provisional_contrasts,
                sensitivity_contrasts,
            )
        )
        expected_h1_sensitivities = {
            f"{estimand_id}::{metric}"
            for estimand_id in H1_CONTRASTS
            for metric in contract.confirmatory_metrics
        }
        family_frozen = multiplicity.get("confirmatory_family_frozen") is True
        multiplicity_paper_eligible = multiplicity.get("paper_eligible") is True
        if (
            partition_union != effect_keys
            or partition_total != len(partition_union)
            or set(hypotheses) != effect_keys
        ):
            errors.append(
                "multiplicity artifact does not partition the declared analysis estimands"
            )
        if sensitivity_contrasts != expected_h1_sensitivities:
            errors.append("H1 sign flips must be sensitivity-only")
        if family_frozen != bool(frozen_contrasts):
            errors.append("multiplicity frozen-family state is inconsistent")
        if multiplicity_paper_eligible and not family_frozen:
            errors.append("unfrozen multiplicity cannot be paper-eligible")
        expected_family = (
            "confirmatory-H1-H3-H4"
            if family_frozen
            else "unfrozen-first-paper-analysis"
        )
        if multiplicity.get("family") != expected_family:
            errors.append("multiplicity family label is inconsistent with freeze state")
        if recomputed is not None and multiplicity != recomputed.multiplicity:
            errors.append("multiplicity artifact does not reproduce from analysis inputs")
        effect_map = {
            f"{row['estimand_id']}::{row['metric']}": row
            for row in effects.to_dict("records")
        }
        for key in sorted(expected_h1_sensitivities & set(effect_map)):
            effect = effect_map[key]
            hypothesis = hypotheses.get(key, {})
            if not (
                effect.get("inference_role") == "sensitivity_only"
                and effect.get("confirmatory") is False
                and effect.get("paper_eligible") is False
                and effect.get("multiplicity_status") == "excluded_sensitivity"
                and hypothesis.get("inference_role") == "sensitivity_only"
                and hypothesis.get("adjusted_p") is None
                and hypothesis.get("reject") is False
                and hypothesis.get("paper_eligible") is False
            ):
                errors.append(f"H1 sensitivity metadata is inconsistent for {key}")
        for key in sorted(frozen_contrasts & set(effect_map)):
            effect = effect_map[key]
            if not (
                effect.get("confirmatory") is True
                and effect.get("inference_role") == "confirmatory"
            ):
                errors.append(f"frozen estimand lacks confirmatory inference for {key}")
        if paper_requested and not (
            family_frozen and multiplicity_paper_eligible and frozen_contrasts
        ):
            errors.append("paper request relies on an unfrozen confirmatory analysis")

    sensitivity_path = bundle_dir / "sensitivity_results.parquet"
    if sensitivity_path.is_file():
        sensitivity = pd.read_parquet(sensitivity_path)
        primary = sensitivity.loc[sensitivity["specification_id"] == "primary-mean"]
        primary_keys = {
            f"{row['estimand_id']}::{row['metric']}" for row in primary.to_dict("records")
        }
        if len(primary) != len(effects) or primary_keys != effect_keys:
            errors.append("crossed sensitivities lack one primary row per estimand")
        else:
            estimates = {
                f"{row['estimand_id']}::{row['metric']}": float(row["estimate"])
                for row in effects.to_dict("records")
            }
            if any(
                not np.isclose(
                    float(row["estimate"]),
                    estimates[f"{row['estimand_id']}::{row['metric']}"],
                )
                for row in primary.to_dict("records")
            ):
                errors.append("crossed sensitivity primary estimates differ from effects")

    equivalence_path = bundle_dir / "equivalence_noninferiority.json"
    if equivalence_path.is_file():
        payload = _json(equivalence_path)
        results = cast(list[dict[str, Any]], payload.get("results", []))
        result_map = {
            f"{row.get('estimand_id')}::{row.get('metric')}": row for row in results
        }
        if len(results) != len(result_map) or set(result_map) != set(contract.estimands):
            errors.append("equivalence artifact does not cover every frozen estimand")
        else:
            for key, thresholds in contract.estimands.items():
                estimand_id, metric = key.rsplit("::", 1)
                values = blocks.loc[
                    (blocks["estimand_id"].astype(str) == estimand_id)
                    & (blocks["metric"].astype(str) == metric),
                    "effect",
                ].astype(float).tolist()
                expected_tost = equivalence_tost(
                    values,
                    thresholds.equivalence_lower,
                    thresholds.equivalence_upper,
                    alpha=contract.alpha,
                )
                expected_ni = _noninferiority_result(
                    values, thresholds.noninferiority_lower, contract.alpha
                )
                observed = result_map[key]
                tost = cast(dict[str, Any], observed.get("equivalence", {}))
                ni = cast(dict[str, Any], observed.get("noninferiority", {}))
                try:
                    tost_ok = all(
                        np.isclose(float(tost[field]), float(expected))
                        for field, expected in (
                            ("estimate", expected_tost.estimate),
                            ("lower_bound", expected_tost.lower_bound),
                            ("upper_bound", expected_tost.upper_bound),
                            ("p_lower", expected_tost.p_lower),
                            ("p_upper", expected_tost.p_upper),
                        )
                    ) and (
                        bool(tost["equivalent"]) == expected_tost.equivalent
                        and bool(tost["paper_claim_allowed"])
                        == (expected_tost.equivalent and paper_requested)
                    )
                    ni_ok = np.isclose(
                        float(ni["p_value"]), float(expected_ni["p_value"])
                    ) and (
                        bool(ni["statistically_noninferior"])
                        == bool(expected_ni["statistically_noninferior"])
                        and bool(ni["paper_claim_allowed"])
                        == (
                            bool(expected_ni["statistically_noninferior"])
                            and paper_requested
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    tost_ok = False
                    ni_ok = False
                if not tost_ok:
                    errors.append(f"equivalence result does not reproduce for {key}")
                if not ni_ok:
                    errors.append(f"noninferiority result does not reproduce for {key}")

    registry_path = bundle_dir / "estimand_registry.json"
    if registry_path.is_file():
        estimands = cast(
            list[dict[str, Any]], _json(registry_path).get("estimands", [])
        )
        registry_map = {
            f"{row.get('estimand_id')}::{row.get('metric')}": row for row in estimands
        }
        if len(estimands) != len(registry_map) or set(registry_map) != set(
            contract.estimands
        ):
            errors.append("estimand registry does not cover the frozen family")
        else:
            for key, thresholds in contract.estimands.items():
                observed = registry_map[key]
                if any(
                    observed.get(field) != value
                    for field, value in thresholds.model_dump().items()
                ) or observed.get("alpha") != contract.alpha:
                    errors.append(f"estimand registry thresholds differ for {key}")

    claims_path = bundle_dir / "claims.json"
    if claims_path.is_file():
        claims = cast(list[dict[str, Any]], _json(claims_path).get("claims", []))
        claim_map = {
            f"{row.get('estimand_id')}::{row.get('metric')}": row for row in claims
        }
        expected_status = "paper-eligible" if paper_requested else "mock-rehearsal"
        expected_evidence = "real" if paper_requested else "mock"
        expected_margin = (
            "frozen-preregistered" if paper_requested else "mock-rehearsal-only"
        )
        required_claims = frozen_contrasts if paper_requested else effect_keys
        if len(claims) != len(claim_map) or set(claim_map) != required_claims:
            errors.append("paper claims do not exactly cover the frozen estimand family")
        elif any(
            row.get("claim_id") != key
            or row.get("verification_status") != expected_status
            or row.get("evidence_kind") != expected_evidence
            or row.get("margin_status") != expected_margin
            for key, row in claim_map.items()
        ):
            errors.append("crossed claims contain inconsistent verification metadata")
    return errors


def verify_study_bundle(
    bundle_dir: Path, *, require_paper: bool = False
) -> StudyBundleVerification:
    """Verify hashes, independent-unit integrity, and optional paper gates."""
    bundle_dir = bundle_dir.resolve()
    errors: list[str] = []
    release_path = bundle_dir / "release-manifest.json"
    if not release_path.is_file():
        return StudyBundleVerification(
            bundle_dir=str(bundle_dir),
            ok=False,
            paper_eligible=False,
            evidence_kind="unknown",
            independent_units=0,
            errors=["missing release-manifest.json"],
        )
    release = _json(release_path)
    if release.get("schema_version") != 2:
        errors.append("release manifest schema is not the complete study-bundle version")
    if release.get("status") != "complete":
        errors.append("release manifest is incomplete")
    crossed_design = release.get("analysis_design") == "crossed-H1-H3-H4"
    contract: H1StatisticalContract | None = None
    paper_contract: FirstPaperStatisticalContract | None = None
    try:
        if crossed_design:
            paper_contract = FirstPaperStatisticalContract.model_validate(
                release.get("first_paper_statistical_contract")
            )
        else:
            contract = H1StatisticalContract.model_validate(
                release.get("statistical_contract")
            )
    except ValueError:
        errors.append(
            "release manifest lacks a valid first-paper statistical contract"
            if crossed_design
            else "release manifest lacks a valid statistical contract"
        )
    evidence_kind = cast(
        Literal["mock", "real", "unknown"], release.get("evidence_kind", "unknown")
    )
    source_manifest = Path(str(release.get("source_manifest", "")))
    if (
        not source_manifest.is_file()
        or release.get("source_manifest_sha256") != _sha256(source_manifest)
    ):
        errors.append("source manifest is missing or changed")
    run_hashes = cast(dict[str, dict[str, str]], release.get("run_input_sha256", {}))
    for raw_run_dir, expected_hashes in run_hashes.items():
        run_dir = Path(raw_run_dir)
        for name in RUN_INPUTS:
            path = run_dir / name
            if not path.is_file() or expected_hashes.get(name) != _sha256(path):
                errors.append(f"run input is missing or changed: {run_dir / name}")
    if crossed_design:
        analysis_hashes = cast(
            dict[str, dict[str, str]], release.get("analysis_input_sha256", {})
        )
        if set(analysis_hashes) != {"crossed_rows", "lineage_rows", "mphiq_rows"}:
            errors.append("release manifest lacks the complete crossed analysis inputs")
        for name, reference in analysis_hashes.items():
            path = Path(str(reference.get("path", "")))
            if not path.is_file() or reference.get("sha256") != _sha256(path):
                errors.append(f"paper analysis input is missing or changed: {name}")
    hashes = cast(dict[str, str], release.get("artifact_sha256", {}))
    for name in CORE_ARTIFACTS:
        path = bundle_dir / name
        if not path.is_file():
            errors.append(f"missing core artifact: {name}")
        elif hashes.get(name) != _sha256(path):
            errors.append(f"artifact hash mismatch: {name}")

    independent_n = 0
    independent_path = bundle_dir / "independent_units.parquet"
    if independent_path.is_file():
        units = pd.read_parquet(independent_path)
        independent_n = len(units)
        for column in ("independent_block", "dependence_cluster", "trajectory_id"):
            if column not in units or cast(pd.Series, units[column]).duplicated().any():
                errors.append(f"independent units require unique {column}")
        expected = set(cast(list[str], release.get("expected_independent_blocks", [])))
        actual = (
            set(cast(pd.Series, units["independent_block"]).astype(str))
            if "independent_block" in units
            else set()
        )
        if expected != actual:
            errors.append("independent units do not match the release manifest")

    stats_path = bundle_dir / "statistical_verification.json"
    if stats_path.is_file():
        stats = _json(stats_path)
        if stats.get("verified") is not True or stats.get("independent_n") != independent_n:
            errors.append("statistical verification is absent or inconsistent")
        if stats.get("margin_status") != release.get("margin_status"):
            errors.append("statistical verification margin status is inconsistent")
        if crossed_design and stats.get("analysis_design") != "crossed-H1-H3-H4":
            errors.append("statistical verification omits the crossed paper design")
        crossed_multiplicity = bundle_dir / "multiplicity.json"
        if crossed_design and crossed_multiplicity.is_file():
            multiplicity_frozen = (
                _json(crossed_multiplicity).get("confirmatory_family_frozen") is True
            )
            if stats.get("confirmatory_family_frozen") is not multiplicity_frozen:
                errors.append(
                    "statistical verification confirmatory freeze state is inconsistent"
                )

    missingness_path = bundle_dir / "missingness_failures.parquet"
    if missingness_path.is_file():
        missingness = pd.read_parquet(missingness_path)
        required = {
            "independent_block",
            "run_complete",
            "verification_ok",
            "missing_independent_unit",
            "terminal_failure",
        }
        if not required.issubset(missingness.columns):
            errors.append("missingness artifact lacks required run-level fields")
        else:
            missing_blocks = set(
                cast(pd.Series, missingness["independent_block"]).astype(str)
            )
            expected_blocks = set(
                cast(list[str], release.get("expected_independent_blocks", []))
            )
            if missing_blocks != expected_blocks or len(missingness) != independent_n:
                errors.append("missingness artifact does not reconcile to independent units")
            complete = cast(pd.Series, missingness["run_complete"]).astype(bool)
            verified = cast(pd.Series, missingness["verification_ok"]).astype(bool)
            absent = cast(pd.Series, missingness["missing_independent_unit"]).astype(bool)
            terminal = cast(pd.Series, missingness["terminal_failure"]).astype(bool)
            if not complete.all() or not verified.all() or absent.any() or terminal.any():
                errors.append("study bundle contains an incomplete or failed independent unit")

    if crossed_design:
        errors.extend(
            _verify_crossed_artifacts(
                bundle_dir, release, paper_contract, independent_n
            )
        )

    sensitivity_path = bundle_dir / "sensitivity_results.parquet"
    effects_path = bundle_dir / "effects.parquet"
    if not crossed_design and sensitivity_path.is_file() and effects_path.is_file():
        sensitivity = pd.read_parquet(sensitivity_path)
        effects = pd.read_parquet(effects_path)
        if "specification_id" not in sensitivity or "estimate" not in sensitivity:
            errors.append("sensitivity artifact lacks specification estimates")
        else:
            primary = sensitivity.loc[
                cast(pd.Series, sensitivity["specification_id"]) == "primary-mean"
            ]
            if len(primary) != 1 or len(effects) != 1 or not np.isclose(
                float(primary.iloc[0]["estimate"]), float(effects.iloc[0]["estimate"])
            ):
                errors.append("sensitivity primary estimate does not match effects")

    equivalence_path = bundle_dir / "equivalence_noninferiority.json"
    if not crossed_design and equivalence_path.is_file():
        equivalence = _json(equivalence_path)
        result = cast(dict[str, Any], equivalence.get("equivalence", {}))
        noninferiority = cast(dict[str, Any], equivalence.get("noninferiority", {}))
        try:
            alpha = float(result["alpha"])
            p_lower = float(result["p_lower"])
            p_upper = float(result["p_upper"])
            established = bool(result["equivalent"])
            expected_established = p_lower < alpha and p_upper < alpha
            provisional = bool(equivalence["margins_provisional"])
            claim_allowed = bool(result["paper_claim_allowed"])
        except (KeyError, TypeError, ValueError):
            errors.append("equivalence artifact is incomplete")
        else:
            if (
                not all(np.isfinite(value) and 0 <= value <= 1 for value in (p_lower, p_upper))
                or not 0 < alpha < 0.5
            ):
                errors.append("equivalence artifact contains invalid probabilities")
            if established != expected_established:
                errors.append("equivalence decision does not implement both TOST tests")
            if claim_allowed != (established and not provisional):
                errors.append("equivalence paper-claim gate is inconsistent")
            if equivalence.get("margin_status") != release.get("margin_status"):
                errors.append("equivalence margin status is inconsistent")
            block_path = bundle_dir / "block_effects.parquet"
            if contract is not None and block_path.is_file():
                blocks = pd.read_parquet(block_path).sort_values("independent_block")
                values = cast(pd.Series, blocks["effect"]).astype(float).tolist()
                recomputed = equivalence_tost(
                    values,
                    contract.equivalence_lower,
                    contract.equivalence_upper,
                    alpha=contract.alpha,
                )
                fields = (
                    ("estimate", recomputed.estimate),
                    ("lower_bound", recomputed.lower_bound),
                    ("upper_bound", recomputed.upper_bound),
                    ("p_lower", recomputed.p_lower),
                    ("p_upper", recomputed.p_upper),
                    ("alpha", recomputed.alpha),
                )
                try:
                    matches_tost = all(
                        np.isclose(float(result[name]), expected) for name, expected in fields
                    ) and bool(result["equivalent"]) == recomputed.equivalent
                    expected_noninferiority = _noninferiority_result(
                        values, contract.noninferiority_lower, contract.alpha
                    )
                    matches_noninferiority = np.isclose(
                        float(noninferiority["p_value"]),
                        float(expected_noninferiority["p_value"]),
                    ) and bool(noninferiority["statistically_noninferior"]) == bool(
                        expected_noninferiority["statistically_noninferior"]
                    )
                except (KeyError, TypeError, ValueError):
                    matches_tost = False
                    matches_noninferiority = False
                if not matches_tost:
                    errors.append("equivalence result does not reproduce from block effects")
                if not matches_noninferiority:
                    errors.append("noninferiority result does not reproduce from block effects")

    registry_path = bundle_dir / "estimand_registry.json"
    if not crossed_design and registry_path.is_file():
        registry = _json(registry_path)
        estimands = cast(list[dict[str, Any]], registry.get("estimands", []))
        if len(estimands) != 1:
            errors.append("estimand registry must contain exactly one primary H1 estimand")
        elif estimands[0].get("margin_status") != release.get("margin_status"):
            errors.append("estimand registry margin status is inconsistent")
        elif contract is not None and (
            estimands[0].get("sesoi") != contract.sesoi
            or estimands[0].get("equivalence_bounds")
            != [contract.equivalence_lower, contract.equivalence_upper]
            or estimands[0].get("noninferiority_lower") != contract.noninferiority_lower
        ):
            errors.append("estimand registry thresholds differ from the release contract")

    claims_path = bundle_dir / "claims.json"
    if claims_path.is_file() and require_paper:
        claims = cast(list[dict[str, Any]], _json(claims_path).get("claims", []))
        claims_unverified = any(
            claim.get("verification_status") != "paper-eligible" for claim in claims
        )
        if not claims or claims_unverified:
            errors.append("paper claims are not verification-eligible")

    crossed_family_paper_eligible = False
    crossed_multiplicity_path = bundle_dir / "multiplicity.json"
    if crossed_design and crossed_multiplicity_path.is_file():
        crossed_multiplicity = _json(crossed_multiplicity_path)
        raw_frozen = crossed_multiplicity.get("frozen_contrasts")
        crossed_family_paper_eligible = (
            isinstance(raw_frozen, list)
            and bool(raw_frozen)
            and all(isinstance(value, str) for value in raw_frozen)
            and crossed_multiplicity.get("confirmatory_family_frozen") is True
            and crossed_multiplicity.get("paper_eligible") is True
        )
    paper_eligible = (
        not errors
        and evidence_kind == "real"
        and bool(release.get("preregistration"))
        and bool(release.get("paper_requested"))
        and release.get("margin_status") == "frozen-preregistered"
        and crossed_design
        and crossed_family_paper_eligible
    )
    if require_paper:
        if not crossed_design:
            errors.append("paper verification requires the crossed H1/H3/H4 design")
        if evidence_kind != "real":
            errors.append("paper verification rejects mock evidence")
        if not release.get("paper_requested"):
            errors.append("bundle was not generated through the paper gate")
        if release.get("margin_status") != "frozen-preregistered":
            errors.append("paper verification requires preregistered statistical margins")
        if not crossed_family_paper_eligible:
            errors.append("paper verification requires a frozen confirmatory analysis")
        prereg = release.get("preregistration")
        if not prereg:
            errors.append("paper verification requires an immutable preregistration")
        else:
            source_path = Path(cast(dict[str, Any], prereg)["path"])
            if not source_path.is_absolute():
                source_path = (source_manifest.parent / source_path).resolve()
            if not source_path.is_file() or _sha256(source_path) != prereg["sha256"]:
                errors.append("preregistration is missing or its hash changed")
            else:
                try:
                    prereg_payload = _json(source_path)
                    prereg_contract = FirstPaperStatisticalContract.model_validate(
                        prereg_payload.get("first_paper_statistical_contract")
                    )
                except (json.JSONDecodeError, ValueError):
                    errors.append("preregistration lacks a valid statistical contract")
                else:
                    if paper_contract is None or prereg_contract != paper_contract:
                        errors.append(
                            "release first-paper statistical contract differs from preregistration"
                        )
        paper_eligible = not errors
    return StudyBundleVerification(
        bundle_dir=str(bundle_dir),
        ok=not errors,
        paper_eligible=paper_eligible,
        evidence_kind=evidence_kind,
        independent_units=independent_n,
        errors=errors,
    )


def reproduce_study_bundle(release_manifest: Path, output_dir: Path) -> Path:
    """Regenerate a release into a clean directory and require byte-identical artifacts."""
    release_manifest = release_manifest.resolve()
    if release_manifest.name != "release-manifest.json" or not release_manifest.is_file():
        raise ValueError("reproduce requires an existing release-manifest.json")
    original_dir = release_manifest.parent
    original_release = _json(release_manifest)
    require_paper = bool(original_release.get("paper_requested"))
    original_verification = verify_study_bundle(
        original_dir, require_paper=require_paper
    )
    if not original_verification.ok:
        raise ValueError(
            f"source release does not verify: {original_verification.errors}"
        )
    output_dir = output_dir.resolve()
    if output_dir == original_dir:
        raise ValueError("reproduction output must differ from the source bundle")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("reproduction output directory must be empty")
    source_manifest = Path(str(original_release["source_manifest"]))
    reproduced = analyze_study_bundle(
        source_manifest,
        output_dir=output_dir,
        paper=require_paper,
        seed=int(original_release.get("analysis_seed", 0)),
    )
    reproduced_release = _json(reproduced / "release-manifest.json")
    expected_hashes = cast(dict[str, str], original_release["artifact_sha256"])
    actual_hashes = cast(dict[str, str], reproduced_release["artifact_sha256"])
    if actual_hashes != expected_hashes:
        mismatches = sorted(
            name
            for name in set(expected_hashes) | set(actual_hashes)
            if expected_hashes.get(name) != actual_hashes.get(name)
        )
        raise ValueError(f"reproduction is not byte-identical: {mismatches}")
    _write_json(
        reproduced / "reproduction-verification.json",
        {
            "verified": True,
            "source_release_manifest": str(release_manifest),
            "source_release_manifest_sha256": _sha256(release_manifest),
            "artifact_sha256": actual_hashes,
        },
    )
    return reproduced
