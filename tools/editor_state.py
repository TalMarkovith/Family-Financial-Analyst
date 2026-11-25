"""Session-state hygiene for the raw-data editor.

The editor's widgets are keyed by row index (raw_type_<idx>, raw_cat_<idx>,
...). Streamlit keeps a widget's value in session state across reruns. When
the table is replaced (a save that deletes rows and renumbers the index, or a
different month loaded), old values stay attached to the old index numbers,
and the next save applies them to whichever row now holds that number. That
shifted categories by one row and flipped income/expense signs on Sept 2026.

Call reset_raw_editor_state() every time the editor's data is replaced.
"""

RAW_EDITOR_KEY_PREFIXES = ('raw_delete_', 'raw_type_', 'raw_cat_', 'raw_sub_')


def reset_raw_editor_state(state) -> int:
    """Drop every per-row editor widget value; return how many were dropped."""
    stale = [k for k in list(state.keys())
             if isinstance(k, str) and k.startswith(RAW_EDITOR_KEY_PREFIXES)]
    for k in stale:
        del state[k]
    if 'rows_to_delete' in state:
        state['rows_to_delete'] = set()
    return len(stale)
