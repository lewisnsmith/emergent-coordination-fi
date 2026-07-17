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


class StudyBundleSpec(BaseModel):
    """Strict source manifest for one complete study bundle."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(min_length=1)
    status: Literal["complete", "incomplete"]
    evidence_kind: Literal["mock", "real"]
    expected_independent_blocks: list[str] = Field(min_length=2)
    run_dirs: list[str] = Field(min_length=2)
    preregistration: PreregistrationRef | None = None

    @model_validator(mode="after")
    def validate_counts(self) -> StudyBundleSpec:
        blocks = [block.strip() for block in self.expected_independent_blocks]
        if any(not block for block in blocks) or len(blocks) != len(set(blocks)):
            raise ValueError("expected independent blocks must be nonempty and unique")
        if len(self.run_dirs) != len(blocks):
            raise ValueError("one run directory is required per expected independent block")
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
    trajectories: set[str] = set()
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
        trajectory = _trajectory_identity(manifest)
        if trajectory in trajectories:
            raise ValueError(
                "duplicate market trajectory; block labels or model seeds do not create "
                f"independent evidence: {trajectory}"
            )
        trajectories.add(trajectory)
        manifests.append(manifest)
        verifications.append(verification)
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
    if paper:
        if spec.evidence_kind != "real" or evidence_kind != "real":
            raise ValueError("paper export rejects mock evidence")
        _check_preregistration(spec, source_manifest.parent)
    contract, margin_status = _statistical_contract(
        spec, source_manifest.parent, require_frozen=paper
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
    try:
        contract = H1StatisticalContract.model_validate(release.get("statistical_contract"))
    except ValueError:
        contract = None
        errors.append("release manifest lacks a valid statistical contract")
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

    sensitivity_path = bundle_dir / "sensitivity_results.parquet"
    effects_path = bundle_dir / "effects.parquet"
    if sensitivity_path.is_file() and effects_path.is_file():
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
    if equivalence_path.is_file():
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
    if registry_path.is_file():
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

    paper_eligible = (
        not errors
        and evidence_kind == "real"
        and bool(release.get("preregistration"))
        and bool(release.get("paper_requested"))
        and release.get("margin_status") == "frozen-preregistered"
    )
    if require_paper:
        if evidence_kind != "real":
            errors.append("paper verification rejects mock evidence")
        if not release.get("paper_requested"):
            errors.append("bundle was not generated through the paper gate")
        if release.get("margin_status") != "frozen-preregistered":
            errors.append("paper verification requires preregistered statistical margins")
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
                    prereg_contract = H1StatisticalContract.model_validate(
                        prereg_payload.get("statistical_contract")
                    )
                except (json.JSONDecodeError, ValueError):
                    errors.append("preregistration lacks a valid statistical contract")
                else:
                    if contract is None or prereg_contract != contract:
                        errors.append(
                            "release statistical contract differs from preregistration"
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
