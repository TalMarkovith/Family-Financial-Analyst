#!/usr/bin/env python3
"""
Quick script: Build historical_ledger.csv from the demo data files.
This version processes ALL files at once without re-classification.
"""

import os
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DEMO_DIR = PROJECT_ROOT / "data" / "demo"
LEDGER_FILE = PROJECT_ROOT / "data" / "processed" / "historical_ledger.csv"

def main():
    print("🔧 QUICK REBUILD: Creating historical_ledger.csv from demo files")
    print("=" * 80)
    
    # Load all demo CSV files for Jan-Nov 2025
    all_files = []
    for month in range(1, 12):  # Jan-Nov
        month_str = f"2025-{month:02d}"
        for source in ["Max", "Isracard", "Bank_Discount"]:
            file_path = DEMO_DIR / f"{month_str}_{source}.csv"
            if file_path.exists():
                all_files.append(file_path)
    
    print(f"📂 Found {len(all_files)} CSV files")
    
    # Read all files
    dfs = []
    for file_path in all_files:
        try:
            df = pd.read_csv(file_path)
            # Ensure required columns exist
            required = ['Date', 'Description', 'Amount', 'Owner', 'Source']
            if all(col in df.columns for col in required):
                # Add Category and Sub_Category if not present
                if 'Category' not in df.columns:
                    df['Category'] = 'Uncategorized'
                if 'Sub_Category' not in df.columns:
                    df['Sub_Category'] = 'Unknown'
                    
                dfs.append(df)
                print(f"   ✓ Loaded {file_path.name}: {len(df)} transactions")
            else:
                print(f"   ✗ Skipping {file_path.name}: missing required columns")
        except Exception as e:
            print(f"   ✗ Error loading {file_path.name}: {e}")
    
    if not dfs:
        print("\n❌ No valid data found!")
        return
    
    # Combine all
    print(f"\n📦 Combining all transactions...")
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['Date', 'Description', 'Amount', 'Owner'])
    
    # Ensure Date column is properly formatted
    combined_df['Date'] = pd.to_datetime(combined_df['Date']).dt.strftime('%Y-%m-%d')
    
    # Sort by date
    combined_df = combined_df.sort_values('Date')
    
    print(f"   Total unique transactions: {len(combined_df)}")
    print(f"   Date range: {combined_df['Date'].min()} to {combined_df['Date'].max()}")
    
    # Save
    print(f"\n💾 Saving to {LEDGER_FILE}...")
    os.makedirs(LEDGER_FILE.parent, exist_ok=True)
    combined_df.to_csv(LEDGER_FILE, index=False, encoding='utf-8-sig')
    
    print("\n✨ HISTORICAL LEDGER CREATED! ✨")
    print("=" * 80)
    print(f"📊 Total transactions: {len(combined_df)}")
    print(f"📁 Saved to: {LEDGER_FILE}")
    print("\n🎬 Restart Streamlit to see full year charts!")

if __name__ == "__main__":
    main()
