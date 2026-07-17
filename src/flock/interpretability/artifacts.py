"""Hashed artifact contract for activation and attribution outputs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class MechanismManifest:
    checkpoint_hash: str
    prompt_hashes: tuple[str, ...]
    intervention: str
    layers: tuple[int, ...]
    tensor_sha256: str
    shape: tuple[int, ...]


def write_mechanism_artifact(
    output_dir: Path,
    tensor: np.ndarray,
    checkpoint_hash: str,
    prompts: list[str],
    intervention: str,
    layers: tuple[int, ...],
) -> MechanismManifest:
    output_dir.mkdir(parents=True, exist_ok=True)
    tensor_path = output_dir / "activations.npy"
    np.save(tensor_path, tensor, allow_pickle=False)
    digest = hashlib.sha256(tensor_path.read_bytes()).hexdigest()
    manifest = MechanismManifest(
        checkpoint_hash=checkpoint_hash,
        prompt_hashes=tuple(hashlib.sha256(prompt.encode()).hexdigest() for prompt in prompts),
        intervention=intervention,
        layers=layers,
        tensor_sha256=digest,
        shape=tensor.shape,
    )
    (output_dir / "manifest.json").write_text(json.dumps(asdict(manifest), indent=2) + "\n")
    return manifest
