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

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from flock.analysis.study import StudyInference, analyze_h1_study
from flock.experiments.verify import RunVerification, verify_run


class PreregistrationRef(BaseModel):
    """Immutable reference recorded before confirmatory calls."""

    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable_uri: str = Field(min_length=1)
    git_sha: str = Field(min_length=7)


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
    "multiplicity.json",
    "statistical_verification.json",
    "claims.json",
)
RUN_INPUTS = ("manifest.json", "decisions.jsonl", "fills.parquet", "portfolio.parquet")


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
            }
        ]
    ).to_parquet(destination / "effects.parquet", index=False)
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
                    "limitations": [
                        "inference is limited to the sampled dated models and classical families",
                        "the sign-flip test assumes symmetric/exchangeable block effects",
                    ],
                    "verification_status": (
                        "paper-eligible" if paper else "verified-diagnostic"
                    ),
                    "evidence_kind": evidence_kind,
                }
            ]
        },
    )
    artifact_hashes = {name: _sha256(destination / name) for name in CORE_ARTIFACTS}
    run_input_hashes = {
        str(run_dir): {name: _sha256(run_dir / name) for name in RUN_INPUTS}
        for run_dir in run_dirs
    }
    preregistration = spec.preregistration.model_dump() if spec.preregistration else None
    _write_json(
        destination / "release-manifest.json",
        {
            "schema_version": 1,
            "study_id": spec.study_id,
            "status": "complete",
            "evidence_kind": evidence_kind,
            "paper_requested": paper,
            "analysis_seed": seed,
            "expected_independent_blocks": sorted(expected_blocks),
            "preregistration": preregistration,
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
    if release.get("status") != "complete":
        errors.append("release manifest is incomplete")
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

    claims_path = bundle_dir / "claims.json"
    if claims_path.is_file() and require_paper:
        claims = cast(list[dict[str, Any]], _json(claims_path).get("claims", []))
        claims_unverified = any(
            claim.get("verification_status") != "paper-eligible" for claim in claims
        )
        if not claims or claims_unverified:
            errors.append("paper claims are not verification-eligible")

    paper_eligible = not errors and evidence_kind == "real" and bool(release.get("preregistration"))
    if require_paper:
        if evidence_kind != "real":
            errors.append("paper verification rejects mock evidence")
        if not release.get("paper_requested"):
            errors.append("bundle was not generated through the paper gate")
        prereg = release.get("preregistration")
        if not prereg:
            errors.append("paper verification requires an immutable preregistration")
        else:
            source_path = Path(cast(dict[str, Any], prereg)["path"])
            if not source_path.is_absolute():
                source_path = (source_manifest.parent / source_path).resolve()
            if not source_path.is_file() or _sha256(source_path) != prereg["sha256"]:
                errors.append("preregistration is missing or its hash changed")
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
