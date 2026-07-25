"""Versioned dataset registry backed by datasets/manifests.json (checked in)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

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
        return errors

    def dataset_dir(self, name: str) -> Path:
        return self.entry_dir(self.get(name))
