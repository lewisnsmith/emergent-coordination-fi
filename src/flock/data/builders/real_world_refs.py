"""Real-world reference panels (H2 external anchor): 13F institutional holdings.

Fetches recent 13F-HR information tables from SEC EDGAR for a panel of large
managers and writes a holdings panel (manager, period, cusip, value_usd).
EDGAR requires a descriptive User-Agent: set EDGAR_USER_AGENT in .env.

The output is a *reference* dataset consumed by the analysis layer (portfolio
overlap / LSV among real managers), not by the replay engine.
"""

from __future__ import annotations

import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import TypedDict

import httpx
import pandas as pd

from flock.data.registry import DATASETS_DIR, DatasetEntry, Registry

# name -> CIK (zero-padded later). A modest, well-known panel; extend freely.
MANAGERS = {
    "berkshire": 1067983,
    "bridgewater": 1350694,
    "renaissance": 1037389,
    "aqr": 1167557,
    "two-sigma": 1179392,
    "citadel": 1423053,
    "millennium": 1273087,
    "de-shaw": 1009207,
}

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}"
VALUE_UNIT_CHANGE_DATE = date(2023, 1, 3)


class Filing13F(TypedDict):
    accession: str
    report_period: str
    filing_date: str
    acceptance_datetime: str
    form: str


class Holding13F(TypedDict):
    cusip: str
    value_usd: float
    shares: float | None
    shares_type: str
    put_call: str


def build_13f_panel(registry: Registry, name: str, quarters: int = 4) -> DatasetEntry:
    ua = os.environ.get("EDGAR_USER_AGENT")
    if not ua:
        raise RuntimeError("set EDGAR_USER_AGENT (e.g. 'flock research <you@example.com>')")
    rows: list[dict[str, object]] = []
    with httpx.Client(timeout=30, headers={"User-Agent": ua}) as client:
        for manager, cik in MANAGERS.items():
            subs = client.get(SUBMISSIONS_URL.format(cik=cik)).json()
            for filing in recent_13f_filings(subs, quarters):
                accession = filing["accession"]
                acc_nodash = accession.replace("-", "")
                filing_root = ARCHIVE_URL.format(cik=cik, accession=acc_nodash)
                index = client.get(f"{filing_root}/index.json").json()
                xml_name = pick_info_table(index)
                if xml_name is None:
                    continue
                source_url = f"{filing_root}/{xml_name}"
                xml = client.get(source_url).text
                for holding in parse_info_table_records(
                    xml,
                    value_scale=filing_value_scale(filing["filing_date"]),
                ):
                    rows.append(
                        {
                            "manager": manager,
                            "manager_cik": cik,
                            "period": filing["report_period"],
                            "filing_date": filing["filing_date"],
                            "acceptance_datetime": filing["acceptance_datetime"],
                            "form": filing["form"],
                            "accession": accession,
                            "source_url": source_url,
                            **holding,
                        }
                    )
                time.sleep(0.15)  # EDGAR fair-use rate limit
    if not rows:
        raise RuntimeError("no 13F holdings retrieved")
    panel = pd.DataFrame(rows)
    dataset_dir = DATASETS_DIR / name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(dataset_dir / "holdings13f.parquet", index=False)
    with open(dataset_dir / "meta.json", "w") as f:
        json.dump(
            {
                "builder": "refs13f",
                "panel_schema_version": 3,
                "managers": list(MANAGERS),
                "quarters": quarters,
                "activity_basis": "realized_holdings_change",
                "amendment_policy": "retain_all_and_quarantine_ambiguous_periods",
            },
            f,
        )
    return registry.register(
        name,
        "refs13f",
        dataset_dir,
        {"quarters": quarters, "panel_schema_version": 3},
        primary_file="holdings13f.parquet",
    )


