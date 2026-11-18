# pages/2_💼_Investments.py
"""
Investments — a READ-ONLY view of the family's long-term savings and brokerage account.

The data lives in a separate project (tal-reut-investment), which owns it and
builds `portfolio_summary.json` from its own source file. This page only reads
that summary: it never writes to it and never stores account or ID numbers.

Location: env var INVESTMENTS_SUMMARY_PATH, else the default path below.
"""
import json
import logging
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DEFAULT_PATH = Path.home() / "projects" / "tal-reut-investment" / "03_ניתוח" / "portfolio_summary.json"
REQUIRED_KEYS = {"schema", "as_of", "rows", "by_cat", "by_prov", "by_owner", "total", "exposure", "holdings", "insurance"}
log = logging.getLogger("investments_page")

st.set_page_config(page_title="Investments", page_icon="💼", layout="wide")
if "lang" not in st.session_state:
    st.session_state.lang = "he"
L = st.session_state.lang
_dir = "rtl" if L == "he" else "ltr"

T = {
    "he": {
        "title": "💼 השקעות וחסכונות", "subtitle": "פנסיה, גמל, השתלמות ותיק מסחר — תצוגה לקריאה בלבד",
        "missing": "לא נמצא קובץ נתוני ההשקעות. הריצו `python3 scripts/build_all.py` בפרויקט tal-reut-investment.",
        "invalid": "קובץ נתוני ההשקעות לא תקין. בנו אותו מחדש עם scripts/build_all.py.",
        "stale": "נתוני פנסיה/גמל/השתלמות נכונים ל־{inst}; תיק המסחר נכון ל־{trd}.",
        "k_total": "סך הנכסים", "k_fee": "דמי ניהול בשנה (הערכה)", "k_dep": "הפקדות חודשיות",
        "k_ins": "פרמיות ביטוח בחודש (ידוע)",
        "group": "קיבוץ", "g_cat": "סוג מוצר", "g_prov": "גוף מנהל", "g_owner": "בעלים",
        "where": "איפה הכסף נמצא", "fees": "דמי ניהול בשנה", "exposure": "חשיפה לפי סוג נכס (בקירוב)",
        "t_sum": "📊 סיכום", "t_trade": "📈 תיק מסחר", "t_rows": "🗂️ כל המוצרים", "t_ins": "🛡️ ביטוחים",
        "name": "שם", "balance": "יתרה", "share": "% מהנכסים", "deposit": "הפקדה חודשית",
        "fee": "₪ בשנה", "rate": "% מהיתרה", "count": "מוצרים",
    },
    "en": {
        "title": "💼 Investments & Savings", "subtitle": "Pension, provident, study funds and brokerage — read-only",
        "missing": "Investments data file not found. Run `python3 scripts/build_all.py` in tal-reut-investment.",
        "invalid": "Investments data file is invalid. Rebuild it with scripts/build_all.py.",
        "stale": "Pension/provident data as of {inst}; brokerage as of {trd}.",
        "k_total": "Total assets", "k_fee": "Annual fees (est.)", "k_dep": "Monthly deposits",
        "k_ins": "Monthly insurance (known)",
        "group": "Group by", "g_cat": "Product type", "g_prov": "Provider", "g_owner": "Owner",
        "where": "Where the money is", "fees": "Annual fees", "exposure": "Exposure by asset (approx.)",
        "t_sum": "📊 Summary", "t_trade": "📈 Brokerage", "t_rows": "🗂️ All products", "t_ins": "🛡️ Insurance",
        "name": "Name", "balance": "Balance", "share": "% of assets", "deposit": "Monthly deposit",
        "fee": "₪ / year", "rate": "% of balance", "count": "Products",
    },
}[L]

