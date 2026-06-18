"""Pre-flag known transfer-style income rows as Excluded."""
import pandas as pd
from pathlib import Path

LEDGER = Path('data/processed/historical_ledger.csv')

df = pd.read_csv(LEDGER)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

if 'Excluded' not in df.columns:
    df['Excluded'] = False
df['Excluded'] = df['Excluded'].fillna(False).astype(bool)

# Flag April 2026 אקסלנס ניה withdrawal (₪30,000, positive)
mask_apr_excellence = (
    (df['Date'].dt.year == 2026)
    & (df['Date'].dt.month == 4)
    & (df['Amount'] > 0)
    & (df['Description'].astype(str).str.contains('אקסלנס', na=False))
)

flagged = df[mask_apr_excellence]
print(f"📌 Flagging {len(flagged)} row(s) as 'Don't Count':")
for _, row in flagged.iterrows():
    print(f"   • {row['Date'].date()}  {row['Description']:<30}  ₪{row['Amount']:,.2f}")

df.loc[mask_apr_excellence, 'Excluded'] = True

# Persist Date as ISO string
df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
df.to_csv(LEDGER, index=False, encoding='utf-8-sig')
print(f"\n✅ Saved {LEDGER}")
print(f"   Total rows now flagged Excluded: {df['Excluded'].sum()}")
