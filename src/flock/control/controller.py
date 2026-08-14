"""Read-only status and fail-closed preflight for prompt-driven control."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field

from flock.control.ledger import ControlLedger, LedgerError
from flock.control.models import (
    AuthorizationTier,
    ProgramPhase,
    ProviderContractV1,
    Sha256,
    StrictFrozenModel,
    canonical_json_bytes,
    canonical_sha256,
)
from flock.control.program import (
    AUTHORIZATION_TIERS,
    PHASE_DEFINITIONS,
    PROGRAM_PHASES,
    tier_at_least,
)
from flock.experiments.materialize import MaterializedStudy

_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
_LEDGER_PATH = Path(".flock/control/ledger.sqlite3")
_EVIDENCE_FILES = (
    Path("docs/research/literature-search-and-screening-log.yaml"),
    Path("docs/research/external-evidence-matrix.yaml"),
    Path("docs/research/external-evidence-artifact-ledger.yaml"),
    Path("docs/research/external-evidence-audit-report.md"),
    Path("paper/references.bib"),
)


class RepositoryStatusV1(StrictFrozenModel):
    scaffold_ok: bool
    execution_ready: bool
    errors: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


class ControlHashesV1(StrictFrozenModel):
    source_sha256: Sha256
    tree_sha256: Sha256
    lock_sha256: Sha256
    control_sha256: Sha256


class LedgerStatusV1(StrictFrozenModel):
    path: str
    present: bool
    valid: bool
    phase_events: int = Field(default=0, ge=0)
    spend_events: int = Field(default=0, ge=0)
    phase_root_sha256: Sha256 | None = None
    spend_root_sha256: Sha256 | None = None
    unresolved_reservations: tuple[str, ...] = ()
    unresolved_dispatches: tuple[str, ...] = ()
    unresolved_unknowns: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class ControlStatusV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    repository_root: str
    program_phases: tuple[ProgramPhase, ...]
    tier_order: tuple[AuthorizationTier, ...]
    hashes: ControlHashesV1
    dirty_paths: tuple[str, ...]
    ledger: LedgerStatusV1
    signer_enrollment_count: int = Field(ge=0)
    study_plan_sha256: Sha256 | None = None
    repository: RepositoryStatusV1
    blockers: dict[str, tuple[str, ...]]
    highest_safe_tier: AuthorizationTier
    state_sha256: Sha256


class PreflightPacketV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    operation: Literal["preflight"] = "preflight"
    phase: ProgramPhase
    tier: AuthorizationTier
    output_root: str
    materialization_path: str
    materialization_sha256: Sha256 | None
    materialization_file_sha256: Sha256 | None
    study_id: str | None
    study_plan_sha256: Sha256 | None
    selected_assignments: int = Field(ge=0)
    selected_assignment_ids_sha256: Sha256
    status_state_sha256: Sha256
    hashes: ControlHashesV1
    ready: bool
    blockers: tuple[str, ...]
    packet_sha256: Sha256


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(repo: Path, *arguments: str) -> bytes | None:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _sensitive_path(path: Path) -> bool:
    lowered = tuple(part.lower() for part in path.parts)
    name = path.name.lower()
    return (
        any(part in {".git", ".venv", ".venv.nosync", "__pycache__"} for part in lowered)
        or name == ".env"
        or name.startswith(".env.")
        or path.suffix.lower() in {".key", ".pem", ".p12", ".pfx"}
    )


def _source_files(repo: Path) -> tuple[Path, ...]:
    tracked = _git(repo, "ls-files", "-z")
    if tracked is not None:
        candidates = [
            Path(item.decode("utf-8", errors="replace")) for item in tracked.split(b"\0") if item
        ]
    else:
        candidates = [
            path.relative_to(repo)
            for root in ("src", "configs", "docs", "paper", "tests", ".agents")
            if (repo / root).exists()
            for path in (repo / root).rglob("*")
            if path.is_file()
        ]
        candidates.extend(
            Path(name)
            for name in ("pyproject.toml", "AGENTS.md", "CLAUDE.md")
            if (repo / name).is_file()
        )
    return tuple(
        sorted(
            {path for path in candidates if not _sensitive_path(path) and (repo / path).is_file()},
            key=lambda path: path.as_posix(),
        )
    )


def _path_set_sha256(repo: Path, paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(_sha256(repo / relative)))
    return digest.hexdigest()


def _dirty_paths(repo: Path) -> tuple[str, ...]:
    output = _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if output is None:
        return tuple(path.as_posix() for path in _source_files(repo))
    records = output.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) < 4:
            index += 1
            continue
        status = record[:2]
        paths.append(record[3:].decode("utf-8", errors="replace"))
        if b"R" in status or b"C" in status:
            index += 1
            if index < len(records) and records[index]:
                paths.append(records[index].decode("utf-8", errors="replace"))
        index += 1
    return tuple(sorted(set(paths)))


def _hashes(repo: Path) -> ControlHashesV1:
    source = _path_set_sha256(repo, _source_files(repo))
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    tree_sha = hashlib.sha256(tree.strip()).hexdigest() if tree else source
    lock = repo / "uv.lock"
    control_paths = tuple(
        sorted(
            (
                *(
                    path.relative_to(repo)
                    for path in (repo / "src/flock/control").glob("*.py")
                    if path.is_file()
                ),
                Path("configs/control/authorized_signers"),
            ),
            key=lambda path: path.as_posix(),
        )
    )
    return ControlHashesV1(
        source_sha256=source,
        tree_sha256=tree_sha,
        lock_sha256=_sha256(lock) if lock.is_file() else _EMPTY_SHA256,
        control_sha256=_path_set_sha256(
            repo, tuple(path for path in control_paths if (repo / path).is_file())
        ),
    )


def _repository_status(repo: Path) -> RepositoryStatusV1:
    try:
        from flock.experiments.verify import verify_repository

        result = verify_repository(repo)
    except (KeyError, OSError, ValueError) as error:
        return RepositoryStatusV1(
            scaffold_ok=False,
            execution_ready=False,
            errors=(f"repository verification failed: {error}",),
            blockers=(),
            warnings=(),
        )
    return RepositoryStatusV1(
        scaffold_ok=result.scaffold_ok,
        execution_ready=result.execution_ready,
        errors=tuple(sorted(result.errors)),
        blockers=tuple(sorted(result.blockers)),
        warnings=tuple(sorted(result.warnings)),
    )


def _ledger_status(repo: Path) -> LedgerStatusV1:
    path = (repo / _LEDGER_PATH).resolve()
    if not path.is_file():
        return LedgerStatusV1(path=str(path), present=False, valid=True)
    try:
        ledger = object.__new__(ControlLedger)
        ledger.path = path
        verified = ledger.verify()
    except (LedgerError, OSError, sqlite3.Error) as error:
        return LedgerStatusV1(
            path=str(path),
            present=True,
            valid=False,
            errors=(f"ledger verification failed: {error}",),
        )
    return LedgerStatusV1(
        path=str(path),
        present=True,
        valid=True,
        phase_events=verified.phase_events,
        spend_events=verified.spend_events,
        phase_root_sha256=verified.phase_root_sha256,
        spend_root_sha256=verified.spend_root_sha256,
        unresolved_reservations=verified.unresolved_reservations,
        unresolved_dispatches=verified.unresolved_dispatches,
        unresolved_unknowns=verified.unresolved_unknowns,
    )


def _signers(repo: Path) -> tuple[int, tuple[str, ...]]:
    path = repo / "configs/control/authorized_signers"
    if not path.is_file():
        return 0, ("authorized signer file is missing",)
    count = 0
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        key_index = next(
            (
                index
                for index, field in enumerate(fields[1:], start=1)
                if field.startswith(("ssh-", "ecdsa-", "sk-"))
            ),
            None,
        )
        if key_index is None or key_index + 1 >= len(fields):
            errors.append(f"authorized signer entry {line_number} is malformed")
        else:
            count += 1
    if count == 0:
        errors.append("no production public signer is enrolled")
    return count, tuple(sorted(errors))


def _yaml_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain one mapping")
    return value


def _mapping_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _evidence_blockers(repo: Path) -> tuple[str, ...]:
    missing = [path.as_posix() for path in _EVIDENCE_FILES if not (repo / path).is_file()]
    if missing:
        return tuple(f"external-evidence audit file is missing: {path}" for path in missing)
    try:
        log = _yaml_mapping(repo / _EVIDENCE_FILES[0])
        matrix = _yaml_mapping(repo / _EVIDENCE_FILES[1])
        artifacts = _yaml_mapping(repo / _EVIDENCE_FILES[2])
    except (OSError, ValueError, yaml.YAMLError) as error:
        return (f"external-evidence audit cannot be parsed: {error}",)

    blockers: list[str] = []
    snapshots = {log.get("snapshot_id"), matrix.get("snapshot_id"), artifacts.get("snapshot_id")}
    if len(snapshots) != 1 or None in snapshots:
        blockers.append("external-evidence snapshot identifiers do not match")
    coverage = _mapping_value(log.get("coverage"))
    if len(set(coverage.get("lanes") or [])) != 21:
        blockers.append("external-evidence audit does not bind all 21 lanes")
    if len(set(coverage.get("hypotheses") or [])) != 14:
        blockers.append("external-evidence audit does not bind all registered hypotheses")
    if set(coverage.get("experiments") or []) != {f"exp-{index:03d}" for index in range(27)}:
        blockers.append("external-evidence audit does not bind exp-000 through exp-026")

    reviews = artifacts.get("artifact_reviews") or []
    families = log.get("work_families") or []
    for review in reviews:
        if isinstance(review, dict) and (not review.get("location") or not review.get("version")):
            blockers.append(f"evidence warning artifact_version: {review.get('id', '<missing>')}")
    direct_or_substitution = {
        str(item.get("id"))
        for item in families
        if isinstance(item, dict)
        and (
            item.get("ring") == "direct"
            or item.get("use") in {"partial_substitute", "full_substitute"}
        )
    }
    reviewed_sources = {
        str(source)
        for review in reviews
        if isinstance(review, dict)
        for source in review.get("source_ids") or []
    }
    if direct_or_substitution - reviewed_sources:
        blockers.append("evidence warning artifact_review_gap: direct sources lack reviews")
    calibration = _mapping_value(log.get("calibration"))
    if not isinstance(calibration.get("source_ids"), list):
        blockers.append("evidence warning dual_screen_untraceable: source ids are not recorded")
    return tuple(sorted(set(blockers)))


def _science_blockers(repo: Path) -> tuple[tuple[str, ...], str | None]:
    blockers: list[str] = []
    plan_hash: str | None = None
    try:
        from flock.experiments.study import compile_study_file

        plan_hash = compile_study_file(repo / "configs/studies/paper-core.yaml").plan_hash
    except (KeyError, OSError, ValueError) as error:
        blockers.append(f"study plan does not compile deterministically: {error}")
    lock_path = repo / "configs/control/science-lock.json"
    if not lock_path.is_file():
        blockers.append("ScienceLockV1 is missing")
    else:
        try:
            record = json.loads(lock_path.read_text(encoding="utf-8"))
            required = {
                "schema_version",
                "study_plan_sha256",
                "primary_cluster_aware_model",
                "directions",
                "sesois",
                "missingness",
                "multiplicity",
                "attainable_power",
                "science_lock_sha256",
            }
            if not isinstance(record, dict) or set(record) != required:
                raise ValueError("ScienceLockV1 fields are incomplete or unexpected")
            if record["schema_version"] != 1:
                raise ValueError("ScienceLockV1 has an unsupported schema version")
            declared = record.pop("science_lock_sha256")
            if declared != canonical_sha256(record):
                raise ValueError("ScienceLockV1 hash does not match its contents")
            if plan_hash is None or record["study_plan_sha256"] != plan_hash:
                raise ValueError("ScienceLockV1 does not bind the current study plan")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            blockers.append(f"ScienceLockV1 is invalid: {error}")
    return tuple(sorted(blockers)), plan_hash


def _preregistration_blockers(repo: Path) -> tuple[str, ...]:
    blockers: list[str] = []
    document = repo / "docs/research/preregistration.md"
    if not document.is_file():
        blockers.append("preregistration document is missing")
    elif "status: draft" in document.read_text(encoding="utf-8").lower():
        blockers.append("preregistration remains a draft")
    receipt = repo / "configs/control/preregistration-receipt.json"
    if not receipt.is_file():
        blockers.append("immutable preregistration receipt is missing")
        return tuple(sorted(blockers))
    try:
        record = json.loads(receipt.read_text(encoding="utf-8"))
        required = {
            "schema_version",
            "document_sha256",
            "git_commit",
            "git_tag",
            "registered_at",
            "registry_id",
            "receipt_sha256",
        }
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError("receipt fields are incomplete or unexpected")
        body = {key: value for key, value in record.items() if key != "receipt_sha256"}
        if record["schema_version"] != 1 or record["receipt_sha256"] != canonical_sha256(body):
            raise ValueError("receipt schema or canonical hash is invalid")
        commit = record["git_commit"]
        if (
            not isinstance(commit, str)
            or len(commit) != 40
            or any(character not in "0123456789abcdef" for character in commit)
        ):
            raise ValueError("receipt git commit is not a full lowercase object id")
        registered_at = datetime.fromisoformat(str(record["registered_at"]).replace("Z", "+00:00"))
        if registered_at.tzinfo is None or registered_at.utcoffset() is None:
            raise ValueError("receipt registration time has no UTC offset")
        if not isinstance(record["registry_id"], str) or not record["registry_id"].strip():
            raise ValueError("receipt registry id is empty")
        declared_document = record["document_sha256"]
        if not isinstance(declared_document, str) or (
            document.is_file() and declared_document != _sha256(document)
        ):
            raise ValueError("receipt does not bind the current preregistration")
        committed_document = _git(repo, "show", f"{commit}:docs/research/preregistration.md")
        if (
            committed_document is None
            or hashlib.sha256(committed_document).hexdigest() != declared_document
        ):
            raise ValueError("receipt does not bind the preregistration at its commit")
        tag = record["git_tag"]
        if not isinstance(tag, str) or not tag.strip():
            raise ValueError("receipt git tag is empty")
        tag_target = _git(repo, "rev-list", "-n", "1", tag)
        if tag_target is None or tag_target.strip().decode("ascii", errors="replace") != commit:
            raise ValueError("receipt tag does not resolve to its frozen commit")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        blockers.append(f"immutable preregistration receipt is invalid: {error}")
    return tuple(sorted(blockers))


def _data_blockers(repo: Path, repository: RepositoryStatusV1) -> tuple[str, ...]:
    blockers = [
        item for item in (*repository.errors, *repository.blockers) if "dataset" in item.lower()
    ]
    for name in ("dataset-manifest-v3.json", "split-registry-v1.json"):
        if not (repo / "configs/control" / name).is_file():
            blockers.append(f"{name} is missing")
    return tuple(sorted(set(blockers)))


def _provider_blockers(repo: Path, signer_errors: tuple[str, ...]) -> tuple[str, ...]:
    blockers = list(signer_errors)
    contracts = sorted((repo / "configs/control/provider-contracts").glob("*.json"))
    pricing_path = repo / "configs/budgets/pricing.yaml"
    pricing_sha256 = _sha256(pricing_path) if pricing_path.is_file() else None
    if not contracts:
        blockers.append("no ProviderContractV1 snapshot is installed")
    for path in contracts:
        try:
            contract = ProviderContractV1.model_validate_json(path.read_text(encoding="utf-8"))
            if pricing_sha256 is None or contract.pricing_sha256 != pricing_sha256:
                blockers.append(
                    f"provider contract {path.name} does not bind the current pricing catalog"
                )
        except (OSError, ValueError) as error:
            blockers.append(f"provider contract {path.name} is invalid: {error}")
    if not (repo / "src/flock/control/worker.py").is_file():
        blockers.append("authorization-bound external worker is not implemented")
    return tuple(sorted(set(blockers)))


def build_status(repo_root: Path = Path(".")) -> ControlStatusV1:
    """Build a deterministic snapshot without reading credentials or environment values."""

    repo = repo_root.resolve()
    repository = _repository_status(repo)
    ledger = _ledger_status(repo)
    signer_count, signer_errors = _signers(repo)
    science, plan_hash = _science_blockers(repo)
    hashes = _hashes(repo)
    blockers = {
        "science": science,
        "evidence": _evidence_blockers(repo),
        "preregistration": _preregistration_blockers(repo),
        "data": _data_blockers(repo, repository),
        "provider": _provider_blockers(repo, signer_errors),
        "repository": tuple(sorted((*repository.errors, *repository.blockers))),
        "ledger": tuple(
            sorted(
                (
                    *ledger.errors,
                    *ledger.unresolved_reservations,
                    *ledger.unresolved_dispatches,
                    *ledger.unresolved_unknowns,
                )
            )
        ),
    }
    ledger_clear = ledger.valid and not (
        ledger.unresolved_reservations or ledger.unresolved_dispatches or ledger.unresolved_unknowns
    )
    highest: AuthorizationTier = "mock" if repository.scaffold_ok and ledger_clear else "plan"
    payload = {
        "schema_version": 1,
        "repository_root": str(repo),
        "program_phases": PROGRAM_PHASES,
        "tier_order": AUTHORIZATION_TIERS,
        "hashes": hashes,
        "dirty_paths": _dirty_paths(repo),
        "ledger": ledger,
        "signer_enrollment_count": signer_count,
        "study_plan_sha256": plan_hash,
        "repository": repository,
        "blockers": blockers,
        "highest_safe_tier": highest,
    }
    hash_payload = {
        **payload,
        "hashes": hashes.model_dump(mode="json"),
        "ledger": ledger.model_dump(mode="json"),
        "repository": repository.model_dump(mode="json"),
    }
    return ControlStatusV1.model_validate(
        {**payload, "state_sha256": canonical_sha256(hash_payload)}
    )


def _load_materialization(path: Path) -> tuple[MaterializedStudy | None, tuple[str, ...]]:
    if not path.is_file():
        return None, (f"materialization file is missing: {path}",)
    try:
        materialized = MaterializedStudy.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return None, (f"materialization is invalid: {error}",)
    assignments = [item.model_dump(mode="json") for item in materialized.assignments]
    expected_hash = hashlib.sha256(
        json.dumps(assignments, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    blockers: list[str] = []
    if expected_hash != materialized.materialization_hash:
        blockers.append("materialization hash does not match its assignments")
    if [item.ordinal for item in materialized.assignments] != list(
        range(1, materialized.exact_runs + 1)
    ):
        blockers.append("materialization ordinals are not contiguous")
    if len({item.assignment_id for item in materialized.assignments}) != materialized.exact_runs:
        blockers.append("materialization assignment ids are not unique")
    if any(
        item.study_id != materialized.study_id or item.plan_hash != materialized.plan_hash
        for item in materialized.assignments
    ):
        blockers.append("materialization assignments do not bind one study and plan")
    totals = (
        len(materialized.assignments),
        sum(item.exact_counts.steps for item in materialized.assignments),
        sum(item.exact_counts.agent_steps for item in materialized.assignments),
        sum(item.exact_counts.calls for item in materialized.assignments),
        sum(item.execution_config is not None for item in materialized.assignments),
    )
    if totals != (
        materialized.exact_runs,
        materialized.exact_steps,
        materialized.exact_agent_steps,
        materialized.exact_calls,
        materialized.executable_runs,
    ):
        blockers.append("materialization declared totals do not rederive from assignments")
    return materialized, tuple(sorted(blockers))


def _selected_assignments(
    materialized: MaterializedStudy, tier: AuthorizationTier
) -> tuple[Any, ...]:
    if tier in {"canary", "pilot", "confirmatory"}:
        return tuple(item for item in materialized.assignments if item.authorization_stage == tier)
    return tuple(materialized.assignments)


def _local_assignment_blockers(repo: Path, assignments: tuple[Any, ...]) -> tuple[str, ...]:
    from flock.core.config import ExperimentConfig, load_models

    blockers: list[str] = []
    try:
        models = load_models(repo / "configs/models.yaml")
    except (OSError, ValueError) as error:
        return (f"model registry cannot be verified locally: {error}",)
    for assignment in assignments:
        if assignment.evidence_kind != "mock":
            blockers.append(f"{assignment.assignment_id}: mock tier requires evidence_kind=mock")
        if assignment.execution_config is None:
            blockers.append(f"{assignment.assignment_id}: no executable configuration")
            continue
        try:
            config = ExperimentConfig.model_validate(assignment.execution_config)
        except ValueError as error:
            blockers.append(f"{assignment.assignment_id}: invalid execution configuration: {error}")
            continue
        for cohort in config.cohorts:
            for group in cohort.agents:
                if group.kind != "llm":
                    continue
                spec = models.get(group.model or "")
                if spec is None or (spec.provider != "mock" and spec.deployment != "local"):
                    blockers.append(
                        f"{assignment.assignment_id}: model {group.model!r} is not mock/local"
                    )
    return tuple(sorted(set(blockers)))


def build_preflight(
    *,
    repo_root: Path,
    phase: ProgramPhase,
    tier: AuthorizationTier,
    materialization_path: Path,
    output_root: Path,
) -> PreflightPacketV1:
    """Assess one exact request and emit a hash-bound packet without executing it."""

    repo = repo_root.resolve()
    materialization_file = materialization_path.resolve()
    resolved_output = output_root.resolve()
    status = build_status(repo)
    materialized, materialization_blockers = _load_materialization(materialization_file)
    blockers = list(materialization_blockers)
    selected: tuple[Any, ...] = ()
    if materialized is not None:
        selected = _selected_assignments(materialized, tier)
        if tier_at_least(tier, "canary") and not selected:
            blockers.append(f"materialization has no assignments for tier {tier}")
        if tier == "mock":
            blockers.extend(_local_assignment_blockers(repo, selected))
            blockers.extend(status.blockers["ledger"])
        elif tier_at_least(tier, "canary"):
            if materialized.plan_hash != status.study_plan_sha256:
                blockers.append("live materialization does not bind the current compiled plan")
            blockers.extend(
                item
                for category in (
                    "science",
                    "evidence",
                    "preregistration",
                    "data",
                    "provider",
                    "repository",
                    "ledger",
                )
                for item in status.blockers[category]
            )
            if status.dirty_paths:
                blockers.append("live preflight requires a clean source tree")
            for assignment in selected:
                if assignment.evidence_kind != "real":
                    blockers.append(
                        f"{assignment.assignment_id}: live tier requires evidence_kind=real"
                    )
                if assignment.execution_config is None:
                    blockers.append(f"{assignment.assignment_id}: no executable configuration")

    definition = next(item for item in PHASE_DEFINITIONS if item.phase == phase)
    if tier_at_least(tier, "canary"):
        if definition.external_tier is None:
            blockers.append(f"phase {phase} is local-only and cannot use a live tier")
        elif not tier_at_least(tier, definition.external_tier):
            blockers.append(
                f"phase {phase} requires tier {definition.external_tier} or higher "
                "for external work"
            )
    if tier in {"plan", "mock"} and not status.repository.scaffold_ok:
        blockers.extend(status.repository.errors)

    assignment_ids = tuple(sorted(item.assignment_id for item in selected))
    payload = {
        "schema_version": 1,
        "operation": "preflight",
        "phase": phase,
        "tier": tier,
        "output_root": str(resolved_output),
        "materialization_path": str(materialization_file),
        "materialization_sha256": (
            materialized.materialization_hash if materialized is not None else None
        ),
        "materialization_file_sha256": (
            _sha256(materialization_file) if materialization_file.is_file() else None
        ),
        "study_id": materialized.study_id if materialized is not None else None,
        "study_plan_sha256": materialized.plan_hash if materialized is not None else None,
        "selected_assignments": len(selected),
        "selected_assignment_ids_sha256": canonical_sha256(assignment_ids),
        "status_state_sha256": status.state_sha256,
        "hashes": status.hashes,
        "ready": not blockers,
        "blockers": tuple(sorted(set(blockers))),
    }
    hash_payload = {**payload, "hashes": status.hashes.model_dump(mode="json")}
    return PreflightPacketV1.model_validate(
        {**payload, "packet_sha256": canonical_sha256(hash_payload)}
    )


def canonical_output(record: StrictFrozenModel) -> str:
    """Render one control record using its canonical byte representation."""

    return canonical_json_bytes(record).decode("utf-8")
