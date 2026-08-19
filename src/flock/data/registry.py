"""Versioned dataset registry backed by datasets/manifests.json (checked in)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from flock.control.data import load_dataset_manifest, load_split_registry

DATASETS_DIR = Path("datasets")


@dataclass
class DatasetEntry:
    name: str
    version: int
    path: str  # relative to repo root
    sha256: str  # canonical hash of the complete dataset directory
    rows: int
    source: str  # builder name
    created_at: str
    params: dict
    files: dict[str, str] | None = None
    control_manifest_path: str | None = None
    control_manifest_sha256: str | None = None
    split_registry_path: str | None = None
    split_registry_sha256: str | None = None

    @property
    def control_ready(self) -> bool:
        """Whether the registry binds both authenticated control records."""

        return all(
            value is not None
            for value in (
                self.control_manifest_path,
                self.control_manifest_sha256,
                self.split_registry_path,
                self.split_registry_sha256,
            )
        )

    @property
    def legacy_local_only(self) -> bool:
        """Legacy synthetic entries remain usable only by local/mock workflows."""

        return self.source == "synthetic" and not self.control_ready


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dataset_bundle_files(dataset_dir: Path) -> dict[str, str]:
    """Hash every regular payload file in a stable relative-path order."""
    return {
        path.relative_to(dataset_dir).as_posix(): _hash_file(path)
        for path in sorted(dataset_dir.rglob("*"))
        if path.is_file() and not path.name.startswith(".")
    }


def dataset_bundle_hash(dataset_dir: Path) -> str:
    files = dataset_bundle_files(dataset_dir)
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class Registry:
    def __init__(self, root: Path = DATASETS_DIR):
        self.root = root
        self.manifest_path = root / "manifests.json"

    def _load(self) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        with open(self.manifest_path) as f:
            return json.load(f)

    def _save(self, entries: list[dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_suffix(".json.tmp")
        with open(temporary, "w") as f:
            json.dump(entries, f, indent=2)
        temporary.replace(self.manifest_path)

    def entries(self) -> list[DatasetEntry]:
        return [DatasetEntry(**e) for e in self._load()]

    def entry_dir(self, entry: DatasetEntry) -> Path:
        """Resolve the payload directory for one exact registry version."""
        path = Path(entry.path)
        return path if path.is_absolute() else self.root.parent / path

    def _control_record_path(self, value: str) -> Path:
        path = Path(value)
        if any(part == ".." for part in path.parts):
            raise ValueError("control record paths must not contain traversal")
        return path if path.is_absolute() else self.root.parent / path

    def get(self, name: str) -> DatasetEntry:
        entries = self.entries()
        matches = [entry for entry in entries if entry.name == name]
        if not matches:
            raise KeyError(
                f"dataset '{name}' not in registry; run `flock data build ...` (have: "
                f"{sorted({entry.name for entry in entries}) or 'none'})"
            )
        return max(matches, key=lambda e: e.version)

    def register(
        self,
        name: str,
        source: str,
        dataset_dir: Path,
        params: dict,
        primary_file: str = "bars.parquet",
        control_manifest_path: str | None = None,
        control_manifest_sha256: str | None = None,
        split_registry_path: str | None = None,
        split_registry_sha256: str | None = None,
    ) -> DatasetEntry:
        entries = self._load()
        version = 1 + max((e["version"] for e in entries if e["name"] == name), default=0)
        bars_path = dataset_dir / primary_file
        files = dataset_bundle_files(dataset_dir)
        entry = DatasetEntry(
            name=name,
            version=version,
            path=str(dataset_dir),
            sha256=dataset_bundle_hash(dataset_dir),
            rows=len(pd.read_parquet(bars_path)),
            source=source,
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
            params=params,
            files=files,
            control_manifest_path=control_manifest_path,
            control_manifest_sha256=control_manifest_sha256,
            split_registry_path=split_registry_path,
            split_registry_sha256=split_registry_sha256,
        )
        entries.append(asdict(entry))
        self._save(entries)
        return entry

    def verify(self, entry: DatasetEntry) -> list[str]:
        dataset_dir = self.entry_dir(entry)
        if not dataset_dir.exists():
            return [f"dataset payload is missing: {dataset_dir}"]
        if entry.files is None:
            return ["legacy manifest hashes only the primary file; rebuild dataset"]
        actual_files = dataset_bundle_files(dataset_dir)
        errors = []
        if actual_files != entry.files:
            errors.append("dataset file inventory or content hashes changed")
        if dataset_bundle_hash(dataset_dir) != entry.sha256:
            errors.append("dataset bundle hash changed")

        control_values = (
            entry.control_manifest_path,
            entry.control_manifest_sha256,
            entry.split_registry_path,
            entry.split_registry_sha256,
        )
        if not any(control_values):
            if entry.source != "synthetic":
                errors.append(
                    "real dataset is missing authenticated data and split control records"
                )
            return errors
        if not entry.control_ready:
            errors.append("dataset control record references are incomplete")
            return errors

        assert entry.control_manifest_path is not None
        assert entry.control_manifest_sha256 is not None
        assert entry.split_registry_path is not None
        assert entry.split_registry_sha256 is not None
        try:
            manifest = load_dataset_manifest(
                self._control_record_path(entry.control_manifest_path),
                expected_sha256=entry.control_manifest_sha256,
                dataset_dir=dataset_dir,
            )
        except (OSError, ValueError):
            errors.append("dataset control manifest failed authentication")
            return errors
        expected_source_class = "synthetic" if entry.source == "synthetic" else "real"
        if (
            manifest.dataset_name != entry.name
            or manifest.dataset_version != entry.version
            or manifest.source_class != expected_source_class
        ):
            errors.append("dataset control manifest identity does not match the registry")
        if manifest.dataset_bundle_sha256 != entry.sha256:
            errors.append("dataset control manifest binds a different bundle root")
        try:
            load_split_registry(
                self._control_record_path(entry.split_registry_path),
                expected_sha256=entry.split_registry_sha256,
                dataset_manifest=manifest,
            )
        except (OSError, ValueError):
            errors.append("split registry failed authentication")
        return errors

    def dataset_dir(self, name: str) -> Path:
        return self.entry_dir(self.get(name))