st.markdown(
    f"""<style>
    .stApp {{ background: #1f2347; }}
    .main .block-container {{ direction: {_dir}; max-width: 1300px; color: #e8e8f0; }}
    .stApp h1, .stApp h2, .stApp h3 {{ color: #fff !important; }}
    .stApp [data-testid="stCaptionContainer"] p {{ color: #b8bce0 !important; }}
    .stApp [data-baseweb="tab"] p {{ color: #c5c8e6 !important; }}
    .stApp [data-baseweb="tab"][aria-selected="true"] p {{ color: #fff !important; }}
    .stApp [data-testid="stMainBlockContainer"] {{ direction: {_dir}; }}
    label, div[role="radiogroup"] label p {{ color: #d0d3ee !important; }}
    div[data-testid="stMetric"] {{ background: #262a4d; border-radius: 12px; padding: 14px 18px; border: 1px solid #34395e; }}
    div[data-testid="stMetricLabel"] p {{ color: #b8bce0 !important; }}
    div[data-testid="stMetricValue"] {{ color: #fff; }}
    .stDataFrame {{ direction: ltr; }}
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_summary(path: str):
    """Read and validate the summary file. Returns (data, error_key)."""
    p = Path(path).expanduser()
    if not p.is_file():
        return None, "missing"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log.warning("investments summary unreadable")
        return None, "invalid"
    if not isinstance(data, dict) or not REQUIRED_KEYS <= data.keys() or data.get("schema") != 1:
        log.warning("investments summary failed schema check")
        return None, "invalid"
    return data, None


path = os.environ.get("INVESTMENTS_SUMMARY_PATH", str(DEFAULT_PATH))
data, err = load_summary(path)
log.info("investments page viewed (data loaded: %s)", err is None)

st.markdown(f"## {T['title']}")
st.caption(T["subtitle"])
if err:
    st.info(T[err])
    st.stop()

st.warning(T["stale"].format(inst=data["as_of"]["institutional"], trd=data["as_of"]["trading"]))

tot = data["total"]
shek = lambda v: f"₪{v:,.0f}"
k = st.columns(4)
k[0].metric(T["k_total"], shek(tot["balance"]))
k[1].metric(T["k_fee"], shek(tot["fee"]), delta=f"{tot['rate']:.2%}", delta_color="off")
k[2].metric(T["k_dep"], shek(tot["deposit"]))
k[3].metric(T["k_ins"], shek(data["ins_total"]))

st.markdown("---")
tab_sum, tab_trade, tab_rows, tab_ins = st.tabs([T["t_sum"], T["t_trade"], T["t_rows"], T["t_ins"]])

BAR = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
           margin=dict(l=10, r=10, t=40, b=10), showlegend=False,
           font_color="#d0d3ee", title_font_color="#ffffff")


def show(df: pd.DataFrame, money=(), pct=()):
    """Display-only table: format money/percent columns as text so they read the same everywhere."""
    out = df.copy()
    for c in money:
        out[c] = out[c].map(lambda v: "" if pd.isna(v) else f"₪{v:,.0f}")
    for c in pct:
        out[c] = out[c].map(lambda v: "" if pd.isna(v) else f"{v:.2%}")
    st.dataframe(out, hide_index=True, width="stretch")

with tab_sum:
    g = st.radio(T["group"], ["by_cat", "by_prov", "by_owner"], horizontal=True,
                 format_func=lambda x: T[{"by_cat": "g_cat", "by_prov": "g_prov", "by_owner": "g_owner"}[x]])
    df = pd.DataFrame(data[g]).sort_values("balance")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(df, x="balance", y="name", orientation="h", title=T["where"],
                     color_discrete_sequence=["#0984e3"], labels={"balance": "₪", "name": ""})
        fig.update_layout(**BAR)
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.bar(df.sort_values("fee"), x="fee", y="name", orientation="h", title=T["fees"],
                     color_discrete_sequence=["#0984e3"], labels={"fee": "₪", "name": ""},
                     hover_data={"rate": ":.2%"})
        fig.update_layout(**BAR)
        st.plotly_chart(fig, width="stretch")
    tbl = df.sort_values("balance", ascending=False).assign(share=lambda x: x["balance"] / tot["balance"])
    show(tbl[["name", "balance", "share", "deposit", "fee", "rate", "count"]].rename(columns={
            "name": T["name"], "balance": T["balance"], "share": T["share"], "deposit": T["deposit"],
            "fee": T["fee"], "rate": T["rate"], "count": T["count"]}),
         money=(T["balance"], T["deposit"], T["fee"]), pct=(T["share"], T["rate"]))
    ex = pd.DataFrame(data["exposure"]).sort_values("balance")
    fig = px.bar(ex, x="balance", y="name", orientation="h", title=T["exposure"],
                 color_discrete_sequence=["#0984e3"], labels={"balance": "₪", "name": ""})
    fig.update_layout(**BAR)
    st.plotly_chart(fig, width="stretch")

with tab_trade:
    h = pd.DataFrame(data["holdings"])
    h["return"] = h["pnl"] / h["cost"]
    h["weight"] = h["value"] / h["value"].sum()
    show(h[["name", "region", "qty", "cost", "pnl", "value", "return", "weight"]].sort_values("value", ascending=False),
         money=("cost", "pnl", "value"), pct=("return", "weight"))

with tab_rows:
    r = pd.DataFrame(data["rows"])
    show(r[["owner", "category", "provider", "track", "balance", "monthly_deposit", "fee_acc", "fee_dep",
            "annual_fee", "as_of"]].sort_values("balance", ascending=False),
         money=("balance", "monthly_deposit", "annual_fee"), pct=("fee_acc", "fee_dep"))

with tab_ins:
    st.dataframe(pd.DataFrame(data["insurance"]), hide_index=True, width="stretch")
