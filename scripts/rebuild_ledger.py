"""
Rebuild Historical Ledger - Load all 2025 demo data into historical_ledger.csv
This ensures the visualizations show the full year.
"""

import pandas as pd
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix SSL certificates
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

from tools.classify_dataframe import classify_dataframe

def rebuild_ledger_for_months(start_month=1, end_month=11):
    """Rebuild historical ledger for specified months"""
    
    print("="*70)
    print(f"📊 REBUILDING HISTORICAL LEDGER (Months {start_month}-{end_month})")
    print("="*70)
    
    demo_dir = 'data/demo'
    all_transactions = []
    
    for month in range(start_month, end_month + 1):
        month_str = f"2025-{month:02d}"
        print(f"\n📅 Processing {month_str}...")
        
        # Find files for this month
        files = []
        for source in ['Max', 'Isracard', 'Bank_Discount']:
            filename = f"{month_str}_{source}.csv"
            filepath = os.path.join(demo_dir, filename)
            if os.path.exists(filepath):
                files.append(filepath)
        
        if not files:
            print(f"  ⚠️  No files found for {month_str}")
            continue
        
        # Load and combine
        dfs = []
        for file in files:
            df = pd.read_csv(file)
            dfs.append(df)
        
        combined = pd.concat(dfs, ignore_index=True)
        print(f"  ✓ Loaded {len(combined)} transactions")
        
        # Classify
        classified_df, _ = classify_dataframe(combined)
        
        # Add Month_Year column
        classified_df['Date'] = pd.to_datetime(classified_df['Date'])
        classified_df['Year'] = classified_df['Date'].dt.year
        classified_df['Month'] = classified_df['Date'].dt.month
        classified_df['Day'] = classified_df['Date'].dt.day
        
        all_transactions.append(classified_df)
        print(f"  ✓ Classified and added to ledger")
    
    # Combine all months
    if all_transactions:
        full_ledger = pd.concat(all_transactions, ignore_index=True)
        
        # Save to historical_ledger.csv
        ledger_file = 'data/processed/historical_ledger.csv'
        
        # If December exists, load it and append
        if os.path.exists(ledger_file):
            existing = pd.read_csv(ledger_file)
            existing['Date'] = pd.to_datetime(existing['Date'])
            
            # Only keep December from existing
            dec_data = existing[(existing['Year'] == 2025) & (existing['Month'] == 12)]
            
            if len(dec_data) > 0:
                print(f"\n✓ Found {len(dec_data)} December transactions, will append")
                full_ledger = pd.concat([full_ledger, dec_data], ignore_index=True)
        
        # Sort by date
        full_ledger = full_ledger.sort_values('Date').reset_index(drop=True)
        
        # Save
        full_ledger.to_csv(ledger_file, index=False)
        
        print(f"\n" + "="*70)
        print(f"✅ LEDGER REBUILT!")
        print(f"="*70)
        print(f"   Total transactions: {len(full_ledger)}")
        print(f"   Months: {sorted(full_ledger['Month'].unique())}")
        print(f"   Date range: {full_ledger['Date'].min()} to {full_ledger['Date'].max()}")
        print("="*70)
        print("\n💡 Now the visualizations will show the full year!")
        print("   Refresh your browser to see the updated charts.")
        print("="*70)
    else:
        print("\n❌ No transactions found!")

if __name__ == "__main__":
    rebuild_ledger_for_months(1, 11)
