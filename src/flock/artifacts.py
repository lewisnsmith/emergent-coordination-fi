"""Small deterministic primitives shared by published studies."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically for hashing and manifests."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    """Hash a file without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(value: str) -> PurePosixPath:
    """Return a normalized release path or reject traversal and ambiguity."""
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe relative path: {value!r}")
    if path.as_posix() != value or any(not part for part in path.parts):
        raise ValueError(f"non-canonical relative path: {value!r}")
    return path


def atomic_write(path: Path, payload: bytes) -> None:
    """Replace a file atomically after writing and syncing a sibling temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_checksums(root: Path, relative_paths: tuple[str, ...], output: Path) -> None:
    """Write a deterministic SHA-256 manifest for files below ``root``."""
    lines = []
    for value in sorted(relative_paths):
        relative = safe_relative_path(value)
        candidate = root.joinpath(*relative.parts)
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        lines.append(f"{sha256_file(candidate)}  {relative.as_posix()}\n")
    atomic_write(output, "".join(lines).encode("utf-8"))


def verify_checksums(root: Path, manifest: Path) -> tuple[str, ...]:
    """Return deterministic validation errors for a SHA-256 manifest."""
    errors: list[str] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        try:
            expected, value = raw_line.split("  ", 1)
            relative = safe_relative_path(value)
        except ValueError:
            errors.append(f"line {line_number}: malformed checksum entry")
            continue
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
            errors.append(f"line {line_number}: invalid sha256")
            continue
        normalized = relative.as_posix()
        if normalized in seen:
            errors.append(f"line {line_number}: duplicate path {normalized}")
            continue
        seen.add(normalized)
        candidate = root.joinpath(*relative.parts)
        if not candidate.is_file():
            errors.append(f"missing: {normalized}")
        elif sha256_file(candidate) != expected:
            errors.append(f"hash mismatch: {normalized}")
    return tuple(errors)
