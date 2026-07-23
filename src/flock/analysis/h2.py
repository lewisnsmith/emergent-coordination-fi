"""Fail-closed H2 external-reference artifact generation."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from flock.analysis.coordination import (
    activity_match_report,
    harmonize_13f_holdings_changes,
    holdings_change_counts,
    lsv_cell_statistics,
    lsv_herding,
    sias_decomposition_from_panel,
)


@dataclass(frozen=True)
class H2ArtifactResult:
    output_dir: Path
    source_rows: int
    activity_rows: int
    lsv_cells: int
    artifact_hash: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _frame_hashes(root: Path, names: tuple[str, ...]) -> dict[str, str]:
    return {name: _sha256(root / name) for name in names}


def build_h2_artifacts(
    holdings_path: Path,
    comparison_counts_path: Path,
    output_dir: Path,
    *,
    min_traders: int = 3,
    activity_rate_tolerance: float = 0.0,
) -> H2ArtifactResult:
    """Build auditable H2 artifacts from realized holdings changes.

    The comparison input must already represent realized simulated holdings
    changes in the count schema used by ``activity_match_report``. Intended
    orders are rejected rather than silently compared with quarterly 13F
    position changes.
    """
    if output_dir.exists():
        raise ValueError(f"H2 output directory already exists: {output_dir}")
    if min_traders < 2:
        raise ValueError("H2 min_traders must be at least two")
    for label, path in (
        ("13F holdings", holdings_path),
        ("comparison counts", comparison_counts_path),
    ):
        if not path.is_file():
            raise ValueError(f"{label} input does not exist: {path}")

    holdings = pd.read_parquet(holdings_path)
    comparison = pd.read_parquet(comparison_counts_path)
    harmonized = harmonize_13f_holdings_changes(holdings)
    counts = holdings_change_counts(harmonized)
    if counts.empty:
        raise ValueError("H2 harmonization produced no realized holdings-change cells")
    cells = lsv_cell_statistics(counts, min_traders=min_traders)
    if cells.empty:
        raise ValueError("H2 has no LSV cells at the configured minimum trader count")
    sias = sias_decomposition_from_panel(
        harmonized.activity, min_traders=min_traders
    )
    if sias.period_pairs < 1 or not all(
        np.isfinite(value)
        for value in (sias.full, sias.following_own, sias.following_others)
    ):
        raise ValueError("H2 has no finite Sias decomposition across consecutive periods")
    match = activity_match_report(
        counts,
        comparison,
        min_traders=min_traders,
        activity_rate_tolerance=activity_rate_tolerance,
        require_same_basis=True,
    )
    if match.empty or not bool(cast(pd.Series, match["matched"]).all()):
        reasons = (
            cast(pd.Series, match["reason"]).value_counts().sort_index().to_dict()
            if not match.empty
            else {"empty_match_report": 1}
        )
        raise ValueError(f"H2 activity matching failed: {reasons}")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent)
    )
    artifacts = (
        "activity.parquet",
        "period-coverage.parquet",
        "unmatched.parquet",
        "counts.parquet",
        "lsv-cells.parquet",
        "activity-match.parquet",
        "metrics.json",
    )
    try:
        harmonized.activity.to_parquet(temporary / artifacts[0], index=False)
        harmonized.period_coverage.to_parquet(temporary / artifacts[1], index=False)
        harmonized.unmatched.to_parquet(temporary / artifacts[2], index=False)
        counts.to_parquet(temporary / artifacts[3], index=False)
        cells.to_parquet(temporary / artifacts[4], index=False)
        match.to_parquet(temporary / artifacts[5], index=False)
        _write_json(
            temporary / artifacts[6],
            {
                "lsv": lsv_herding(counts, min_traders=min_traders),
                "sias": {
                    "full": sias.full,
                    "following_own": sias.following_own,
                    "following_others": sias.following_others,
                    "period_pairs": sias.period_pairs,
                },
                "min_traders": min_traders,
                "activity_rate_tolerance": activity_rate_tolerance,
                "decision_basis": "realized_holdings_change",
                "claim_boundary": "descriptive external anchor; not causal",
            },
        )
        artifact_hashes = _frame_hashes(temporary, artifacts)
        manifest_payload = {
            "schema_version": 1,
            "status": "complete",
            "evidence_kind": "external_reference",
            "paper_eligible": False,
            "inputs": {
                "holdings13f": {
                    "path": str(holdings_path.resolve()),
                    "sha256": _sha256(holdings_path),
                    "rows": len(holdings),
                },
                "comparison_counts": {
                    "path": str(comparison_counts_path.resolve()),
                    "sha256": _sha256(comparison_counts_path),
                    "rows": len(comparison),
                },
            },
            "outputs": artifact_hashes,
            "activity_gate_passed": True,
            "unmatched_rows": len(harmonized.unmatched),
        }
        aggregation_hash = hashlib.sha256(
            json.dumps(
                manifest_payload, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        manifest_payload["artifact_hash"] = aggregation_hash
        _write_json(temporary / "h2-manifest.json", manifest_payload)
        temporary.replace(output_dir)
    except Exception:
        shutil.rmtree(temporary)
        raise

    return H2ArtifactResult(
        output_dir=output_dir.resolve(),
        source_rows=len(holdings),
        activity_rows=len(harmonized.activity),
        lsv_cells=len(cells),
        artifact_hash=aggregation_hash,
    )
