"""Flag May ₪10k payment to parents (Naḥum & Lizzi) as Excluded — returning a loan, not real rent."""
import pandas as pd
from pathlib import Path

LEDGER = Path('data/processed/historical_ledger.csv')

df = pd.read_csv(LEDGER)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

if 'Excluded' not in df.columns:
    df['Excluded'] = False
df['Excluded'] = df['Excluded'].fillna(False).astype(bool)

# May 2026: payment to Naḥum & Lizzi (parents) — returning a loan
mask = (
    (df['Date'].dt.year == 2026)
    & (df['Date'].dt.month == 5)
    & (df['Description'].astype(str).str.contains('נחום וליזי', na=False))
)

hits = df[mask]
print(f"📌 Flagging {len(hits)} row(s) as Excluded (returning loan to parents):")
for _, r in hits.iterrows():
    print(f"   • {r['Date'].date()}  {r['Description']:<40}  ₪{r['Amount']:,.2f}")

df.loc[mask, 'Excluded'] = True

df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
df.to_csv(LEDGER, index=False, encoding='utf-8-sig')
print(f"\n✅ Saved {LEDGER}")
print(f"   Total Excluded rows now: {df['Excluded'].sum()}")
