"""Tiered, uncertainty-labeled data-product export for H11."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, cast

import pandas as pd

EvidenceTier = Literal[
    "simulation_truth",
    "ai_like_signature",
    "verified_ai_exposure",
    "causally_verified_ai_event",
]
TIERS: tuple[EvidenceTier, ...] = (
    "simulation_truth",
    "ai_like_signature",
    "verified_ai_exposure",
    "causally_verified_ai_event",
)


def validate_product(frame: pd.DataFrame) -> list[str]:
    required = {"record_id", "evidence_tier", "confidence", "source_hash"}
    errors = []
    missing = required - set(frame.columns)
    if missing:
        return [f"missing columns: {sorted(missing)}"]
    record_ids = cast(pd.Series, frame["record_id"])
    evidence_tiers = cast(pd.Series, frame["evidence_tier"])
    confidence = cast(pd.Series, frame["confidence"])
    source_hashes = cast(pd.Series, frame["source_hash"])
    if bool(record_ids.duplicated().to_numpy().any()):
        errors.append("duplicate record_id")
    if not bool(evidence_tiers.isin(TIERS).to_numpy().all()):
        errors.append("unknown evidence tier")
    if not bool(confidence.between(0, 1).to_numpy().all()):
        errors.append("confidence outside [0,1]")
    if bool(source_hashes.isna().to_numpy().any()) or bool(
        (source_hashes == "").to_numpy().any()
    ):
        errors.append("missing source hash")
    return errors


def export_product(frame: pd.DataFrame, output_dir: Path, product_id: str) -> Path:
    errors = validate_product(frame)
    if errors:
        raise ValueError("; ".join(errors))
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "records.parquet"
    frame.to_parquet(data_path, index=False)
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    manifest = {
        "product_id": product_id,
        "rows": len(frame),
        "sha256": digest,
        "tiers": frame["evidence_tier"].value_counts().sort_index().to_dict(),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return output_dir
