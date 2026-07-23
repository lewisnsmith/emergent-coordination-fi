import json
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from flock.analysis.coordination import (
    harmonize_13f_holdings_changes,
    holdings_change_counts,
)
from flock.analysis.h2 import build_h2_artifacts
from flock.cli import app


def _holdings() -> pd.DataFrame:
    directions = {
        "2024-06-30": {
            "AAA": [1, 1, 1, -1],
            "BBB": [1, 1, -1, -1],
            "CCC": [1, -1, -1, -1],
        },
        "2024-09-30": {
            "AAA": [1, 1, -1, -1],
            "BBB": [1, -1, -1, -1],
            "CCC": [1, 1, 1, -1],
        },
    }
    levels = {
        (manager, symbol): 100.0
        for manager in range(4)
        for symbol in directions["2024-06-30"]
    }
    rows = []
    for period in ("2024-03-31", "2024-06-30", "2024-09-30"):
        if period in directions:
            for symbol, changes in directions[period].items():
                for manager, direction in enumerate(changes):
                    levels[(manager, symbol)] += 10.0 * direction
        for (manager, symbol), shares in sorted(levels.items()):
            rows.append(
                {
                    "manager": f"m{manager}",
                    "period": period,
                    "cusip": symbol,
                    "shares": shares,
                    "shares_type": "SH",
                    "put_call": "",
                    "accession": f"m{manager}-{period}",
                    "filing_date": period,
                    "acceptance_datetime": f"{period}T12:00:00Z",
                    "source_url": f"https://example.test/m{manager}/{period}",
                    "value_usd": shares,
                }
            )
    return pd.DataFrame(rows)


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    holdings = _holdings()
    holdings_path = tmp_path / "holdings13f.parquet"
    holdings.to_parquet(holdings_path, index=False)
    comparison = holdings_change_counts(harmonize_13f_holdings_changes(holdings))
    comparison_path = tmp_path / "simulated-realized-counts.parquet"
    comparison.to_parquet(comparison_path, index=False)
    return holdings_path, comparison_path


def test_h2_artifacts_are_hashed_activity_matched_and_cli_accessible(tmp_path):
    holdings, comparison = _inputs(tmp_path)
    output = tmp_path / "h2"

    result = build_h2_artifacts(holdings, comparison, output)

    assert result.activity_rows == 24
    assert result.lsv_cells == 6
    manifest = json.loads((output / "h2-manifest.json").read_text())
    assert manifest["activity_gate_passed"] is True
    assert manifest["paper_eligible"] is False
    assert manifest["artifact_hash"] == result.artifact_hash
    metrics = json.loads((output / "metrics.json").read_text())
    assert metrics["sias"]["period_pairs"] == 1
    assert metrics["claim_boundary"] == "descriptive external anchor; not causal"

    cli_output = tmp_path / "h2-cli"
    invoked = CliRunner().invoke(
        app,
        [
            "harmonize-h2",
            str(holdings),
            str(comparison),
            "--output",
            str(cli_output),
        ],
    )
    assert invoked.exit_code == 0, invoked.output
    assert "H2 artifacts ->" in invoked.output


def test_h2_artifacts_reject_intended_order_comparison(tmp_path):
    holdings, comparison_path = _inputs(tmp_path)
    comparison = pd.read_parquet(comparison_path)
    comparison["decision_basis"] = "intended_clipped_order"
    comparison.to_parquet(comparison_path, index=False)

    with pytest.raises(ValueError, match="activity matching failed"):
        build_h2_artifacts(holdings, comparison_path, tmp_path / "rejected")
    assert not (tmp_path / "rejected").exists()
