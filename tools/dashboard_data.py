# tools/dashboard_data.py
"""
Read-only data layer for the Family Financial Dashboard.

This module NEVER runs a new analysis, calls Azure/LLM, or mutates any file.
It only reads the artifacts produced by the analyst flow:

  * data/processed/historical_ledger.csv      -> transaction-level truth
  * data/processed/running_balance.json       -> authoritative monthly headline numbers
  * data/processed/monthly_analysis_history.json -> per-month savings rate + top expenses
  * data/processed/stories/<YYYY-MM>.md        -> the Hebrew narrative per month

Design note on "authoritative numbers":
  - EXPENSES and every transaction-level view are derived from the ledger,
    applying the exact same masks the analyst uses (drop Investments, drop the
    'אנליסט' brokerage keyword, drop rows flagged Excluded / "don't count").
    With those masks the ledger reproduces the official expense totals exactly.
  - INCOME / NET-SAVINGS / INVESTMENT headline figures come from
    running_balance.json so the dashboard matches the monthly stories to the
    shekel (the analyst computes income slightly differently from the raw
    ledger income rows).

All functions are pure (no Streamlit) so they can be unit-tested and reused.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

import pandas as pd

# ── File locations (relative to project root, matching app.py) ──
LEDGER_FILE = "data/processed/historical_ledger.csv"
BALANCE_FILE = "data/processed/running_balance.json"
HISTORY_FILE = "data/processed/monthly_analysis_history.json"
STORIES_DIR = "data/processed/stories"

# Credit-card sources whose sign convention may need normalising (see load_ledger)
_CC_SOURCES = ["Max", "Isracard", "Discount_Credit_Card"]

# Keyword marking an investment/brokerage transfer that must never count as spend
_INVEST_KEYWORD = "אנליסט"

# Economic lens: which categories are "committed / fixed" vs "discretionary".
# Rent, insurance and gan/education are recurring commitments that are hard to
# change month-to-month; everything else is treated as more controllable.
FIXED_CATEGORIES = {
    "Housing_Fixed",
    "Insurance_Health",
    "Insurance",
    "Kids_Family",
}


# ──────────────────────────────────────────────────────────────────────────
# Loading
# ──────────────────────────────────────────────────────────────────────────
def load_ledger() -> pd.DataFrame:
    """Load the full transaction ledger with normalised Date/Amount/Excluded.

    Returns an empty DataFrame if the ledger does not exist yet.
    """
    if not os.path.exists(LEDGER_FILE):
        return pd.DataFrame(
            columns=[
                "Date", "Description", "Amount", "Owner",
                "Source", "Category", "Sub_Category", "Excluded",
            ]
        )

    df = pd.read_csv(LEDGER_FILE)

    # Date -> datetime
    df["Date"] = pd.to_datetime(df.get("Date"), errors="coerce")

    # Amount -> numeric, with the same legacy sign-normalisation as app.py:
    # older data stored credit-card charges as positive; the current convention
    # is negative = money out. Only flip when the data still looks "old".
    df["Amount"] = pd.to_numeric(df.get("Amount"), errors="coerce")
    if "Source" in df.columns:
        cc_mask = df["Source"].isin(_CC_SOURCES)
        if cc_mask.any() and (df.loc[cc_mask, "Amount"] > 0).mean() > 0.5:
            df.loc[cc_mask, "Amount"] = df.loc[cc_mask, "Amount"] * -1

    # Excluded -> clean boolean
    if "Excluded" not in df.columns:
        df["Excluded"] = False
    df["Excluded"] = (
        df["Excluded"].map(
            lambda v: str(v).strip().lower() in ("true", "1", "yes")
        )
        if df["Excluded"].dtype == object
        else df["Excluded"].fillna(False).astype(bool)
    )

    # Drop rows without a usable date and add a Month period column
    df = df.dropna(subset=["Date"]).copy()
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df


def load_balance() -> dict:
    """Load running_balance.json (authoritative headline numbers)."""
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "total_net_savings": 0,
        "total_income": 0,
        "total_expenses": 0,
        "total_investments": 0,
        "months_analyzed": [],
        "monthly_breakdown": {},
    }


def load_history() -> dict:
    """Load monthly_analysis_history.json (savings rate + top expenses per month)."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_story(month: str) -> str | None:
    """Return the raw markdown narrative for a month, or None if absent."""
    path = os.path.join(STORIES_DIR, f"{month}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


# ──────────────────────────────────────────────────────────────────────────
# Masks
# ──────────────────────────────────────────────────────────────────────────
def real_spend(df: pd.DataFrame) -> pd.DataFrame:
    """Return only rows that count as real living expenses (positive amounts, abs'd).

    Applies the exact same three exclusions the analyst uses:
      * Category == 'Investments'            (brokerage/savings transfers)
      * Description contains 'אנליסט'         (analyst brokerage keyword)
      * Excluded == True                     ("don't count" flag)
    """
    if df.empty:
        return df.assign(AbsAmount=pd.Series(dtype=float))
    mask = (
        (df["Amount"] < 0)
        & (df["Category"] != "Investments")
        & (~df["Description"].astype(str).str.contains(_INVEST_KEYWORD, case=False, na=False))
        & (~df["Excluded"])
    )
    out = df[mask].copy()
    out["AbsAmount"] = out["Amount"].abs()
    return out


# ──────────────────────────────────────────────────────────────────────────
# Aggregations
# ──────────────────────────────────────────────────────────────────────────
def monthly_summary() -> pd.DataFrame:
    """Authoritative per-month headline table from running_balance.json.

    Columns: Month, income, expenses, investments, net_savings, savings_rate,
    plus cumulative columns for the balance / net-worth timeline.
    """
    balance = load_balance()
    breakdown = balance.get("monthly_breakdown", {})
    if not breakdown:
        return pd.DataFrame(
            columns=[
                "Month", "income", "expenses", "investments", "net_savings",
                "savings_rate", "cum_net_savings", "cum_investments", "cum_wealth",
            ]
        )

    rows = []
    for month in sorted(breakdown.keys()):
        m = breakdown[month]
        income = m.get("income", 0.0)
        net = m.get("net_savings", 0.0)
        rows.append(
            {
                "Month": month,
                "income": income,
                "expenses": m.get("expenses", 0.0),
                "investments": m.get("investments", 0.0),
                "net_savings": net,
                "savings_rate": (net / income * 100) if income else 0.0,
            }
        )
    df = pd.DataFrame(rows)
    df["cum_net_savings"] = df["net_savings"].cumsum()
    df["cum_investments"] = df["investments"].cumsum()
    df["cum_wealth"] = df["cum_net_savings"] + df["cum_investments"]
    return df


def available_months(df: pd.DataFrame) -> list[str]:
    """Sorted list of months present in the ledger."""
    if df.empty:
        return []
    return sorted(df["Month"].unique().tolist())


def category_monthly(df: pd.DataFrame, level: str = "Category") -> pd.DataFrame:
    """Wide table of spend per (category or sub-category) x month.

    Rows = category/sub-category, columns = months, values = absolute spend.
    Uses real_spend() so it matches the official expense totals.
    """
    spend = real_spend(df)
    if spend.empty:
        return pd.DataFrame()
    pivot = spend.pivot_table(
        index=level, columns="Month", values="AbsAmount", aggfunc="sum", fill_value=0.0
    )
    # Order rows by total descending
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    return pivot


def merchant_totals(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Top merchants by total real spend across all months.

    Columns: Description, total, count, avg.
    """
    spend = real_spend(df)
    if spend.empty:
        return pd.DataFrame(columns=["Description", "total", "count", "avg"])
    g = (
        spend.groupby(spend["Description"].astype(str).str.strip())["AbsAmount"]
        .agg(total="sum", count="count", avg="mean")
        .reset_index()
        .rename(columns={"Description": "Description"})
        .sort_values("total", ascending=False)
        .head(top_n)
    )
    return g


def fixed_vs_variable(df: pd.DataFrame) -> pd.DataFrame:
    """Per-month split of committed/fixed vs discretionary/variable spend.

    Columns: Month, Fixed, Variable, fixed_share (% of that month's spend).
    """
    spend = real_spend(df)
    if spend.empty:
        return pd.DataFrame(columns=["Month", "Fixed", "Variable", "fixed_share"])
    spend = spend.assign(
        Bucket=spend["Category"].map(
            lambda c: "Fixed" if c in FIXED_CATEGORIES else "Variable"
        )
    )
    wide = (
        spend.pivot_table(
            index="Month", columns="Bucket", values="AbsAmount", aggfunc="sum", fill_value=0.0
        )
        .reset_index()
    )
    for col in ("Fixed", "Variable"):
        if col not in wide.columns:
            wide[col] = 0.0
    total = wide["Fixed"] + wide["Variable"]
    wide["fixed_share"] = (wide["Fixed"] / total * 100).where(total > 0, 0.0)
    return wide[["Month", "Fixed", "Variable", "fixed_share"]]


def category_anomalies(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """For a given month, compare each category's spend to its average in the
    OTHER months, to surface where this month deviates.

    Columns: Category, this_month, avg_other, delta, delta_pct.
    Sorted by absolute delta descending. Empty if <2 months of data.
    """
    pivot = category_monthly(df, level="Category")
    if pivot.empty or month not in pivot.columns or pivot.shape[1] < 2:
        return pd.DataFrame(columns=["Category", "this_month", "avg_other", "delta", "delta_pct"])
    other_cols = [c for c in pivot.columns if c != month]
    this_month = pivot[month]
    avg_other = pivot[other_cols].mean(axis=1)
    out = pd.DataFrame(
        {
            "Category": pivot.index,
            "this_month": this_month.values,
            "avg_other": avg_other.values,
        }
    )
    out["delta"] = out["this_month"] - out["avg_other"]
    out["delta_pct"] = (out["delta"] / out["avg_other"] * 100).where(out["avg_other"] > 0, 0.0)
    out = out[(out["this_month"] > 0) | (out["avg_other"] > 0)]
    return out.reindex(out["delta"].abs().sort_values(ascending=False).index).reset_index(drop=True)
