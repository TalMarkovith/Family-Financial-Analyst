"""
Tests for multi-sheet Excel ingestion.

IngestionAgent must pull transactions from EVERY sheet in a workbook, not just
the first one. These tests use the "headerless Isracard" layout (col_0=Date,
col_1=Description, col_4=charge amount) because that path exercises the Excel
reader end-to-end without needing Azure or any network access.
"""
import pandas as pd
import pytest

from tools.credit_card_ingestion import IngestionAgent


def _write_headerless_isracard(path, sheets):
    """Write a workbook where each sheet is headerless Isracard-style rows.

    sheets: dict of {sheet_name: [ [date, desc, full_amt, blank, charge_amt], ... ]}
    Each sheet needs >= 2 rows: the first row is consumed as the (bogus) header
    on the initial read, which is exactly what triggers the parser's headerless
    detection + re-read that recovers all rows.
    """
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        for name, rows in sheets.items():
            pd.DataFrame(rows).to_excel(xl, sheet_name=name, header=False, index=False)


def test_multi_sheet_excel_reads_all_sheets(tmp_path):
    """A 3-sheet workbook must yield transactions from all three sheets."""
    path = str(tmp_path / "אשראי 3172 טל.xlsx")
    _write_headerless_isracard(path, {
        "Feb": [["08.02.26", "מכולת שלי", "100", "", "100"],
                ["10.02.26", "תחנת דלק", "200", "", "200"]],
        "Mar": [["09.03.26", "בית קפה", "50", "", "50"],
                ["11.03.26", "סופר בשכונה", "75", "", "75"]],
        "Apr": [["05.04.26", "פארם", "30", "", "30"],
                ["06.04.26", "חניון", "20", "", "20"]],
    })

    df = IngestionAgent().run_monthly_ingestion([path])

    assert len(df) == 6, f"expected 6 rows from 3 sheets, got {len(df)}: {df.to_dict('records')}"
    descs = set(df["Description"].astype(str))
    for merchant in ("מכולת שלי", "תחנת דלק", "בית קפה", "סופר בשכונה", "פארם", "חניון"):
        assert merchant in descs, f"missing {merchant!r} — a sheet was dropped"


def test_single_sheet_still_works(tmp_path):
    """Regression: a plain single-sheet workbook behaves exactly as before."""
    path = str(tmp_path / "אשראי 3172 טל.xlsx")
    _write_headerless_isracard(path, {
        "Feb": [["08.02.26", "מכולת שלי", "100", "", "100"],
                ["10.02.26", "תחנת דלק", "200", "", "200"]],
    })

    df = IngestionAgent().run_monthly_ingestion([path])

    assert len(df) == 2
    assert set(df["Description"].astype(str)) == {"מכולת שלי", "תחנת דלק"}


def test_read_file_targets_requested_sheet(tmp_path):
    """_read_file must return the requested sheet, not always the first."""
    path = str(tmp_path / "plain.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as xl:
        pd.DataFrame({"a": [1]}).to_excel(xl, sheet_name="One", index=False)
        pd.DataFrame({"b": [2]}).to_excel(xl, sheet_name="Two", index=False)

    agent = IngestionAgent()
    first = agent._read_file(path, sheet=0)
    second = agent._read_file(path, sheet="Two")

    assert list(first.columns) == ["a"]
    assert list(second.columns) == ["b"]
