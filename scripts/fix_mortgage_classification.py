"""Relabel the 4 mortgage rows that were misclassified as Income/Other_Income_Bit."""
import pandas as pd
from pathlib import Path

LEDGER = Path('data/processed/historical_ledger.csv')

df = pd.read_csv(LEDGER)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

mask = (
    df['Description'].astype(str).str.contains('דסק-משכנתא', na=False)
    & (df['Category'] == 'Income')
)
hits = df[mask]
print(f"📌 Re-labeling {len(hits)} mortgage rows (Income → Housing_Fixed/Rent_Mortgage):")
for _, r in hits.iterrows():
    print(f"   • {r['Date'].date()}  {r['Description']:<25}  ₪{r['Amount']:,.2f}")

df.loc[mask, 'Category'] = 'Housing_Fixed'
df.loc[mask, 'Sub_Category'] = 'Rent_Mortgage'

df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
df.to_csv(LEDGER, index=False, encoding='utf-8-sig')
print(f"\n✅ Saved {LEDGER}")
