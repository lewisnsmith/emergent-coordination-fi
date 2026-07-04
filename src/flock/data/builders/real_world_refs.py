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
from pathlib import Path

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


def build_13f_panel(registry: Registry, name: str, quarters: int = 4) -> DatasetEntry:
    ua = os.environ.get("EDGAR_USER_AGENT")
    if not ua:
        raise RuntimeError("set EDGAR_USER_AGENT (e.g. 'flock research <you@example.com>')")
    rows = []
    with httpx.Client(timeout=30, headers={"User-Agent": ua}) as client:
        for manager, cik in MANAGERS.items():
            subs = client.get(SUBMISSIONS_URL.format(cik=cik)).json()
            for accession, period in recent_13f_accessions(subs, quarters):
                acc_nodash = accession.replace("-", "")
                index = client.get(
                    ARCHIVE_URL.format(cik=cik, accession=f"{acc_nodash}/index.json")
                ).json()
                xml_name = pick_info_table(index)
                if xml_name is None:
                    continue
                xml = client.get(
                    ARCHIVE_URL.format(cik=cik, accession=f"{acc_nodash}/{xml_name}")
                ).text
                for cusip, value in parse_info_table(xml):
                    rows.append(
                        {"manager": manager, "period": period, "cusip": cusip,
                         "value_usd": value}
                    )
                time.sleep(0.15)  # EDGAR fair-use rate limit
    if not rows:
        raise RuntimeError("no 13F holdings retrieved")
    panel = pd.DataFrame(rows)
    dataset_dir = DATASETS_DIR / name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(dataset_dir / "holdings13f.parquet", index=False)
    with open(dataset_dir / "meta.json", "w") as f:
        json.dump({"builder": "refs13f", "managers": list(MANAGERS), "quarters": quarters}, f)
    return registry.register(
        name, "refs13f", dataset_dir, {"quarters": quarters},
        primary_file="holdings13f.parquet",
    )


def recent_13f_accessions(submissions: dict, quarters: int) -> list[tuple[str, str]]:
    """Pure transform: EDGAR submissions JSON -> [(accession, report period)]."""
    recent = submissions.get("filings", {}).get("recent", {})
    out = []
    for form, accession, period in zip(
        recent.get("form", []),
        recent.get("accessionNumber", []),
        recent.get("reportDate", []),
        strict=False,
    ):
        if form == "13F-HR":
            out.append((accession, period))
        if len(out) >= quarters:
            break
    return out


def pick_info_table(index: dict) -> str | None:
    """Choose the information-table XML from a filing's index.json."""
    items = index.get("directory", {}).get("item", [])
    candidates = [
        i["name"] for i in items
        if i["name"].lower().endswith(".xml") and "primary_doc" not in i["name"].lower()
    ]
    return candidates[0] if candidates else None


def parse_info_table(xml_text: str) -> list[tuple[str, float]]:
    """Pure transform: 13F info-table XML -> [(cusip, value_usd)]."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns = {"n": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    tag = "n:infoTable" if ns else "infoTable"
    out = []
    for info in root.iterfind(f".//{tag}", ns):
        cusip = info.findtext("n:cusip" if ns else "cusip", default="", namespaces=ns)
        value = info.findtext("n:value" if ns else "value", default="0", namespaces=ns)
        if cusip:
            # 13F values are reported in thousands of dollars
            out.append((cusip.strip(), float(value) * 1000.0))
    return out


def load_13f_panel(dataset_dir: Path) -> pd.DataFrame:
    return pd.read_parquet(dataset_dir / "holdings13f.parquet")
