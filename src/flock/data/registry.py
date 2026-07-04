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
    sha256: str  # hash of bars.parquet
    rows: int
    source: str  # builder name
    created_at: str
    params: dict


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
        with open(self.manifest_path, "w") as f:
            json.dump(entries, f, indent=2)

    def entries(self) -> list[DatasetEntry]:
        return [DatasetEntry(**e) for e in self._load()]

    def get(self, name: str) -> DatasetEntry:
        matches = [e for e in self.entries() if e.name == name]
        if not matches:
            raise KeyError(
                f"dataset '{name}' not in registry; run `flock data build ...` (have: "
                f"{[e.name for e in self.entries()] or 'none'})"
            )
        return max(matches, key=lambda e: e.version)

    def dataset_dir(self, name: str) -> Path:
        return Path(self.get(name).path)

    def register(self, name: str, source: str, dataset_dir: Path, params: dict) -> DatasetEntry:
        entries = self._load()
        version = 1 + max((e["version"] for e in entries if e["name"] == name), default=0)
        bars_path = dataset_dir / "bars.parquet"
        entry = DatasetEntry(
            name=name,
            version=version,
            path=str(dataset_dir),
            sha256=_hash_file(bars_path),
            rows=len(pd.read_parquet(bars_path)),
            source=source,
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
            params=params,
        )
        entries.append(asdict(entry))
        self._save(entries)
        return entry
