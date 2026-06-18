"""
Rebuild historical_ledger.csv from raw files using the FIXED parser.

Why: Card 8428 (Tal's Discount-issued CAL/Visa) was silently dropped from
every monthly upload between Feb 2026 and May 2026 due to wrong routing
in the ingestion pipeline. This rebuilds the full ledger month-by-month.

Steps:
  1. Backup data/processed/* (timestamped folder)
  2. Wipe historical_ledger.csv, running_balance.json,
     monthly_analysis_history.json
  3. For each month (Feb→May 2026), pick the matching raw files,
     re-ingest with the new parser, classify with vector memory,
     and save to history.
  4. Re-inject the known Manual_Income entries (recovered from the
     pre-rebuild backup of historical_ledger.csv).
  5. Print a per-month summary so the user can compare to the old KPIs.
"""
import os
import sys
import shutil
import json
import glob
from datetime import datetime
from pathlib import Path

# Add project root to import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Lazy imports of project modules so SSL setup runs first via classify_dataframe
from tools.credit_card_ingestion import IngestionAgent
from classifier_agent import process_and_classify

# ───────────────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────────────
RAW_DIR = Path('data/raw')
PROCESSED_DIR = Path('data/processed')
LEDGER_FILE = PROCESSED_DIR / 'historical_ledger.csv'
RUNNING_BAL_FILE = PROCESSED_DIR / 'running_balance.json'
MONTHLY_HIST_FILE = PROCESSED_DIR / 'monthly_analysis_history.json'

# Hebrew month-name → period mapping
HEB_MONTH = {
    'פברואר': '2026-02',
    'מרץ': '2026-03',
    'אפריל': '2026-04',
    'מאי': '2026-05',
}

# Manual income per month, recovered from the most recent backup.
# (Tal_Salary, Reut_Salary, Other_Income) tuples.
MANUAL_INCOME = {
    '2026-02': {'Tal': 17485.0, 'Reut': 24435.0, 'Other': 8528.0},
    '2026-03': {'Tal': 17485.0, 'Reut': 19037.0, 'Other':  119.0},
    '2026-04': {'Tal': 36365.0, 'Reut': 20843.0, 'Other':    0.0},
    '2026-05': {'Tal': 17904.0, 'Reut': 19653.0, 'Other':    0.0},
}


# ───────────────────────────────────────────────────────────────────
# Step 1: Backup
# ───────────────────────────────────────────────────────────────────
def backup_processed():
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = PROCESSED_DIR / f'_backup_{stamp}'
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in PROCESSED_DIR.glob('*'):
        if f.is_file() and f.name != f'_backup_{stamp}':
            shutil.copy(f, backup_dir / f.name)
    print(f"📦 Backup created at: {backup_dir}")
    return backup_dir


# ───────────────────────────────────────────────────────────────────
# Step 2: Wipe
# ───────────────────────────────────────────────────────────────────
def wipe_processed():
    for f in [LEDGER_FILE, RUNNING_BAL_FILE, MONTHLY_HIST_FILE]:
        if f.exists():
            f.unlink()
            print(f"🗑️  Removed: {f}")
    # Reset running balance to a zeroed shell so update_balance() won't crash
    RUNNING_BAL_FILE.write_text(json.dumps({
        'total_net_savings': 0.0,
        'total_income': 0.0,
        'total_expenses': 0.0,
        'total_investments': 0.0,
        'months_analyzed': [],
        'monthly_breakdown': {},
    }, ensure_ascii=False, indent=2))
    MONTHLY_HIST_FILE.write_text(json.dumps({}, ensure_ascii=False, indent=2))
    print("✅ Processed data wiped & re-initialized as empty stores")


# ───────────────────────────────────────────────────────────────────
# Step 3: Group raw files by month
# ───────────────────────────────────────────────────────────────────
def group_files_by_month():
    files = sorted(RAW_DIR.glob('*.xlsx'))
    buckets = {m: [] for m in HEB_MONTH.values()}
    skipped = []
    for f in files:
        name = f.name
        matched = False
        for heb, month in HEB_MONTH.items():
            if heb in name:
                buckets[month].append(str(f))
                matched = True
                break
        if not matched:
            skipped.append(name)
    if skipped:
        print(f"\n⏭️  Skipping ambiguous files (no clear month):")
        for s in skipped:
            print(f"     • {s}")
    return buckets


