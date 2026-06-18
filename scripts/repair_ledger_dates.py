"""
Repair historical_ledger.csv: reconstruct missing Date values from Year/Month/Day columns.
Safe — only fills NaN dates, never overwrites existing valid dates.
"""
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime

LEDGER = Path('data/processed/historical_ledger.csv')

# Backup
backup = LEDGER.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
shutil.copy(LEDGER, backup)
print(f"📦 Backup created: {backup}")

df = pd.read_csv(LEDGER)
print(f"\n📊 Before repair:")
print(f"   Total rows: {len(df)}")
print(f"   Valid Date: {pd.to_datetime(df['Date'], errors='coerce').notna().sum()}")
print(f"   NaN Date:   {pd.to_datetime(df['Date'], errors='coerce').isna().sum()}")

# Parse existing dates
df['Date_parsed'] = pd.to_datetime(df['Date'], errors='coerce')

# For rows missing a parsed date but having Year/Month/Day → reconstruct
mask_fixable = (
    df['Date_parsed'].isna()
    & df['Year'].notna()
    & df['Month'].notna()
    & df['Day'].notna()
)

print(f"\n🔧 Fixable rows (NaN Date + valid Y/M/D): {mask_fixable.sum()}")

if mask_fixable.any():
    fixable = df.loc[mask_fixable].copy()
    fixable['Date_parsed'] = pd.to_datetime(
        dict(
            year=fixable['Year'].astype(int),
            month=fixable['Month'].astype(int),
            day=fixable['Day'].astype(int),
        ),
        errors='coerce',
    )
    df.loc[mask_fixable, 'Date_parsed'] = fixable['Date_parsed']

# Drop rows where we still can't recover a date (9 orphans)
orphans = df['Date_parsed'].isna().sum()
if orphans > 0:
    print(f"⚠️  Dropping {orphans} unrecoverable orphan rows (no Date AND no Y/M/D)")
    df = df[df['Date_parsed'].notna()].copy()

# Overwrite Date column with ISO-format strings (consistent format)
df['Date'] = df['Date_parsed'].dt.strftime('%Y-%m-%d')
df = df.drop(columns=['Date_parsed'])

# Save
df.to_csv(LEDGER, index=False, encoding='utf-8-sig')

print(f"\n✅ After repair:")
print(f"   Total rows: {len(df)}")
parsed = pd.to_datetime(df['Date'], errors='coerce')
print(f"   Valid Date: {parsed.notna().sum()}")
print(f"   NaN Date:   {parsed.isna().sum()}")
print(f"\n📅 Months in ledger now:")
print(parsed.dt.to_period('M').value_counts().sort_index())
