"""Authenticated data-lineage and split records for controlled experiments."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, StringConstraints, field_validator, model_validator

from flock.control.models import (
    Identifier,
    Sha256,
    StrictFrozenModel,
    canonical_sha256,
)

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PrivacyClass = Literal["public", "restricted", "confidential", "personal", "sensitive"]
ReleaseClass = Literal["public", "restricted", "metadata-only", "prohibited"]
SourceClass = Literal["synthetic", "real"]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value.astimezone(UTC)


def _validate_reference_uri(value: str, *, https_only: bool = False) -> str:
    parsed = urlsplit(value)
    schemes = {"https"} if https_only else {"https", "s3", "gs"}
    if parsed.scheme not in schemes or not parsed.hostname:
        raise ValueError(f"URI must use one of {sorted(schemes)} and include a host")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("URI must not contain credentials or a fragment")
    return value


class RawAcquisitionReceiptV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    artifact_id: Identifier
    uri: Annotated[str, StringConstraints(min_length=8, max_length=2_000)]
    source_version: NonEmptyText
    retrieved_at: datetime
    raw_bytes: Annotated[int, Field(ge=0)]
    raw_sha256: Sha256

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, value: str) -> str:
        return _validate_reference_uri(value)

    @field_validator("retrieved_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _utc(value)


class RightsRecordV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    license_id: NonEmptyText
    terms_uri: Annotated[str, StringConstraints(min_length=8, max_length=2_000)]
    terms_sha256: Sha256
    verified_at: datetime
    permitted_uses: tuple[Identifier, ...] = Field(min_length=1)

    @field_validator("license_id")
    @classmethod
    def reject_placeholder_rights(cls, value: str) -> str:
        if value.casefold() in {"none", "noassertion", "tbd", "unknown"}:
            raise ValueError("license_id must identify verified rights, not a placeholder")
        return value

    @field_validator("terms_uri")
    @classmethod
    def validate_terms_uri(cls, value: str) -> str:
        return _validate_reference_uri(value, https_only=True)

    @field_validator("verified_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _utc(value)

    @field_validator("permitted_uses")
    @classmethod
    def require_sorted_unique_uses(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != tuple(sorted(set(value))):
            raise ValueError("permitted_uses must be sorted and unique")
        return value


class DatasetFileV1(StrictFrozenModel):
    path: Annotated[str, StringConstraints(min_length=1, max_length=1_000)]
    bytes: Annotated[int, Field(ge=0)]
    file_sha256: Sha256

    @field_validator("path")
    @classmethod
    def require_safe_relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or str(path) != value
            or any(part in {"", ".", ".."} for part in path.parts)
            or "\\" in value
        ):
            raise ValueError("payload paths must be normalized relative POSIX paths")
        return value


class TransformationStepV1(StrictFrozenModel):
    step_id: Identifier
    code_sha256: Sha256
    parameters_sha256: Sha256
    input_sha256s: tuple[Sha256, ...] = Field(min_length=1)
    output_sha256: Sha256

    @field_validator("input_sha256s")
    @classmethod
    def require_sorted_unique_inputs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != tuple(sorted(set(value))):
            raise ValueError("transformation inputs must be sorted and unique")
        return value


class DatasetWindowV1(StrictFrozenModel):
    window_id: Identifier
    family_id: Identifier
    requested_start: datetime
    requested_end: datetime
    observed_start: datetime
    observed_end: datetime
    selected_rows: Annotated[int, Field(ge=1)]
    selected_rows_sha256: Sha256
    content_sha256: Sha256
    content_unit_id: Identifier
    overlap_cluster_id: Identifier

    @field_validator(
        "requested_start",
        "requested_end",
        "observed_start",
        "observed_end",
    )
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.requested_end < self.requested_start:
            raise ValueError("requested window end precedes its start")
        if self.observed_end < self.observed_start:
            raise ValueError("observed window end precedes its start")
        if not (
            self.requested_start <= self.observed_start
            and self.observed_end <= self.requested_end
        ):
            raise ValueError("observed rows fall outside the requested window")
        if self.content_sha256 != self.selected_rows_sha256:
            raise ValueError("content SHA-256 must be the canonical selected-row hash")
        expected_unit = f"unit:{self.content_sha256}"
        if self.content_unit_id != expected_unit:
            raise ValueError("content_unit_id must be derived from the content SHA-256")
        return self


class DatasetManifestV3(StrictFrozenModel):
    schema_version: Literal[3] = 3
    dataset_name: Identifier
    dataset_version: Annotated[int, Field(ge=1)]
    source_class: SourceClass
    raw_acquisitions: tuple[RawAcquisitionReceiptV1, ...] = Field(min_length=1)
    rights: RightsRecordV1
    privacy_class: PrivacyClass
    release_class: ReleaseClass
    timestamp_semantics: NonEmptyText
    transformation_dag: tuple[TransformationStepV1, ...] = Field(min_length=1)
    payload_files: tuple[DatasetFileV1, ...] = Field(min_length=1)
    dataset_bundle_sha256: Sha256
    windows: tuple[DatasetWindowV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_manifest(self) -> Self:
        if self.privacy_class in {"confidential", "personal", "sensitive"} and (
            self.release_class == "public"
        ):
            raise ValueError("non-public data cannot have a public release class")

        artifact_ids = tuple(item.artifact_id for item in self.raw_acquisitions)
        if artifact_ids != tuple(sorted(set(artifact_ids))):
            raise ValueError("raw acquisitions must be sorted by unique artifact_id")
        raw_hashes = tuple(item.raw_sha256 for item in self.raw_acquisitions)
        if len(raw_hashes) != len(set(raw_hashes)):
            raise ValueError("duplicate raw bytes must not be relabeled as separate artifacts")

        payload_paths = tuple(item.path for item in self.payload_files)
        if payload_paths != tuple(sorted(set(payload_paths))):
            raise ValueError("payload files must be sorted by unique path")
        expected_bundle = canonical_sha256(
            {item.path: item.file_sha256 for item in self.payload_files}
        )
        if self.dataset_bundle_sha256 != expected_bundle:
            raise ValueError("dataset bundle root does not match the payload inventory")

        known_hashes = set(raw_hashes)
        step_ids: set[str] = set()
        for step in self.transformation_dag:
            if step.step_id in step_ids:
                raise ValueError("transformation step IDs must be unique")
            if not set(step.input_sha256s).issubset(known_hashes):
                raise ValueError("transformation DAG references an unknown or future input")
            if step.output_sha256 in known_hashes:
                raise ValueError("transformation outputs must be unique")
            step_ids.add(step.step_id)
            known_hashes.add(step.output_sha256)
        if self.transformation_dag[-1].output_sha256 != self.dataset_bundle_sha256:
            raise ValueError("the final transformation must produce the dataset bundle root")

        window_ids = tuple(window.window_id for window in self.windows)
        if window_ids != tuple(sorted(set(window_ids))):
            raise ValueError("windows must be sorted by unique window_id")
        content_hashes = tuple(window.content_sha256 for window in self.windows)
        if len(content_hashes) != len(set(content_hashes)):
            raise ValueError("identical content cannot be relabeled as independent windows")
        for index, left in enumerate(self.windows):
            for right in self.windows[index + 1 :]:
                overlaps = (
                    left.observed_start <= right.observed_end
                    and right.observed_start <= left.observed_end
                )
                if overlaps and left.overlap_cluster_id != right.overlap_cluster_id:
                    raise ValueError("overlapping windows must share an overlap cluster")
        return self

    @property
    def canonical_root(self) -> str:
        return self.sha256()


class SplitMemberV1(StrictFrozenModel):
    window_id: Identifier
    family_id: Identifier
    content_unit_id: Identifier
    selected_rows_sha256: Sha256


class SplitPartitionV1(StrictFrozenModel):
    split_id: Identifier
    members: tuple[SplitMemberV1, ...] = Field(min_length=1)
    selected_rows_sha256: Sha256

    @model_validator(mode="after")
    def validate_partition(self) -> Self:
        window_ids = tuple(member.window_id for member in self.members)
        if window_ids != tuple(sorted(set(window_ids))):
            raise ValueError("split members must be sorted by unique window_id")
        expected = canonical_sha256(
            tuple(member.selected_rows_sha256 for member in self.members)
        )
        if self.selected_rows_sha256 != expected:
            raise ValueError("split selected-row root does not match its members")
        return self


class SplitRegistryV1(StrictFrozenModel):
    schema_version: Literal[1] = 1
    registry_id: Identifier
    dataset_manifest_sha256: Sha256
    splits: tuple[SplitPartitionV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_splits(self) -> Self:
        split_ids = tuple(split.split_id for split in self.splits)
        if split_ids != tuple(sorted(set(split_ids))):
            raise ValueError("splits must be sorted by unique split_id")
        family_owner: dict[str, str] = {}
        content_owner: dict[str, str] = {}
        window_ids: set[str] = set()
        for split in self.splits:
            for member in split.members:
                if member.window_id in window_ids:
                    raise ValueError("a window cannot appear in multiple splits")
                window_ids.add(member.window_id)
                for label, value, owners in (
                    ("family", member.family_id, family_owner),
                    ("content unit", member.content_unit_id, content_owner),
                ):
                    owner = owners.setdefault(value, split.split_id)
                    if owner != split.split_id:
                        raise ValueError(f"{label} {value!r} leaks across splits")
        return self

    @property
    def canonical_root(self) -> str:
        return self.sha256()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_dataset_manifest(
    path: Path,
    *,
    expected_sha256: str | None = None,
    dataset_dir: Path | None = None,
) -> DatasetManifestV3:
    """Load and authenticate one dataset manifest and, optionally, its payload."""

    manifest = DatasetManifestV3.model_validate_json(path.read_text(encoding="utf-8"))
    if expected_sha256 is not None and manifest.sha256() != expected_sha256:
        raise ValueError("dataset control manifest hash does not match the registry")
    if dataset_dir is not None:
        actual: list[DatasetFileV1] = []
        for payload_path in sorted(dataset_dir.rglob("*")):
            if payload_path.is_symlink():
                raise ValueError("dataset payload must not contain symbolic links")
            if payload_path.is_file() and not payload_path.name.startswith("."):
                actual.append(
                    DatasetFileV1(
                        path=payload_path.relative_to(dataset_dir).as_posix(),
                        bytes=payload_path.stat().st_size,
                        file_sha256=_hash_file(payload_path),
                    )
                )
        if tuple(actual) != manifest.payload_files:
            raise ValueError("dataset payload differs from the authenticated inventory")
    return manifest


def load_split_registry(
    path: Path,
    *,
    expected_sha256: str | None = None,
    dataset_manifest: DatasetManifestV3 | None = None,
) -> SplitRegistryV1:
    """Load and authenticate a split registry against its dataset manifest."""

    registry = SplitRegistryV1.model_validate_json(path.read_text(encoding="utf-8"))
    if expected_sha256 is not None and registry.sha256() != expected_sha256:
        raise ValueError("split registry hash does not match the dataset registry")
    if dataset_manifest is None:
        return registry
    if registry.dataset_manifest_sha256 != dataset_manifest.sha256():
        raise ValueError("split registry is bound to a different dataset manifest")
    expected_windows = {window.window_id: window for window in dataset_manifest.windows}
    observed_windows: set[str] = set()
    for split in registry.splits:
        for member in split.members:
            window = expected_windows.get(member.window_id)
            if window is None:
                raise ValueError("split registry references an unknown dataset window")
            expected = (
                window.family_id,
                window.content_unit_id,
                window.selected_rows_sha256,
            )
            observed = (
                member.family_id,
                member.content_unit_id,
                member.selected_rows_sha256,
            )
            if observed != expected:
                raise ValueError("split member does not match its authenticated dataset window")
            observed_windows.add(member.window_id)
    if observed_windows != set(expected_windows):
        raise ValueError("split registry must assign every authenticated dataset window")
    return registry


__all__ = [
    "DatasetFileV1",
    "DatasetManifestV3",
    "DatasetWindowV1",
    "RawAcquisitionReceiptV1",
    "RightsRecordV1",
    "SplitMemberV1",
    "SplitPartitionV1",
    "SplitRegistryV1",
    "TransformationStepV1",
    "load_dataset_manifest",
    "load_split_registry",
]