# ───────────────────────────────────────────────────────────────────
# Step 4: Process one month
# ───────────────────────────────────────────────────────────────────
def process_month(month_str: str, files: list):
    print(f"\n{'='*70}")
    print(f"📅 Processing {month_str}  ({len(files)} files)")
    print('='*70)
    for f in files:
        print(f"   • {os.path.basename(f)}")

    if not files:
        print("   ⚠️  No files for this month — skipping")
        return None

    # Phase 1: ingest
    agent = IngestionAgent()
    raw_df = agent.run_monthly_ingestion(files)
    if raw_df.empty:
        print(f"   ⚠️  No transactions after ingestion — skipping")
        return None

    # Make sure Date is datetime
    raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
    raw_df = raw_df.dropna(subset=['Date'])

    # Filter to selected month
    year, mo = map(int, month_str.split('-'))
    filtered = raw_df[
        (raw_df['Date'].dt.year == year) & (raw_df['Date'].dt.month == mo)
    ].copy()
    print(f"\n   ✅ {len(filtered)} transactions in {month_str} after filtering")
    if filtered.empty:
        return None

    # Phase 2: classify (vector-memory only, won't burn LLM budget if memory hits)
    classified, pending_reviews = process_and_classify(filtered)
    classified['Date'] = pd.to_datetime(classified['Date'], errors='coerce')
    classified['Month_Year'] = classified['Date'].dt.to_period('M').astype(str)

    # Phase 3: inject manual income for this month
    income_cfg = MANUAL_INCOME.get(month_str, {})
    income_rows = []
    if income_cfg.get('Tal', 0) > 0:
        income_rows.append({
            'Date': pd.to_datetime(f"{month_str}-01"),
            'Description': 'Tal Salary (Manual Entry)',
            'Amount': income_cfg['Tal'],
            'Owner': 'Tal',
            'Source': 'Manual_Income',
            'Category': 'Income',
            'Sub_Category': 'Tal_Salary',
            'Month_Year': month_str,
        })
    if income_cfg.get('Reut', 0) > 0:
        income_rows.append({
            'Date': pd.to_datetime(f"{month_str}-01"),
            'Description': 'Reut Salary (Manual Entry)',
            'Amount': income_cfg['Reut'],
            'Owner': 'Reut',
            'Source': 'Manual_Income',
            'Category': 'Income',
            'Sub_Category': 'Reut_Salary',
            'Month_Year': month_str,
        })
    if income_cfg.get('Other', 0) > 0:
        income_rows.append({
            'Date': pd.to_datetime(f"{month_str}-01"),
            'Description': 'Other Income (Manual Entry)',
            'Amount': income_cfg['Other'],
            'Owner': 'Joint',
            'Source': 'Manual_Income',
            'Category': 'Income',
            'Sub_Category': 'Other_Income_Bit',
            'Month_Year': month_str,
        })
    if income_rows:
        classified = pd.concat([classified, pd.DataFrame(income_rows)], ignore_index=True)
        print(f"   💰 Injected {len(income_rows)} manual-income rows "
              f"(₪{sum(r['Amount'] for r in income_rows):,.0f})")

    return classified


# ───────────────────────────────────────────────────────────────────
# Step 5: Save merged ledger
# ───────────────────────────────────────────────────────────────────
def save_ledger(all_months_dfs):
    if not all_months_dfs:
        print("\n⚠️  No data parsed — leaving processed/ empty")
        return
    full = pd.concat(all_months_dfs, ignore_index=True)
    full['Date'] = pd.to_datetime(full['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    full = full.dropna(subset=['Date'])
    if 'Month_Year' in full.columns:
        full = full.drop(columns=['Month_Year'])
    if 'Excluded' not in full.columns:
        full['Excluded'] = False
    full.to_csv(LEDGER_FILE, index=False, encoding='utf-8-sig')
    print(f"\n✅ Wrote {len(full)} rows to {LEDGER_FILE}")


# ───────────────────────────────────────────────────────────────────
# Step 6: Per-month summary
# ───────────────────────────────────────────────────────────────────
def print_summary():
    if not LEDGER_FILE.exists():
        return
    df = pd.read_csv(LEDGER_FILE)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    print("\n" + "="*70)
    print("📊 REBUILD SUMMARY")
    print("="*70)
    for month in sorted(df['Month'].unique()):
        sub = df[df['Month'] == month]
        income = sub[sub['Amount'] > 0]['Amount'].sum()
        # exclude investments from expenses
        is_investment = (
            (sub['Amount'] < 0) & (
                (sub.get('Category', '') == 'Investments') |
                (sub['Description'].astype(str).str.contains('אנליסט', case=False, na=False))
            )
        )
        expenses = sub[(sub['Amount'] < 0) & (~is_investment)]['Amount'].abs().sum()
        investments = sub[is_investment]['Amount'].abs().sum()
        net = income - expenses

        print(f"\n📅 {month}  ({len(sub)} rows)")
        print(f"   💰 Income:      ₪{income:>12,.2f}")
        print(f"   💸 Expenses:    ₪{expenses:>12,.2f}")
        print(f"   💎 Investments: ₪{investments:>12,.2f}")
        print(f"   🎯 Net Savings: ₪{net:>12,.2f}  ({(net/income*100 if income else 0):.1f}%)")

    print("\n" + "="*70)
    print(f"Total ledger size: {len(df)} rows  |  Months: {sorted(df['Month'].unique())}")
    print("="*70)
    print("\n💡 Next step: open the Streamlit app and click 'Run AI Analysis'")
    print("   per month to regenerate the financial story narratives.")


# ───────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n🔧 Family Financial Analyst — Full Rebuild")
    print(f"   Started: {datetime.now().isoformat(timespec='seconds')}\n")

    backup_processed()
    wipe_processed()

    buckets = group_files_by_month()
    months_in_order = ['2026-02', '2026-03', '2026-04', '2026-05']
    all_dfs = []
    for m in months_in_order:
        df = process_month(m, buckets.get(m, []))
        if df is not None:
            all_dfs.append(df)

    save_ledger(all_dfs)
    print_summary()
    print(f"\n   Finished: {datetime.now().isoformat(timespec='seconds')}")
