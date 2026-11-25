"""
Tests for the shared month calculation (tools/month_totals.py).

Synthetic rows only. The key rule: a refund reduces spending in its category;
it is not income. Before this, a ₪8,080 charge refunded the same month showed
as ₪8,080 of spending plus ₪8,080 of income, and the history chart (which used
abs()) showed ₪16,160 of spending.
"""
import pandas as pd
import pytest

from tools.month_totals import compute_month_totals, split_month, net_spending_by


def _df(rows):
    return pd.DataFrame(rows, columns=['Description', 'Amount', 'Category', 'Sub_Category', 'Excluded'])


def test_refund_nets_against_its_category_not_income():
    df = _df([
        ('Salary', 20000.0, 'Income', 'Tal_Salary', False),
        ('Furniture shop', -8080.0, 'Variable_Daily', 'Home_Furniture_Decor', False),
        ('Furniture shop', 8080.0, 'Variable_Daily', 'Home_Furniture_Decor', False),
        ('Supermarket', -500.0, 'Food', 'Groceries_Supermarket', False),
    ])
    t = compute_month_totals(df)
    assert t['income'] == 20000.0
    assert t['expenses'] == 500.0
    assert t['refunds'] == 8080.0
    assert t['net_savings'] == 19500.0
    _, spending, _ = split_month(df)
    by_cat = net_spending_by(spending, 'Category')
    assert by_cat['Variable_Daily'] == 0.0
    assert by_cat['Food'] == 500.0


def test_excluded_rows_are_ignored_including_string_flags():
    # CSV round-trips can turn the flag into the string 'True'
    df = _df([
        ('Salary', 10000.0, 'Income', 'Tal_Salary', False),
        ('Card settlement', 7790.84, 'Variable_Daily', 'General_Shopping', 'True'),
        ('Rent', -5000.0, 'Housing_Fixed', 'Rent_Mortgage', None),
    ])
    t = compute_month_totals(df)
    assert t['income'] == 10000.0
    assert t['expenses'] == 5000.0


def test_investments_are_neither_income_nor_expense():
    df = _df([
        ('Salary', 10000.0, 'Income', 'Tal_Salary', False),
        ('Brokerage transfer', -3000.0, 'Investments', 'Savings_Analyst_Brokerage', False),
        ('אנליסט קופת גמל', -1000.0, 'Variable_Daily', 'General_Shopping', False),
        ('Groceries', -2000.0, 'Food', 'Groceries_Supermarket', False),
    ])
    t = compute_month_totals(df)
    assert t['investments'] == 4000.0
    assert t['expenses'] == 2000.0
    assert t['net_savings'] == 8000.0
    assert t['savings_rate'] == pytest.approx(80.0)


def test_income_categorised_benefit_counts_as_income():
    df = _df([
        ('Child allowance', 115.0, 'Income', 'Other_Income_Bit', False),
        ('Same benefit, wrong category', 50.0, 'Insurance_Health', 'Insurances', False),
    ])
    t = compute_month_totals(df)
    assert t['income'] == 115.0
    # Mis-categorised money in reduces spending instead; net savings is unchanged
    assert t['expenses'] == -50.0
    assert t['net_savings'] == 165.0


def test_missing_excluded_column_is_fine():
    df = pd.DataFrame({'Description': ['a'], 'Amount': [-10.0], 'Category': ['Food'], 'Sub_Category': ['x']})
    assert compute_month_totals(df)['expenses'] == 10.0
