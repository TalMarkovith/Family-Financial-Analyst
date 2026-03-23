"""
Pre-load Demo History - Load January-November 2025 into the system
This prepares the app for a December demo by loading 11 months of history.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix SSL certificates
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

from tools.credit_card_ingestion import IngestionAgent
from tools.classify_dataframe import classify_dataframe, save_approved_to_memory
from tools.analyst_agent import FinancialAnalystAgent
from tools.balance_tracker import update_balance


def load_month_data(year, month, demo_dir='data/demo', skip_if_exists=True):
    """Load and process data for a specific month"""
    
    month_str = f"{year}-{month:02d}"
    print(f"\n{'='*70}")
    print(f"📅 Processing {month_str}")
    print(f"{'='*70}")
    
    # Check if already processed
    if skip_if_exists:
        balance_file = "data/processed/running_balance.json"
        if os.path.exists(balance_file):
            import json
            with open(balance_file, 'r', encoding='utf-8') as f:
                balance = json.load(f)
            if month_str in balance.get('months_analyzed', []):
                print(f"⏭️  {month_str} already processed - skipping")
                return None
    
    # Find files for this month
    files = []
    for source in ['Max', 'Isracard', 'Bank_Discount']:
        filename = f"{month_str}_{source}.csv"
        filepath = os.path.join(demo_dir, filename)
        if os.path.exists(filepath):
            files.append(filepath)
    
    if not files:
        print(f"❌ No files found for {month_str}")
        return None
    
    print(f"📂 Found {len(files)} files:")
    for f in files:
        print(f"   - {os.path.basename(f)}")
    
    # Ingest files
    print(f"\n🔄 Ingesting files...")
    ingestion_agent = IngestionAgent()
    
    all_dfs = []
    for file in files:
        df = pd.read_csv(file)
        all_dfs.append(df)
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"✅ Combined {len(combined_df)} transactions")
    
    # Check for duplicates in historical ledger
    ledger_file = "data/processed/historical_ledger.csv"
    if os.path.exists(ledger_file):
        existing_ledger = pd.read_csv(ledger_file)
        # Check if any transactions from this month already exist
        existing_ledger['Date'] = pd.to_datetime(existing_ledger['Date'])
        month_matches = existing_ledger[
            (existing_ledger['Date'].dt.year == year) & 
            (existing_ledger['Date'].dt.month == month)
        ]
        if len(month_matches) > 0:
            print(f"⚠️  Warning: Found {len(month_matches)} existing transactions for {month_str} in ledger")
            response = input(f"   Skip this month to avoid duplicates? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                print(f"⏭️  Skipping {month_str}")
                return None
    
    # Classify transactions
    print(f"\n🤖 Classifying transactions...")
    classified_df, pending_saves = classify_dataframe(combined_df)
    
    # Count classifications
    memory_hits = len(classified_df[
        (classified_df['Category'] != 'Unknown') & 
        (classified_df['Category'] != 'Pending')
    ])
    
    print(f"✅ Classified {memory_hits}/{len(classified_df)} transactions from memory")
    
    # Save pending merchants to memory (auto-approve for demo)
    if pending_saves:
        print(f"\n💾 Saving {len(pending_saves)} new merchants to memory...")
        save_approved_to_memory(pending_saves)
    
    # Calculate financials
    income = classified_df[classified_df['Amount'] > 0]['Amount'].sum()
    
    # Separate investments from expenses
    investments_df = classified_df[
        (classified_df['Amount'] < 0) & 
        (
            (classified_df['Category'] == 'Investments') |
            (classified_df['Description'].str.contains('אנליסט', case=False, na=False))
        )
    ]
    
    expenses_df = classified_df[
        (classified_df['Amount'] < 0) & 
        (~classified_df.index.isin(investments_df.index))
    ]
    
    expenses = expenses_df['Amount'].abs().sum()
    investments = investments_df['Amount'].abs().sum()
    net_savings = income - expenses
    savings_rate = (net_savings / income * 100) if income > 0 else 0
    
    print(f"\n💰 Financial Summary:")
    print(f"   Income:      ₪{income:>10,.2f}")
    print(f"   Expenses:    ₪{expenses:>10,.2f}")
    print(f"   Investments: ₪{investments:>10,.2f}")
    print(f"   Net Savings: ₪{net_savings:>10,.2f} ({savings_rate:.1f}%)")
    
    # Update balance tracker
    update_balance(month_str, income, expenses, investments, net_savings)
    
    # Generate analyst story and save to history
    print(f"\n📝 Generating financial analysis...")
    analyst = FinancialAnalystAgent()
    story = analyst.generate_monthly_story(classified_df, month_year=month_str, lang='he')
    
    print(f"✅ Analysis complete and saved to history")
    
    return {
        'month': month_str,
        'transactions': len(classified_df),
        'income': income,
        'expenses': expenses,
        'investments': investments,
        'net_savings': net_savings,
        'savings_rate': savings_rate
    }


def main():
    """Load January through November 2025"""
    
    print("="*70)
    print("🎬 PRE-LOADING DEMO HISTORY (JAN-NOV 2025)")
    print("="*70)
    print("\nThis will load 11 months of data into your system.")
    print("After this, you can demo December with rich historical context!")
    
    # Check if data already exists
    balance_file = "data/processed/running_balance.json"
    if os.path.exists(balance_file):
        import json
        with open(balance_file, 'r', encoding='utf-8') as f:
            balance = json.load(f)
        existing_months = [m for m in balance.get('months_analyzed', []) if m.startswith('2025')]
        if existing_months:
            print(f"\n⚠️  Found existing 2025 data: {len(existing_months)} months")
            print(f"   Months: {', '.join(sorted(existing_months))}")
            print(f"\n💡 To start fresh, first run:")
            print(f"   python scripts/cleanup_demo_data.py")
            print(f"\n   The script will skip already-processed months.")
    
    print()
    response = input("Continue with pre-load? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n❌ Cancelled")
        return
    
    results = []
    
    # Load months 1-11
    for month in range(1, 12):  # January (1) through November (11)
        try:
            result = load_month_data(2025, month)
            if result:
                results.append(result)
        except Exception as e:
            print(f"\n❌ Error processing month {month}: {e}")
            import traceback
            traceback.print_exc()
            response = input("\nContinue with next month? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                break
    
    # Summary
    print("\n" + "="*70)
    print("✨ PRE-LOAD COMPLETE!")
    print("="*70)
    
    if results:
        print(f"\n📊 LOADED {len(results)} MONTHS:")
        print(f"\n   {'Month':<10} {'Transactions':>12} {'Income':>12} {'Expenses':>12} {'Net Savings':>12} {'Rate':>6}")
        print(f"   {'-'*70}")
        
        total_income = 0
        total_expenses = 0
        total_investments = 0
        total_savings = 0
        
        for r in results:
            print(f"   {r['month']:<10} {r['transactions']:>12} "
                  f"₪{r['income']:>10,.0f} ₪{r['expenses']:>10,.0f} "
                  f"₪{r['net_savings']:>10,.0f} {r['savings_rate']:>5.1f}%")
            total_income += r['income']
            total_expenses += r['expenses']
            total_investments += r['investments']
            total_savings += r['net_savings']
        
        print(f"   {'-'*70}")
        print(f"   {'TOTAL':<10} {sum(r['transactions'] for r in results):>12} "
              f"₪{total_income:>10,.0f} ₪{total_expenses:>10,.0f} "
              f"₪{total_savings:>10,.0f} {(total_savings/total_income*100):>5.1f}%")
    
    print("\n" + "="*70)
    print("🎯 READY FOR DECEMBER DEMO!")
    print("="*70)
    print("\n📖 DEMO INSTRUCTIONS:")
    print("1. Run: streamlit run app.py")
    print("2. Select 'December 2025'")
    print("3. Enter income (Tal: ₪22,000, Reut: ₪18,000)")
    print("4. Upload December files from data/demo/:")
    print("   - 2025-12_Max.csv")
    print("   - 2025-12_Isracard.csv")
    print("   - 2025-12_Bank_Discount.csv")
    print("5. Click 'Run Financial Analyst Agent 🚀'")
    print("\n✨ You'll see:")
    print("   - Instant classification (all merchants known!)")
    print("   - Rich month-over-month comparison")
    print("   - Full year trends and insights")
    print("   - 11 months of historical context")
    print("\n💡 Perfect for showing the power of the learning system!")
    print("="*70)


if __name__ == "__main__":
    main()
