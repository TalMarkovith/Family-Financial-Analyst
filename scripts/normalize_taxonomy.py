"""Remap stored ledger rows so each sub-category sits under its one parent.

Usage (from the project root):
    python3 scripts/normalize_taxonomy.py            # dry run: report only
    python3 scripts/normalize_taxonomy.py --apply    # back up, then write

Only Category (and known sub-category misspellings, e.g. '_Pharm') change.
Amounts, dates, descriptions and the Excluded flag are never touched, so every
month's income, expenses and net savings stay the same. The script checks this
and refuses to write if any month's totals would move.

Output shows counts and per-month category totals only, never descriptions.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.month_totals import compute_month_totals, split_month, net_spending_by  # noqa: E402
from tools.taxonomy import normalize_frame  # noqa: E402

DEFAULT_LEDGER = "data/processed/historical_ledger.csv"


def _month(df: pd.DataFrame) -> pd.Series:
    return pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m")


def remap_ledger(ledger: pd.DataFrame):
    """Return (remapped ledger, mask of rows whose Category/Sub_Category changed)."""
    out = normalize_frame(ledger)
    changed = (ledger["Category"].astype(str) != out["Category"].astype(str)) | (
        ledger["Sub_Category"].astype(str) != out["Sub_Category"].astype(str)
    )
    return out, changed


def month_totals(ledger: pd.DataFrame) -> dict:
    m = _month(ledger)
    return {k: compute_month_totals(g) for k, g in ledger.groupby(m)}


def category_table(ledger: pd.DataFrame) -> pd.DataFrame:
    m = _month(ledger)
    cols = {k: net_spending_by(split_month(g)[1], "Category") for k, g in ledger.groupby(m)}
    return pd.DataFrame(cols).fillna(0).round(0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--apply", action="store_true", help="write the remapped ledger (after a backup)")
    args = ap.parse_args(argv)

    if not os.path.exists(args.ledger):
        print(f"Ledger not found: {args.ledger}")
        return 1
    before = pd.read_csv(args.ledger)
    after, changed = remap_ledger(before)

    print(f"Rows: {len(before)} | rows to remap: {int(changed.sum())}")
    if changed.any():
        moves = (pd.DataFrame({"from": before.loc[changed, "Category"].astype(str) + "/" + before.loc[changed, "Sub_Category"].astype(str),
                               "to": after.loc[changed, "Category"].astype(str) + "/" + after.loc[changed, "Sub_Category"].astype(str)})
                 .value_counts().rename("rows"))
        print(moves.to_string())

    tb, ta = month_totals(before), month_totals(after)
    moved = [m for m in tb if any(abs(tb[m][k] - ta[m][k]) > 0.005 for k in ("income", "expenses", "investments", "net_savings"))]
    if moved:
        print(f"REFUSING: month totals would change in {moved}")
        return 2
    print("Month totals unchanged in every month ✓")

    if changed.any():
        cb, ca = category_table(before), category_table(after)
        diff = ca.sub(cb, fill_value=0)
        diff = diff.loc[(diff != 0).any(axis=1), (diff != 0).any(axis=0)]
        if diff.empty:
            print("Category totals unchanged (only sub-category spelling fixes).")
        else:
            print("\nNet spending change by category and month (after − before):")
            print(diff.to_string())

    if not args.apply:
        print("\nDry run — nothing written. Re-run with --apply to write.")
        return 0
    if not changed.any():
        print("Nothing to write.")
        return 0

    backup_dir = os.path.join(os.path.dirname(args.ledger), f"_backup_taxonomy_{datetime.now():%Y%m%d_%H%M%S}")
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2(args.ledger, backup_dir)
    after.to_csv(args.ledger, index=False)
    print(f"\nWrote {args.ledger} (backup in {backup_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
