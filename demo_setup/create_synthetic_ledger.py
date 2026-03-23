#!/usr/bin/env python3
"""
Create a synthetic historical_ledger.csv from running_balance.json
This creates monthly summary entries that work with the visualization code.
"""

import json
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RUNNING_BALANCE_FILE = PROJECT_ROOT / "data" / "processed" / "running_balance.json"
LEDGER_FILE = PROJECT_ROOT / "data" / "processed" / "historical_ledger.csv"

def main():
    print("🔧 Creating synthetic historical ledger from running_balance.json")
    print("=" * 80)
    
    # Load running_balance.json
    with open(RUNNING_BALANCE_FILE, 'r', encoding='utf-8') as f:
        balance_data = json.load(f)
    
    months = balance_data['months_analyzed']
    monthly_breakdown = balance_data['monthly_breakdown']
    
    print(f"📅 Found {len(months)} months: {', '.join(months)}")
    
    # Create synthetic transactions for each month
    transactions = []
    
    for month in months:
        if month not in monthly_breakdown:
            continue
            
        data = monthly_breakdown[month]
        year, month_num = month.split('-')
        
        # Create income transaction
        if data['income'] > 0:
            transactions.append({
                'Date': f"{year}-{month_num}-15",  # Mid-month
                'Description': 'משכורות חודשיות',
                'Amount': data['income'],
                'Owner': 'Shared',
                'Source': 'Salary',
                'Category': 'Income',
                'Sub_Category': 'Salary'
            })
        
        # Create expense transaction
        if data['expenses'] > 0:
            transactions.append({
                'Date': f"{year}-{month_num}-15",
                'Description': 'הוצאות חודשיות',
                'Amount': -data['expenses'],  # Negative for expenses
                'Owner': 'Shared',
                'Source': 'Monthly',
                'Category': 'Expenses',
                'Sub_Category': 'General'
            })
        
        # Create investment transaction
        if data['investments'] > 0:
            transactions.append({
                'Date': f"{year}-{month_num}-15",
                'Description': 'אנליסט השקעות',
                'Amount': -data['investments'],  # Negative for investments
                'Owner': 'Shared',
                'Source': 'Analyst',
                'Category': 'Investments',
                'Sub_Category': 'Analyst_Brokerage'
            })
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    df = df.sort_values('Date')
    
    print(f"\n📊 Created {len(df)} synthetic transactions")
    print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
    
    # Save to ledger
    print(f"\n💾 Saving to {LEDGER_FILE}...")
    df.to_csv(LEDGER_FILE, index=False, encoding='utf-8-sig')
    
    print("\n✨ SYNTHETIC LEDGER CREATED! ✨")
    print("=" * 80)
    print("⚠️  NOTE: This ledger contains monthly summaries, not individual transactions")
    print("📊 It's sufficient for month-over-month visualizations")
    print("\n🎬 Restart Streamlit to see full year charts!")

if __name__ == "__main__":
    main()
