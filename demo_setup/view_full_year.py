"""
View Full Year Analysis - Shows cumulative data from all analyzed months
"""

import json
import os
import pandas as pd
from datetime import datetime

def view_full_year():
    """Display the full year analysis from running balance"""
    
    balance_file = "data/processed/running_balance.json"
    
    if not os.path.exists(balance_file):
        print("❌ No data found. Upload some months first!")
        return
    
    with open(balance_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if len(data.get('months_analyzed', [])) == 0:
        print("❌ No months have been analyzed yet!")
        return
    
    print("=" * 80)
    print("📊 FULL YEAR ANALYSIS")
    print("=" * 80)
    
    # Overall summary
    print(f"\n💰 CUMULATIVE TOTALS")
    print(f"   Months Analyzed: {len(data['months_analyzed'])}")
    print(f"   Period: {min(data['months_analyzed'])} to {max(data['months_analyzed'])}")
    print(f"\n   Total Income:        ₪{data['total_income']:>12,.2f}")
    print(f"   Total Expenses:      ₪{data['total_expenses']:>12,.2f}")
    print(f"   Total Investments:   ₪{data['total_investments']:>12,.2f}")
    print(f"   ─────────────────────────────────────")
    print(f"   Net Savings:         ₪{data['total_net_savings']:>12,.2f}")
    
    avg_savings_rate = (data['total_net_savings'] / data['total_income'] * 100) if data['total_income'] > 0 else 0
    print(f"   Average Savings Rate: {avg_savings_rate:>11.1f}%")
    
    # Monthly breakdown
    print(f"\n📅 MONTH-BY-MONTH BREAKDOWN")
    print(f"   {'Month':<12} {'Income':>12} {'Expenses':>12} {'Investments':>12} {'Net Savings':>12} {'Rate':>6}")
    print(f"   {'-'*78}")
    
    monthly = data.get('monthly_breakdown', {})
    for month in sorted(data['months_analyzed']):
        if month in monthly:
            m = monthly[month]
            rate = (m['net_savings'] / m['income'] * 100) if m['income'] > 0 else 0
            print(f"   {month:<12} ₪{m['income']:>10,.0f} ₪{m['expenses']:>10,.0f} "
                  f"₪{m['investments']:>10,.0f} ₪{m['net_savings']:>10,.0f} {rate:>5.1f}%")
    
    # Trends
    print(f"\n📈 TRENDS")
    if len(data['months_analyzed']) >= 2:
        months_list = sorted(data['months_analyzed'])
        first_month = monthly[months_list[0]]
        last_month = monthly[months_list[-1]]
        
        expense_change = last_month['expenses'] - first_month['expenses']
        expense_pct = (expense_change / first_month['expenses'] * 100) if first_month['expenses'] > 0 else 0
        
        savings_change = last_month['net_savings'] - first_month['net_savings']
        
        print(f"   First Month ({months_list[0]}): ₪{first_month['net_savings']:,.2f} savings")
        print(f"   Last Month ({months_list[-1]}):  ₪{last_month['net_savings']:,.2f} savings")
        print(f"   Change: ₪{savings_change:,.2f} ({'+' if savings_change > 0 else ''}{(savings_change/first_month['net_savings']*100 if first_month['net_savings'] != 0 else 0):.1f}%)")
        
        if expense_pct > 0:
            print(f"   ⚠️  Expenses increased by {expense_pct:.1f}% over time")
        elif expense_pct < 0:
            print(f"   ✅ Expenses decreased by {abs(expense_pct):.1f}% over time")
    
    # Best and worst months
    if len(monthly) > 0:
        print(f"\n🏆 HIGHLIGHTS")
        
        best_savings = max(monthly.items(), key=lambda x: x[1]['net_savings'])
        worst_savings = min(monthly.items(), key=lambda x: x[1]['net_savings'])
        
        print(f"   Best Savings Month:  {best_savings[0]} (₪{best_savings[1]['net_savings']:,.2f})")
        print(f"   Worst Savings Month: {worst_savings[0]} (₪{worst_savings[1]['net_savings']:,.2f})")
        
        best_rate_month = max(monthly.items(), 
                             key=lambda x: x[1]['net_savings']/x[1]['income'] if x[1]['income'] > 0 else 0)
        best_rate = (best_rate_month[1]['net_savings'] / best_rate_month[1]['income'] * 100) if best_rate_month[1]['income'] > 0 else 0
        print(f"   Best Savings Rate:   {best_rate_month[0]} ({best_rate:.1f}%)")
    
    print("\n" + "=" * 80)
    print("💡 TIP: Each time you analyze a new month, these totals update automatically!")
    print("=" * 80)


if __name__ == "__main__":
    view_full_year()
