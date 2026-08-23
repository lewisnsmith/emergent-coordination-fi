from __future__ import annotations

from pathlib import Path

import pytest

from flock.artifacts import (
    atomic_write,
    canonical_json_bytes,
    safe_relative_path,
    verify_checksums,
    write_checksums,
)


def test_canonical_json_is_stable() -> None:
    assert canonical_json_bytes({"b": 2, "a": [1, "é"]}) == b'{"a":[1,"\xc3\xa9"],"b":2}\n'


@pytest.mark.parametrize(
    "value",
    ["", "/absolute", "../escape", "a/../b", "./a", "a\nb", "a\rb", "a\0b"],
)
def test_safe_relative_path_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ValueError):
        safe_relative_path(value)


def test_atomic_write_replaces_the_target(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "artifact.bin"
    atomic_write(target, b"first")
    atomic_write(target, b"second")
    assert target.read_bytes() == b"second"
    assert list(target.parent.iterdir()) == [target]


def test_checksums_detect_tampering(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("original\n", encoding="utf-8")
    manifest = tmp_path / "checksums.sha256"
    write_checksums(tmp_path, ("artifact.txt",), manifest)
    assert verify_checksums(tmp_path, manifest) == ()

    artifact.write_text("changed\n", encoding="utf-8")
    assert verify_checksums(tmp_path, manifest) == ("hash mismatch: artifact.txt",)


def test_checksums_reject_symlinks(tmp_path: Path) -> None:
    release = tmp_path / "release"
    release.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = release / "linked.txt"
    link.symlink_to(outside)

    manifest = release / "checksums.sha256"
    with pytest.raises(ValueError, match="symlink"):
        write_checksums(release, ("linked.txt",), manifest)

    manifest.write_text(f"{'0' * 64}  linked.txt\n", encoding="utf-8")
    assert verify_checksums(release, manifest) == ("unsafe path: linked.txt",)
