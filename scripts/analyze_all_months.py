"""
Generate monthly stories + KPIs for every month already in the ledger.

This bypasses the upload flow — useful right after rebuild_from_raw.py
when historical_ledger.csv is fresh but running_balance.json /
monthly_analysis_history.json are empty.

For each month found in the ledger:
  • Calls FinancialAnalystAgent.generate_monthly_story()
  • Saves the story narrative to data/processed/stories/<month>.md
  • Updates running_balance.json + monthly_analysis_history.json
    automatically (handled inside generate_monthly_story).
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from tools.analyst_agent import FinancialAnalystAgent

LEDGER = Path('data/processed/historical_ledger.csv')
STORIES_DIR = Path('data/processed/stories')
STORIES_DIR.mkdir(parents=True, exist_ok=True)

LANG = 'he'

if not LEDGER.exists():
    print(f"❌ {LEDGER} not found — run rebuild_from_raw.py first.")
    sys.exit(1)

df = pd.read_csv(LEDGER)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
df = df.dropna(subset=['Date', 'Amount'])
df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)

if 'Excluded' not in df.columns:
    df['Excluded'] = False

months = sorted(df['Month_Year'].unique())
print(f"\n📅 Found {len(months)} months in the ledger: {months}\n")

agent = FinancialAnalystAgent()

for month in months:
    print(f"\n{'='*70}")
    print(f"🤖 Generating story for {month}")
    print('='*70)

    month_df = df[df['Month_Year'] == month].copy()
    print(f"   Rows in this month: {len(month_df)}")

    story = agent.generate_monthly_story(month_df, month_year=month, lang=LANG)

    story_file = STORIES_DIR / f'{month}.md'
    story_file.write_text(story, encoding='utf-8')
    print(f"\n   ✅ Story saved: {story_file}")

print(f"\n{'='*70}")
print("✅ All months processed.")
print(f"   Stories saved in: {STORIES_DIR}")
print("   running_balance.json + monthly_analysis_history.json updated.")
print('='*70)
