"""
Tests for the raw-data editor's session-state reset (tools/editor_state.py).

Reproduces the Sept 2026 corruption without Streamlit: widget values keyed by
row index outlive a save that deletes a row and renumbers the table, so the
next save applies row N's old choice to the row that is now at index N.
"""
import pandas as pd

from tools.editor_state import reset_raw_editor_state


def _apply_category_widgets(df, state):
    """Mirror of the editor save loop: read raw_cat_<idx> for each row."""
    df = df.copy()
    for idx in df.index:
        new_cat = state.get(f"raw_cat_{idx}", '')
        if new_cat and new_cat != df.at[idx, 'Category']:
            df.at[idx, 'Category'] = new_cat
    return df


def _render_defaults(df, state):
    """Streamlit only sets a widget's default when its key is not in state."""
    for idx, row in df.iterrows():
        state.setdefault(f"raw_cat_{idx}", row['Category'])


def _table():
    return pd.DataFrame({'Description': ['rent', 'wolt', 'fuel'],
                         'Category': ['Housing_Fixed', 'Food_Delivery', 'Transportation']})


def test_without_reset_a_delete_shifts_categories():
    state = {}
    df = _table()
    _render_defaults(df, state)
    df = df.drop(index=[0]).reset_index(drop=True)  # delete 'rent', renumber
    _render_defaults(df, state)  # stale keys win: idx 0 keeps 'Housing_Fixed'
    shifted = _apply_category_widgets(df, state)
    assert shifted.loc[0, 'Category'] == 'Housing_Fixed'  # wolt became housing: the bug


def test_reset_after_replacing_the_table_keeps_categories():
    state = {'rows_to_delete': {0}, 'unrelated': 1}
    df = _table()
    _render_defaults(df, state)
    state['raw_type_0'] = 'income'
    df = df.drop(index=[0]).reset_index(drop=True)
    dropped = reset_raw_editor_state(state)
    assert dropped == 4
    assert state['rows_to_delete'] == set()
    assert state['unrelated'] == 1
    _render_defaults(df, state)
    kept = _apply_category_widgets(df, state)
    assert kept['Category'].tolist() == ['Food_Delivery', 'Transportation']
