#!/usr/bin/env python3
"""
Rebuild historical_ledger.csv from demo data files (Jan-Nov 2025)
This reads the original CSV files and processes them into the ledger.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.classify_dataframe import classify_dataframe

DEMO_DIR = project_root / "data" / "demo"
LEDGER_FILE = project_root / "data" / "processed" / "historical_ledger.csv"

def load_month_data(year_month):
    """Load all CSV files for a given month"""
    month_files = [
        DEMO_DIR / f"{year_month}_Max.csv",
        DEMO_DIR / f"{year_month}_Isracard.csv",
        DEMO_DIR / f"{year_month}_Bank_Discount.csv"
    ]
    
    dfs = []
    for file in month_files:
        if file.exists():
            df = pd.read_csv(file)
            dfs.append(df)
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def main():
    print("🔧 REBUILDING HISTORICAL LEDGER FROM DEMO DATA")
    print("=" * 80)
    
    # Months to process (Jan-Nov 2025)
    months = [
        "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
        "2025-07", "2025-08", "2025-09", "2025-10", "2025-11"
    ]
    
    all_transactions = []
    
    for month in months:
        print(f"\n📅 Processing {month}...")
        
        # Load month data
        df = load_month_data(month)
        if df.empty:
            print(f"   ⚠️  No data found for {month}")
            continue
        
        print(f"   📊 Found {len(df)} transactions")
        
        # Classify the dataframe
        print(f"   🤖 Classifying...")
        classified_df = classify_dataframe(df)
        
        # Add to collection
        all_transactions.append(classified_df)
        print(f"   ✅ Classified and added to ledger")
    
    if not all_transactions:
        print("\n❌ No data to save!")
        return
    
    # Combine all months
    print(f"\n📦 Combining all transactions...")
    final_df = pd.concat(all_transactions, ignore_index=True)
    
    # Remove duplicates
    final_df = final_df.drop_duplicates(subset=['Date', 'Description', 'Amount', 'Owner'])
    
    print(f"   Total transactions: {len(final_df)}")
    print(f"   Date range: {final_df['Date'].min()} to {final_df['Date'].max()}")
    
    # Save to historical ledger
    print(f"\n💾 Saving to {LEDGER_FILE}...")
    os.makedirs(LEDGER_FILE.parent, exist_ok=True)
    final_df.to_csv(LEDGER_FILE, index=False, encoding='utf-8-sig')
    
    print("\n✨ HISTORICAL LEDGER REBUILT SUCCESSFULLY! ✨")
    print("=" * 80)
    print(f"📊 Total transactions: {len(final_df)}")
    print(f"📅 Months covered: {len(months)}")
    print(f"💾 Saved to: {LEDGER_FILE}")
    print("\n🎬 Ready for demo! Restart your Streamlit app to see the full year charts.")

if __name__ == "__main__":
    main()
