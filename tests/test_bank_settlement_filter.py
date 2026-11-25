"""
Bank file: card settlements must be filtered, whatever their sign.

The card files already itemise every purchase, so a card settlement line in the
current account would double count. In Sept 2026 the bank showed a bare
'ישראכרט' CREDIT of +7,790.84 (a card refund passed back to the account). The
filter only knew 'ישראכרט חיוב', so it was counted as income. Synthetic data only.
"""
import datetime as dt

import pandas as pd

from tools.credit_card_ingestion import IngestionAgent


def _write_bank(path, rows):
    """Bank export layout: title rows, then a header row, then transactions."""
    header = ['תאריך', 'יום ערך', 'תיאור התנועה', '₪ זכות/חובה ', '₪ יתרה ', 'אסמכתה', 'עמלה', 'ערוץ ביצוע']
    top = [['עובר ושב'] + [None] * 7, [None] * 8, ['מסמך בדיקה'] + [None] * 7,
           ['שורת כותרת'] + [None] * 7, [None] * 8, ['תנועות אחרונות'] + [None] * 7, [None] * 8]
    body = [[dt.datetime(2026, 9, d), dt.datetime(2026, 9, d), desc, amt, 1000.0, 'x', None, 'y']
            for d, desc, amt in rows]
    pd.DataFrame(top + [header] + body).to_excel(path, header=False, index=False)


def test_bare_isracard_credit_and_debit_are_filtered(tmp_path):
    path = str(tmp_path / 'עובר ושב - בדיקה.xlsx')
    _write_bank(path, [
        (10, 'ישראכרט', 7790.84),          # bare, credit
        (10, 'ישראכרט חיוב', -779.41),     # classic debit
        (10, 'מקס איט פי', -500.00),
        (1, 'בנק פועלים משכורת', 15000.0),
        (10, 'דסק-משכנתא חיוב', -7032.59),  # real bank-only expense: keep
        (18, 'ביטוח לאומי - ילדים', 115.0),  # real bank-only income: keep
    ])
    df = IngestionAgent().parse_bank_discount(path)
    kept = sorted(df['Description'].tolist())
    assert kept == sorted(['דסק-משכנתא חיוב', 'ביטוח לאומי - ילדים'])
