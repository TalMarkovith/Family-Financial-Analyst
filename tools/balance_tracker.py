# tools/balance_tracker.py
"""
Persistent running balance tracker.
Stores cumulative net savings across all analyzed months.
"""
import os
import json

BALANCE_FILE = "data/processed/running_balance.json"

def load_balance() -> dict:
    """Load the running balance data."""
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'total_net_savings': 0,
        'total_income': 0,
        'total_expenses': 0,
        'total_investments': 0,
        'months_analyzed': [],
        'monthly_breakdown': {}
    }

def update_balance(month_year: str, income: float, expenses: float, 
                   investments: float, net_savings: float) -> dict:
    """
    Update the running balance with a month's data.
    If the month was already analyzed, it replaces the old data.
    """
    data = load_balance()
    
    # If this month was already recorded, subtract old values first
    if month_year in data['monthly_breakdown']:
        old = data['monthly_breakdown'][month_year]
        data['total_net_savings'] -= old.get('net_savings', 0)
        data['total_income'] -= old.get('income', 0)
        data['total_expenses'] -= old.get('expenses', 0)
        data['total_investments'] -= old.get('investments', 0)
    else:
        data['months_analyzed'].append(month_year)
        data['months_analyzed'] = sorted(set(data['months_analyzed']))
    
    # Add new values
    data['total_net_savings'] += net_savings
    data['total_income'] += income
    data['total_expenses'] += expenses
    data['total_investments'] += investments
    
    # Store monthly breakdown
    data['monthly_breakdown'][month_year] = {
        'income': income,
        'expenses': expenses,
        'investments': investments,
        'net_savings': net_savings,
    }
    
    # Save
    os.makedirs(os.path.dirname(BALANCE_FILE), exist_ok=True)
    with open(BALANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data

def get_avg_savings_rate(data: dict) -> float:
    """Calculate average savings rate across all months."""
    if data['total_income'] > 0:
        return (data['total_net_savings'] / data['total_income']) * 100
    return 0
