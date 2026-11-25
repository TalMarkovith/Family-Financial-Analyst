"""
Tests for the single taxonomy (tools/taxonomy.py), the ledger remap script and
the classifier's progress counter. Synthetic data only, no network.
"""
import re

import pandas as pd
import pytest

from tools.taxonomy import (TAXONOMY, ALL_CATEGORIES, canonical_parent,
                            normalize_category, normalize_frame)
from local_prompts.prompts import FINANCIAL_TAXONOMY_PROMPT


def test_every_sub_category_has_exactly_one_parent():
    seen = {}
    for parent, subs in TAXONOMY.items():
        for sub in subs:
            assert sub not in seen, f"{sub} under {seen[sub]} and {parent}"
            seen[sub] = parent
    assert ALL_CATEGORIES == list(TAXONOMY)


@pytest.mark.parametrize("sub,parent", [
    ("Groceries_Supermarket", "Food"),
    ("Dining_Restaurants_Wolt", "Food_Delivery"),
    ("General_Shopping", "Variable_Daily"),
    ("_Pharm", "Pharm"),
])
def test_canonical_parent(sub, parent):
    assert canonical_parent(sub) == parent


def test_normalize_moves_parent_and_fixes_alias_but_keeps_unknowns():
    assert normalize_category("Variable_Daily", "Groceries_Supermarket") == ("Food", "Groceries_Supermarket")
    assert normalize_category("Variable_Daily", "Dining_Restaurants_Wolt") == ("Food_Delivery", "Dining_Restaurants_Wolt")
    assert normalize_category("Pharm", "_Pharm") == ("Pharm", "Pharm")
    assert normalize_category("Unknown", "Unknown") == ("Unknown", "Unknown")
    assert normalize_category("Error", None) == ("Error", None)


def test_prompt_taxonomy_matches_code():
    """The LLM must be offered exactly the categories the app accepts."""
    listed = dict(re.findall(r"^\s*\d+\.\s+(\w+): \[([^\]]*)\]", FINANCIAL_TAXONOMY_PROMPT, re.M))
    listed = {k: [s.strip() for s in v.split(",")] for k, v in listed.items()}
    assert listed == TAXONOMY


def _ledger():
    rows = [
        # Date, Description, Amount, Category, Sub_Category, Excluded
        ("2026-08-03", "shop a", -300.0, "Variable_Daily", "Groceries_Supermarket", False),
        ("2026-08-04", "shop b", -200.0, "Food", "Groceries_Supermarket", False),
        ("2026-08-05", "delivery", -150.0, "Variable_Daily", "Dining_Restaurants_Wolt", False),
        ("2026-08-06", "refund", 50.0, "Variable_Daily", "Dining_Restaurants_Wolt", False),
        ("2026-08-07", "pharmacy", -40.0, "Pharm", "_Pharm", False),
        ("2026-08-01", "salary", 10000.0, "Income", "Tal_Salary", False),
        ("2026-09-02", "settlement", 999.0, "Variable_Daily", "General_Shopping", True),
        ("2026-09-03", "clothes", -120.0, "Variable_Daily", "Clothing_Shoes", False),
        ("2026-09-01", "salary", 9000.0, "Income", "Tal_Salary", False),
    ]
    return pd.DataFrame(rows, columns=["Date", "Description", "Amount", "Category", "Sub_Category", "Excluded"])


def test_remap_changes_labels_only_and_month_totals_stay_equal():
    from scripts.normalize_taxonomy import remap_ledger, month_totals, category_table
    before = _ledger()
    after, changed = remap_ledger(before)
    assert changed.sum() == 4
    for col in ("Date", "Description", "Amount", "Excluded"):
        assert before[col].equals(after[col])
    assert month_totals(before) == month_totals(after)
    cats = category_table(after)
    assert cats.loc["Food", "2026-08"] == 500
    assert cats.loc["Food_Delivery", "2026-08"] == 100  # 150 spent, 50 refunded
    assert "Variable_Daily" not in cats.index or cats.loc["Variable_Daily", "2026-08"] == 0


def test_script_dry_run_writes_nothing_and_apply_backs_up(tmp_path, capsys):
    from scripts.normalize_taxonomy import main
    path = tmp_path / "ledger.csv"
    _ledger().to_csv(path, index=False)
    original = path.read_text()
    assert main(["--ledger", str(path)]) == 0
    assert path.read_text() == original
    out = capsys.readouterr().out
    assert "rows to remap: 4" in out and "Dry run" in out
    assert "shop a" not in out  # no transaction descriptions in output
    assert main(["--ledger", str(path), "--apply"]) == 0
    assert normalize_frame(pd.read_csv(path)).equals(pd.read_csv(path))
    backups = list(tmp_path.glob("_backup_taxonomy_*/ledger.csv"))
    assert len(backups) == 1 and backups[0].read_text() == original


def test_classifier_counter_and_parent_normalization(monkeypatch, capsys):
    import tools.classify_dataframe as cd

    class FakeMemory:
        def find_similar_merchant(self, name, threshold):
            return {"category": "Variable_Daily", "sub_category": "Groceries_Supermarket", "matched_name": "x"}

    monkeypatch.setattr(cd, "MemoryManager", FakeMemory)
    monkeypatch.setattr(cd, "AzureOpenAI", lambda **kw: object())
    df = pd.DataFrame({"Description": ["market one", "market two", "market three"], "Amount": [-1.0, -2.0, -3.0]},
                      index=[40, 96, 97])  # non-contiguous, like after filtering
    out, pending = cd.classify_dataframe(df)
    printed = capsys.readouterr().out
    assert "[1/3]" in printed and "[3/3]" in printed and "[97/3]" not in printed
    assert set(out["Category"]) == {"Food"}
    assert pending == []
