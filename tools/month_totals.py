"""Single source of truth for how a month's income, expenses and savings are computed.

Sign convention in the ledger: negative = money out, positive = money in.

Rules:
- Rows marked Excluded ("don't count") are ignored everywhere.
- Investments: money out with Category 'Investments' (or the אנליסט keyword).
  They are wealth allocation, not consumption, so they are not expenses.
- Income: money in whose Category is Income (salaries, benefits, interest).
- Refunds: any other money in (a card refund, a returned purchase). A refund
  reduces spending in its own category. It is NOT income. Counting it as
  income inflated both income and expenses (e.g. a ₪8,080 charge that was
  refunded showed up as ₪8,080 of spending plus ₪8,080 of "income").
"""
import pandas as pd

INCOME_CATEGORIES = ('Income', 'הכנסות')
INVESTMENT_CATEGORIES = ('Investments', 'השקעות')
INVESTMENT_KEYWORD = 'אנליסט'


def _active(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'Excluded' not in df.columns:
        df['Excluded'] = False
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    excluded = df['Excluded'].fillna(False).astype(str).str.lower().isin(['true', '1'])
    return df[~excluded & df['Amount'].notna()]


def split_month(df: pd.DataFrame):
    """Return (income_df, spending_df, investments_df) for the active rows.

    spending_df holds expenses (negative) together with refunds (positive), so
    ``-spending_df['Amount'].sum()`` is net spending.
    """
    active = _active(df)
    is_invest = (active['Amount'] < 0) & (
        active['Category'].isin(INVESTMENT_CATEGORIES)
        | active['Description'].astype(str).str.contains(INVESTMENT_KEYWORD, na=False)
    )
    is_income = (active['Amount'] > 0) & active['Category'].isin(INCOME_CATEGORIES)
    investments_df = active[is_invest]
    income_df = active[is_income]
    spending_df = active[~is_invest & ~is_income & (active['Amount'] != 0)]
    return income_df, spending_df, investments_df


def net_spending_by(spending_df: pd.DataFrame, by) -> pd.Series:
    """Net spending (positive number) per group; refunds reduce their group."""
    if spending_df.empty:
        return pd.Series(dtype=float)
    return (-spending_df.groupby(by)['Amount'].sum()).sort_values(ascending=False)


def compute_month_totals(df: pd.DataFrame) -> dict:
    income_df, spending_df, investments_df = split_month(df)
    income = float(income_df['Amount'].sum())
    expenses = float(-spending_df['Amount'].sum())
    investments = float(-investments_df['Amount'].sum())
    net = income - expenses
    return {
        'income': round(income, 2),
        'expenses': round(expenses, 2),
        'investments': round(investments, 2),
        'refunds': round(float(spending_df.loc[spending_df['Amount'] > 0, 'Amount'].sum()), 2),
        'net_savings': round(net, 2),
        'savings_rate': (net / income * 100) if income > 0 else 0.0,
    }
