"""Pure-transform tests for network dataset builders (no network)."""

import pandas as pd
import pytest

from flock.data.builders.kalshi import candles_to_bars
from flock.data.builders.polymarket import history_to_bars, parse_market
from flock.data.builders.real_world_refs import (
    parse_info_table,
    parse_info_table_records,
    recent_13f_accessions,
    recent_13f_filings,
)
from flock.data.schemas import write_dataset


def test_polymarket_parse_market():
    m = {
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["1", "0"]',
        "clobTokenIds": '["111", "222"]',
        "slug": "will-x-happen",
        "question": "Will X happen?",
    }
    parsed = parse_market(m)
    assert parsed is not None
    symbol, token, resolution = parsed
    assert token == "111" and resolution == 1.0
    assert symbol.startswith("PM-WILL-X")
    assert parse_market({"outcomes": "bad"}) is None


def test_polymarket_history_settles_at_resolution():
    history = [
        {"t": 1_700_000_000 + i * 86_400, "p": 0.4 + 0.01 * i} for i in range(20)
    ]
    bars = history_to_bars(history, "PM-T", resolution=1.0)
    assert bars is not None
    assert bars.iloc[-1]["close"] == 1.0
    assert bars.iloc[-1]["high"] >= 1.0
    assert bars["ts"].is_monotonic_increasing


def test_kalshi_candles_to_bars_converts_cents():
    candles = [
        {"end_period_ts": 1_700_000_000 + i * 86_400,
         "price": {"open": 40 + i, "high": 45 + i, "low": 38 + i, "close": 42 + i},
         "volume": 10}
        for i in range(20)
    ]
    bars = candles_to_bars(candles, "KX-T", resolution=0.0)
    assert bars is not None
    assert 0 < bars.iloc[0]["close"] < 1
    assert bars.iloc[-1]["close"] == 0.0


def test_13f_info_table_parsing_with_namespace():
    xml = """<?xml version="1.0"?>
    <informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
      <infoTable><nameOfIssuer>ACME</nameOfIssuer><cusip>037833100</cusip>
        <value>1500</value><shrsOrPrnAmt><sshPrnamt>10000</sshPrnamt>
        <sshPrnamtType>SH</sshPrnamtType></shrsOrPrnAmt></infoTable>
      <infoTable><nameOfIssuer>BETA</nameOfIssuer><cusip>594918104</cusip>
        <value>2500</value><shrsOrPrnAmt><sshPrnamt>20000</sshPrnamt>
        <sshPrnamtType>SH</sshPrnamtType></shrsOrPrnAmt><putCall>CALL</putCall></infoTable>
    </informationTable>"""
    holdings = parse_info_table(xml)
    assert holdings == [("037833100", 1_500_000.0), ("594918104", 2_500_000.0)]
    records = parse_info_table_records(xml)
    assert records[0]["shares"] == 10_000
    assert records[0]["shares_type"] == "SH"
    assert records[1]["put_call"] == "CALL"
    assert parse_info_table("not xml") == []


def test_13f_accession_selection():
    subs = {
        "filings": {
            "recent": {
                "form": ["10-K", "13F-HR", "13F-HR/A", "13F-HR"],
                "accessionNumber": ["a", "b", "c", "d"],
                "reportDate": ["2024-12-31", "2024-09-30", "2024-09-30", "2024-06-30"],
                "filingDate": ["2025-01-01", "2024-11-14", "2024-11-20", "2024-08-14"],
                "acceptanceDateTime": [
                    "2025-01-01T00:00:00.000Z",
                    "2024-11-14T17:00:00.000Z",
                    "2024-11-20T17:00:00.000Z",
                    "2024-08-14T17:00:00.000Z",
                ],
            }
        }
    }
    accs = recent_13f_accessions(subs, quarters=2)
    assert accs == [("b", "2024-09-30"), ("d", "2024-06-30")]
    filings = recent_13f_filings(subs, quarters=2)
    assert filings[0] == {
        "accession": "b",
        "report_period": "2024-09-30",
        "filing_date": "2024-11-14",
        "acceptance_datetime": "2024-11-14T17:00:00.000Z",
        "form": "13F-HR",
    }


def test_registry_primary_file(tmp_path):
    from flock.data.registry import Registry

    d = tmp_path / "refs"
    d.mkdir()
    pd.DataFrame({"manager": ["x"], "cusip": ["1"], "value_usd": [1.0]}).to_parquet(
        d / "holdings13f.parquet"
    )
    reg = Registry(root=tmp_path)
    entry = reg.register("refs", "refs13f", d, {}, primary_file="holdings13f.parquet")
    assert entry.rows == 1


def test_binary_dataset_allows_zero_settlement_with_complete_yes_semantics(tmp_path):
    bars = pd.DataFrame(
        [
            {
                "ts": "2030-01-01",
                "symbol": "KX-TEST",
                "open": 0.4,
                "high": 0.5,
                "low": 0.3,
                "close": 0.4,
                "volume": 10,
            },
            {
                "ts": "2030-01-02",
                "symbol": "KX-TEST",
                "open": 0.4,
                "high": 0.4,
                "low": 0.0,
                "close": 0.0,
                "volume": 10,
            },
        ]
    )
    meta = {
        "instrument_kind": "binary",
        "contracts": [
            {
                "symbol": "KX-TEST",
                "question": "Will the test resolve yes?",
                "rules": "Resolves Yes when the test condition is met.",
                "open_ts": "2030-01-01T00:00:00Z",
                "close_ts": "2030-01-02T00:00:00Z",
                "resolution": 0.0,
                "yes_label": "Yes",
                "no_label": "No",
                "price_semantics": "YES probability in [0,1]",
            }
        ],
    }
    assert write_dataset(tmp_path / "binary", bars, meta=meta) == 2


def test_binary_dataset_rejects_missing_contract_semantics(tmp_path):
    bars = pd.DataFrame(
        [
            {
                "ts": "2030-01-01",
                "symbol": "PM-X",
                "open": 0.5,
                "high": 0.5,
                "low": 0.5,
                "close": 0.5,
                "volume": 0,
            }
        ]
    )
    with pytest.raises(ValueError, match="contract metadata"):
        write_dataset(
            tmp_path / "binary",
            bars,
            meta={"instrument_kind": "binary", "contracts": [{"symbol": "PM-X"}]},
        )


def test_binary_dataset_rejects_bar_before_intraday_listing(tmp_path):
    bars = pd.DataFrame(
        [
            {
                "ts": "2030-01-01T00:00:00Z",
                "symbol": "PM-X",
                "open": 0.5,
                "high": 0.5,
                "low": 0.5,
                "close": 0.5,
                "volume": 0,
            },
            {
                "ts": "2030-01-02T00:00:00Z",
                "symbol": "PM-X",
                "open": 0.5,
                "high": 1.0,
                "low": 0.5,
                "close": 1.0,
                "volume": 0,
            },
        ]
    )
    meta = {
        "instrument_kind": "binary",
        "contracts": [
            {
                "symbol": "PM-X",
                "question": "Will X occur?",
                "rules": "Resolves Yes if X occurs.",
                "open_ts": "2030-01-01T12:00:00Z",
                "close_ts": "2030-01-02T00:00:00Z",
                "resolution": 1.0,
                "yes_label": "Yes",
                "no_label": "No",
                "price_semantics": "YES probability in [0,1]",
            }
        ],
    }

    with pytest.raises(ValueError, match="outside the contract lifetime"):
        write_dataset(tmp_path / "binary-intraday", bars, meta=meta)
