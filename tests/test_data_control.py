from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from flock.control.data import (
    DatasetFileV1,
    DatasetManifestV3,
    DatasetWindowV1,
    RawAcquisitionReceiptV1,
    RightsRecordV1,
    SplitMemberV1,
    SplitPartitionV1,
    SplitRegistryV1,
    TransformationStepV1,
    load_dataset_manifest,
    load_split_registry,
)
from flock.control.models import canonical_sha256
from flock.data.registry import (
    DatasetEntry,
    Registry,
    dataset_bundle_files,
    dataset_bundle_hash,
)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _payload(tmp_path: Path) -> Path:
    dataset_dir = tmp_path / "payload"
    dataset_dir.mkdir()
    (dataset_dir / "bars.csv").write_bytes(b"ts,symbol,close\n2026-01-01,A,10\n")
    (dataset_dir / "meta.json").write_bytes(b'{"source":"fixture"}\n')
    return dataset_dir


def _window(
    window_id: str,
    family_id: str,
    start_day: int,
    end_day: int,
    cluster: str,
) -> DatasetWindowV1:
    content = _sha(f"rows:{window_id}".encode())
    return DatasetWindowV1(
        window_id=window_id,
        family_id=family_id,
        requested_start=datetime(2026, 1, start_day, tzinfo=UTC),
        requested_end=datetime(2026, 1, end_day, tzinfo=UTC),
        observed_start=datetime(2026, 1, start_day, tzinfo=UTC),
        observed_end=datetime(2026, 1, end_day, tzinfo=UTC),
        selected_rows=end_day - start_day + 1,
        selected_rows_sha256=content,
        content_sha256=content,
        content_unit_id=f"unit:{content}",
        overlap_cluster_id=cluster,
    )


def _manifest(dataset_dir: Path) -> DatasetManifestV3:
    file_hashes = dataset_bundle_files(dataset_dir)
    payload_files = tuple(
        DatasetFileV1(
            path=relative,
            bytes=(dataset_dir / relative).stat().st_size,
            file_sha256=digest,
        )
        for relative, digest in sorted(file_hashes.items())
    )
    raw_sha = _sha(b"immutable raw fixture")
    bundle_sha = dataset_bundle_hash(dataset_dir)
    return DatasetManifestV3(
        dataset_name="market-fixture",
        dataset_version=1,
        source_class="real",
        raw_acquisitions=(
            RawAcquisitionReceiptV1(
                artifact_id="raw-market",
                uri="https://data.example.test/market.csv",
                source_version="snapshot-2026-01-07",
                retrieved_at=datetime(2026, 1, 7, 12, tzinfo=UTC),
                raw_bytes=21,
                raw_sha256=raw_sha,
            ),
        ),
        rights=RightsRecordV1(
            license_id="fixture-research-license",
            terms_uri="https://data.example.test/terms",
            terms_sha256=_sha(b"fixture terms"),
            verified_at=datetime(2026, 1, 7, 12, tzinfo=UTC),
            permitted_uses=("offline-research",),
        ),
        privacy_class="restricted",
        release_class="metadata-only",
        timestamp_semantics="UTC event time available at the recorded timestamp",
        transformation_dag=(
            TransformationStepV1(
                step_id="normalize",
                code_sha256=_sha(b"normalizer source"),
                parameters_sha256=canonical_sha256({"timezone": "UTC"}),
                input_sha256s=(raw_sha,),
                output_sha256=bundle_sha,
            ),
        ),
        payload_files=payload_files,
        dataset_bundle_sha256=bundle_sha,
        windows=(
            _window("window-a", "family-a", 1, 2, "overlap-a"),
            _window("window-b", "family-a", 2, 3, "overlap-a"),
            _window("window-c", "family-b", 5, 6, "overlap-c"),
        ),
    )


def _member(window: DatasetWindowV1) -> SplitMemberV1:
    return SplitMemberV1(
        window_id=window.window_id,
        family_id=window.family_id,
        content_unit_id=window.content_unit_id,
        selected_rows_sha256=window.selected_rows_sha256,
    )


def _partition(split_id: str, members: tuple[SplitMemberV1, ...]) -> SplitPartitionV1:
    return SplitPartitionV1(
        split_id=split_id,
        members=members,
        selected_rows_sha256=canonical_sha256(
            tuple(member.selected_rows_sha256 for member in members)
        ),
    )


def _splits(manifest: DatasetManifestV3) -> SplitRegistryV1:
    windows = {window.window_id: window for window in manifest.windows}
    return SplitRegistryV1(
        registry_id="market-fixture-splits",
        dataset_manifest_sha256=manifest.sha256(),
        splits=(
            _partition("confirm", (_member(windows["window-c"]),)),
            _partition(
                "train",
                (_member(windows["window-a"]), _member(windows["window-b"])),
            ),
        ),
    )


def _write_control_records(
    tmp_path: Path,
    manifest: DatasetManifestV3,
    splits: SplitRegistryV1,
) -> tuple[Path, Path]:
    manifest_path = tmp_path / "dataset-control.json"
    split_path = tmp_path / "split-control.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    split_path.write_text(splits.model_dump_json(indent=2), encoding="utf-8")
    return manifest_path, split_path


def _entry(
    dataset_dir: Path,
    manifest_path: Path,
    manifest: DatasetManifestV3,
    split_path: Path,
    splits: SplitRegistryV1,
) -> DatasetEntry:
    return DatasetEntry(
        name="market-fixture",
        version=1,
        path=str(dataset_dir),
        sha256=dataset_bundle_hash(dataset_dir),
        rows=2,
        source="fixture-real-builder",
        created_at="2026-01-07T12:00:00+00:00",
        params={},
        files=dataset_bundle_files(dataset_dir),
        control_manifest_path=str(manifest_path),
        control_manifest_sha256=manifest.sha256(),
        split_registry_path=str(split_path),
        split_registry_sha256=splits.sha256(),
    )


