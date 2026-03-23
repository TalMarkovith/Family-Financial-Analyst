"""
Quick Cleanup - Remove December 2025 data for fresh demo recording
"""

import json
import os
import pandas as pd

def cleanup_december():
    """Remove December 2025 from all data files"""
    
    print("="*70)
    print("🧹 CLEANING DECEMBER 2025 DATA")
    print("="*70)
    
    # 1. Clean running_balance.json
    balance_file = "data/processed/running_balance.json"
    if os.path.exists(balance_file):
        with open(balance_file, 'r') as f:
            balance = json.load(f)
        
        if '2025-12' in balance.get('monthly_breakdown', {}):
            dec_data = balance['monthly_breakdown']['2025-12']
            
            # Subtract December values
            balance['total_income'] -= dec_data.get('income', 0)
            balance['total_expenses'] -= dec_data.get('expenses', 0)
            balance['total_investments'] -= dec_data.get('investments', 0)
            balance['total_net_savings'] -= dec_data.get('net_savings', 0)
            
            # Remove from lists
            del balance['monthly_breakdown']['2025-12']
            balance['months_analyzed'] = [m for m in balance['months_analyzed'] if m != '2025-12']
            
            with open(balance_file, 'w', encoding='utf-8') as f:
                json.dump(balance, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Removed December from running_balance.json")
        else:
            print(f"ℹ️  No December in running_balance.json")
    
    # 2. Clean monthly_analysis_history.json
    analysis_file = "data/processed/monthly_analysis_history.json"
    if os.path.exists(analysis_file):
        with open(analysis_file, 'r') as f:
            analysis = json.load(f)
        
        if '2025-12' in analysis:
            del analysis['2025-12']
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Removed December from monthly_analysis_history.json")
        else:
            print(f"ℹ️  No December in monthly_analysis_history.json")
    
    # 3. Clean historical_ledger.csv
    ledger_file = "data/processed/historical_ledger.csv"
    if os.path.exists(ledger_file):
        df = pd.read_csv(ledger_file)
        
        if len(df) > 0:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Count December entries
            dec_count = len(df[(df['Date'].dt.year == 2025) & (df['Date'].dt.month == 12)])
            
            if dec_count > 0:
                # Remove December 2025
                df_clean = df[~((df['Date'].dt.year == 2025) & (df['Date'].dt.month == 12))]
                
                # Convert date back to string format without time
                df_clean['Date'] = df_clean['Date'].dt.strftime('%Y-%m-%d')
                df_clean.to_csv(ledger_file, index=False)
                print(f"✅ Removed {dec_count} December transactions from historical_ledger.csv")
            else:
                print(f"ℹ️  No December transactions in historical_ledger.csv")
        else:
            print(f"ℹ️  Historical ledger is empty")
    
    print("\n" + "="*70)
    print("✨ DECEMBER CLEANUP COMPLETE!")
    print("="*70)
    print("\n🎬 Ready for fresh demo recording!")
    print("\nYou can now:")
    print("1. Select December 2025 in the app")
    print("2. Upload the 3 December files")
    print("3. Record your demo with fresh data!")
    print("="*70)

if __name__ == "__main__":
    cleanup_december()
