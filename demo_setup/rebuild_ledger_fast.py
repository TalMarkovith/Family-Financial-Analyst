#!/usr/bin/env python3
"""
Fast rebuild: Load demo CSVs and add to historical ledger.
We'll load the pre-classified CSVs directly (they already have Category/Sub_Category).
"""

import os
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DEMO_DIR = PROJECT_ROOT / "data" / "demo"
LEDGER_FILE = PROJECT_ROOT / "data" / "processed" / "historical_ledger.csv"

def main():
    print("🔧 FAST REBUILD: Loading pre-classified demo data")
    print("=" * 80)
    
    # Check if demo CSVs have Category column (they should from generation)
    sample_file = DEMO_DIR / "2025-01_Max.csv"
    if sample_file.exists():
        sample_df = pd.read_csv(sample_file)
        print(f"📋 Sample columns: {list(sample_df.columns)}")
        
        if 'Category' not in sample_df.columns:
            print("\n⚠️  Demo files don't have Category column!")
            print("   These files need to be re-classified.")
            print("   Aborting to avoid creating incomplete ledger.")
            return
    
    # Load all demo CSV files for Jan-Nov 2025
    all_dfs = []
    for month in range(1, 12):  # Jan-Nov
        month_str = f"2025-{month:02d}"
        for source in ["Max", "Isracard", "Bank_Discount"]:
            file_path = DEMO_DIR / f"{month_str}_{source}.csv"
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    
                    # Check if it has the required columns
                    required = ['Date', 'Description', 'Amount', 'Owner', 'Source', 'Category', 'Sub_Category']
                    if all(col in df.columns for col in required):
                        all_dfs.append(df)
                        print(f"   ✓ Loaded {file_path.name}: {len(df)} transactions")
                    else:
                        # File doesn't have classifications, skip it
                        print(f"   ⚠️  Skipping {file_path.name}: missing Category/Sub_Category")
                except Exception as e:
                    print(f"   ✗ Error loading {file_path.name}: {e}")
    
    if not all_dfs:
        print("\n❌ No valid classified data found!")
        print("   The demo CSV files need to have Category and Sub_Category columns.")
        return
    
    # Combine all
    print(f"\n📦 Combining {len(all_dfs)} files...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['Date', 'Description', 'Amount', 'Owner'])
    
    # Ensure Date column is properly formatted
    combined_df['Date'] = pd.to_datetime(combined_df['Date']).dt.strftime('%Y-%m-%d')
    
    # Sort by date
    combined_df = combined_df.sort_values('Date')
    
    print(f"   Total unique transactions: {len(combined_df)}")
    print(f"   Date range: {combined_df['Date'].min()} to {combined_df['Date'].max()}")
    print(f"\n📊 Category breakdown:")
    print(combined_df['Category'].value_counts())
    
    # Save
    print(f"\n💾 Saving to {LEDGER_FILE}...")
    os.makedirs(LEDGER_FILE.parent, exist_ok=True)
    combined_df.to_csv(LEDGER_FILE, index=False, encoding='utf-8-sig')
    
    print("\n✨ HISTORICAL LEDGER CREATED! ✨")
    print("=" * 80)
    print(f"📊 Total transactions: {len(combined_df)}")
    print(f"📁 Saved to: {LEDGER_FILE}")
    print("\n🔄 Refresh your browser to see updated charts!")

if __name__ == "__main__":
    main()
