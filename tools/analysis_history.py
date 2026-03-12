import os
import json
from datetime import datetime
import pandas as pd

ANALYSIS_HISTORY_FILE = "data/processed/monthly_analysis_history.json"

def save_monthly_analysis(month_year: str, income: float, expenses: float, net_savings: float, 
                         savings_rate: float, top_expenses: dict):
    """
    Save monthly analysis summary for future comparisons.
    
    Args:
        month_year: Month in format "YYYY-MM"
        income: Total income for the month
        expenses: Total expenses for the month
        net_savings: Net savings (income - expenses)
        savings_rate: Savings rate percentage
        top_expenses: Dictionary of top expense categories {category: amount}
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(ANALYSIS_HISTORY_FILE), exist_ok=True)
    
    # Load existing history
    history = load_analysis_history()
    
    # Add new analysis
    history[month_year] = {
        "month": month_year,
        "income": float(income),
        "expenses": float(expenses),
        "net_savings": float(net_savings),
        "savings_rate": float(savings_rate),
        "top_expenses": {k: float(v) for k, v in top_expenses.items()},
        "analyzed_at": datetime.now().isoformat()
    }
    
    # Save back to file
    with open(ANALYSIS_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved analysis for {month_year}")

def load_analysis_history() -> dict:
    """Load all historical monthly analyses."""
    if os.path.exists(ANALYSIS_HISTORY_FILE):
        with open(ANALYSIS_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_previous_month_analysis(current_month: str) -> dict:
    """
    Get the previous month's analysis for comparison.
    
    Args:
        current_month: Current month in format "YYYY-MM"
        
    Returns:
        Dictionary with previous month's analysis or None
    """
    history = load_analysis_history()
    
    # Parse current month
    year, month = map(int, current_month.split('-'))
    
    # Calculate previous month
    if month == 1:
        prev_month = f"{year-1}-12"
    else:
        prev_month = f"{year}-{month-1:02d}"
    
    return history.get(prev_month)

def get_comparison_insights(current_month: str, current_income: float, current_expenses: float, 
                           current_savings: float, current_rate: float) -> str:
    """
    Generate comparison text between current and previous month.
    
    Returns:
        Hebrew text with comparison insights
    """
    prev = get_previous_month_analysis(current_month)
    
    if not prev:
        return "זה החודש הראשון שאתם מנתחים - אין עדיין נתונים להשוואה."
    
    # Calculate changes
    income_change = current_income - prev['income']
    income_pct = (income_change / prev['income'] * 100) if prev['income'] > 0 else 0
    
    expenses_change = current_expenses - prev['expenses']
    expenses_pct = (expenses_change / prev['expenses'] * 100) if prev['expenses'] > 0 else 0
    
    savings_change = current_savings - prev['net_savings']
    savings_pct = (savings_change / prev['net_savings'] * 100) if prev['net_savings'] > 0 else 0
    
    rate_change = current_rate - prev['savings_rate']
    
    # Build comparison text
    comparison = f"\n\n### 📈 השוואה לחודש הקודם ({prev['month']})\n\n"
    
    # Income comparison
    if income_change > 0:
        comparison += f"💰 **הכנסות:** עלו ב-₪{income_change:,.0f} ({income_pct:+.1f}%)\n\n"
    elif income_change < 0:
        comparison += f"💰 **הכנסות:** ירדו ב-₪{abs(income_change):,.0f} ({income_pct:.1f}%)\n\n"
    else:
        comparison += f"💰 **הכנסות:** זהות לחודש שעבר\n\n"
    
    # Expenses comparison
    if expenses_change > 0:
        comparison += f"💳 **הוצאות:** עלו ב-₪{expenses_change:,.0f} ({expenses_pct:+.1f}%) ⚠️\n\n"
    elif expenses_change < 0:
        comparison += f"💳 **הוצאות:** ירדו ב-₪{abs(expenses_change):,.0f} ({abs(expenses_pct):.1f}%) ✅\n\n"
    else:
        comparison += f"💳 **הוצאות:** זהות לחודש שעבר\n\n"
    
    # Savings comparison
    if savings_change > 0:
        comparison += f"🎯 **חיסכון:** עלה ב-₪{savings_change:,.0f} ({savings_pct:+.1f}%) 🎉\n\n"
    elif savings_change < 0:
        comparison += f"🎯 **חיסכון:** ירד ב-₪{abs(savings_change):,.0f} ({abs(savings_pct):.1f}%) 📉\n\n"
    else:
        comparison += f"🎯 **חיסכון:** זהה לחודש שעבר\n\n"
    
    # Savings rate comparison
    if rate_change > 0:
        comparison += f"📊 **שיעור חיסכון:** עלה ב-{rate_change:+.1f}% (מ-{prev['savings_rate']:.1f}% ל-{current_rate:.1f}%) 👏\n\n"
    elif rate_change < 0:
        comparison += f"📊 **שיעור חיסכון:** ירד ב-{abs(rate_change):.1f}% (מ-{prev['savings_rate']:.1f}% ל-{current_rate:.1f}%)\n\n"
    else:
        comparison += f"📊 **שיעור חיסכון:** יציב ב-{current_rate:.1f}%\n\n"
    
    return comparison