def test_control_records_authenticate_payload_and_registry(tmp_path: Path) -> None:
    dataset_dir = _payload(tmp_path)
    manifest = _manifest(dataset_dir)
    splits = _splits(manifest)
    manifest_path, split_path = _write_control_records(tmp_path, manifest, splits)

    loaded = load_dataset_manifest(
        manifest_path,
        expected_sha256=manifest.canonical_root,
        dataset_dir=dataset_dir,
    )
    loaded_splits = load_split_registry(
        split_path,
        expected_sha256=splits.canonical_root,
        dataset_manifest=loaded,
    )
    assert loaded_splits.canonical_root == splits.sha256()
    assert Registry(root=tmp_path / "registry").verify(
        _entry(dataset_dir, manifest_path, manifest, split_path, splits)
    ) == []


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    [
        ("raw_acquisitions", "source_version", "changed-upstream-version"),
        ("rights", "license_id", "changed-rights-record"),
    ],
)
def test_registry_detects_raw_or_rights_drift(
    tmp_path: Path,
    section: str,
    field: str,
    replacement: str,
) -> None:
    dataset_dir = _payload(tmp_path)
    manifest = _manifest(dataset_dir)
    splits = _splits(manifest)
    manifest_path, split_path = _write_control_records(tmp_path, manifest, splits)
    entry = _entry(dataset_dir, manifest_path, manifest, split_path, splits)
    payload = manifest.model_dump(mode="json")
    target = payload[section][0] if section == "raw_acquisitions" else payload[section]
    target[field] = replacement
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    assert "dataset control manifest failed authentication" in Registry(
        root=tmp_path / "registry"
    ).verify(entry)


def test_manifest_rejects_overlapping_windows_in_separate_clusters(
    tmp_path: Path,
) -> None:
    manifest = _manifest(_payload(tmp_path))
    payload = manifest.model_dump(mode="json")
    payload["windows"][1]["overlap_cluster_id"] = "fake-independent-cluster"

    with pytest.raises(ValidationError, match="overlapping windows"):
        DatasetManifestV3.model_validate_json(json.dumps(payload))


def test_manifest_rejects_duplicate_content_relabeling(tmp_path: Path) -> None:
    manifest = _manifest(_payload(tmp_path))
    payload = manifest.model_dump(mode="json")
    content = payload["windows"][0]["content_sha256"]
    payload["windows"][1]["selected_rows_sha256"] = content
    payload["windows"][1]["content_sha256"] = content
    payload["windows"][1]["content_unit_id"] = f"unit:{content}"

    with pytest.raises(ValidationError, match="identical content"):
        DatasetManifestV3.model_validate_json(json.dumps(payload))


def test_manifest_rejects_rows_outside_requested_window(tmp_path: Path) -> None:
    manifest = _manifest(_payload(tmp_path))
    payload = manifest.model_dump(mode="json")
    payload["windows"][0]["observed_start"] = "2025-12-31T00:00:00Z"

    with pytest.raises(ValidationError, match="outside the requested window"):
        DatasetManifestV3.model_validate_json(json.dumps(payload))


def test_split_registry_rejects_family_leakage(tmp_path: Path) -> None:
    manifest = _manifest(_payload(tmp_path))
    windows = {window.window_id: window for window in manifest.windows}
    leaked = _member(windows["window-b"])
    payload = {
        "schema_version": 1,
        "registry_id": "leaked-splits",
        "dataset_manifest_sha256": manifest.sha256(),
        "splits": [
            _partition("confirm", (leaked,)).model_dump(mode="json"),
            _partition("train", (_member(windows["window-a"]),)).model_dump(
                mode="json"
            ),
        ],
    }

    with pytest.raises(ValidationError, match="family .* leaks across splits"):
        SplitRegistryV1.model_validate_json(json.dumps(payload))


def test_split_loader_rejects_selected_row_hash_tamper(tmp_path: Path) -> None:
    dataset_dir = _payload(tmp_path)
    manifest = _manifest(dataset_dir)
    splits = _splits(manifest)
    payload = splits.model_dump(mode="json")
    payload["splits"][0]["members"][0]["selected_rows_sha256"] = _sha(b"other rows")
    payload["splits"][0]["selected_rows_sha256"] = canonical_sha256(
        tuple(member["selected_rows_sha256"] for member in payload["splits"][0]["members"])
    )
    changed = SplitRegistryV1.model_validate_json(json.dumps(payload))
    _, split_path = _write_control_records(tmp_path, manifest, changed)

    with pytest.raises(ValueError, match="split member"):
        load_split_registry(split_path, dataset_manifest=manifest)


def test_registry_rejects_control_path_and_hash_tamper(tmp_path: Path) -> None:
    dataset_dir = _payload(tmp_path)
    manifest = _manifest(dataset_dir)
    splits = _splits(manifest)
    manifest_path, split_path = _write_control_records(tmp_path, manifest, splits)
    entry = _entry(dataset_dir, manifest_path, manifest, split_path, splits)
    registry = Registry(root=tmp_path / "registry")

    wrong_hash = replace(entry, control_manifest_sha256="f" * 64)
    assert "dataset control manifest failed authentication" in registry.verify(wrong_hash)
    traversed = replace(entry, control_manifest_path="../outside.json")
    assert "dataset control manifest failed authentication" in registry.verify(traversed)