def recent_13f_filings(submissions: dict, quarters: int) -> list[Filing13F]:
    """Return originals and amendments for the latest report periods.

    Amendments can either restate a filing or add previously confidential
    holdings. Submissions metadata does not distinguish those semantics, so all
    accessions for a selected period are retained and downstream harmonization
    quarantines ambiguous manager-periods.
    """
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    candidates: list[Filing13F] = []
    for index, form in enumerate(forms):
        if form not in {"13F-HR", "13F-HR/A"}:
            continue

        def field(name: str, row_index: int = index) -> str:
            values = recent.get(name, [])
            return str(values[row_index]) if row_index < len(values) else ""

        accession = field("accessionNumber")
        report_period = field("reportDate")
        if not accession or not report_period:
            continue
        candidates.append(
            {
                "accession": accession,
                "report_period": report_period,
                "filing_date": field("filingDate"),
                "acceptance_datetime": field("acceptanceDateTime"),
                "form": str(form),
            }
        )
    selected_periods: list[str] = []
    for filing in candidates:
        period = filing["report_period"]
        if period not in selected_periods:
            selected_periods.append(period)
        if len(selected_periods) == quarters:
            break
    selected = set(selected_periods)
    return [filing for filing in candidates if filing["report_period"] in selected]


def recent_13f_accessions(submissions: dict, quarters: int) -> list[tuple[str, str]]:
    """Pure transform: EDGAR submissions JSON -> [(accession, report period)]."""
    return [
        (filing["accession"], filing["report_period"])
        for filing in recent_13f_filings(submissions, quarters)
    ]


def pick_info_table(index: dict) -> str | None:
    """Choose the information-table XML from a filing's index.json."""
    items = index.get("directory", {}).get("item", [])
    candidates = [
        i["name"] for i in items
        if i["name"].lower().endswith(".xml") and "primary_doc" not in i["name"].lower()
    ]
    return candidates[0] if candidates else None


def filing_value_scale(filing_date: str) -> float:
    """Return the SEC-mandated XML value multiplier for a filing date."""
    try:
        filed = date.fromisoformat(filing_date)
    except ValueError as error:
        raise ValueError(f"invalid 13F filing date {filing_date!r}") from error
    return 1.0 if filed >= VALUE_UNIT_CHANGE_DATE else 1000.0


def parse_info_table_records(
    xml_text: str,
    *,
    value_scale: float = 1000.0,
) -> list[Holding13F]:
    """Parse an information table with share counts required for activity."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns = {"n": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    tag = "n:infoTable" if ns else "infoTable"
    prefix = "n:" if ns else ""
    out: list[Holding13F] = []
    for info in root.iterfind(f".//{tag}", ns):
        cusip = info.findtext(f"{prefix}cusip", default="", namespaces=ns)
        value = info.findtext(f"{prefix}value", default="0", namespaces=ns)
        shares = info.findtext(f"{prefix}shrsOrPrnAmt/{prefix}sshPrnamt", namespaces=ns)
        shares_type = info.findtext(
            f"{prefix}shrsOrPrnAmt/{prefix}sshPrnamtType",
            default="",
            namespaces=ns,
        )
        put_call = info.findtext(f"{prefix}putCall", default="", namespaces=ns)
        if cusip:
            out.append(
                {
                    "cusip": cusip.strip(),
                    "value_usd": float(value) * value_scale,
                    "shares": float(shares) if shares else None,
                    "shares_type": shares_type.strip().upper(),
                    "put_call": put_call.strip().upper(),
                }
            )
    return out


def parse_info_table(xml_text: str) -> list[tuple[str, float]]:
    """Compatibility view of 13F XML as ``(cusip, value_usd)`` rows."""
    return [
        (holding["cusip"], holding["value_usd"])
        for holding in parse_info_table_records(xml_text)
    ]


def load_13f_panel(dataset_dir: Path) -> pd.DataFrame:
    return pd.read_parquet(dataset_dir / "holdings13f.parquet")
