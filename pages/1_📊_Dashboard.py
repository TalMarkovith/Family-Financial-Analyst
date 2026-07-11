# pages/1_📊_Dashboard.py
"""
Family Financial Dashboard — a READ-ONLY view of the full story.

Unlike app.py (which ingests files and runs the AI analyst), this page never
triggers an analysis. It only reads the already-produced artifacts
(historical_ledger.csv, running_balance.json, monthly stories) and lets you
explore the whole timeline: balances, trends, categories, and every transaction.
"""
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from markdown_it import MarkdownIt

from tools import dashboard_data as dd
from tools.translations import cat_display, sub_display

st.set_page_config(page_title="Financial Dashboard", page_icon="📊", layout="wide")

# ── Language (shared with app.py via session_state) ──
if "lang" not in st.session_state:
    st.session_state.lang = "he"

# ── Local translations for this page (keeps translations.py untouched) ──
DASH = {
    "he": {
        "title": "📊 לוח מחוונים משפחתי",
        "subtitle": "כל התמונה הפיננסית במקום אחד — ללא הרצת ניתוח חדש",
        "no_data": "עדיין אין נתונים. הריצו ניתוח בעמוד הראשי כדי לאכלס את לוח המחוונים.",
        "kpi_savings": "💰 חיסכון מצטבר (מזומן)",
        "kpi_income": 'סה"כ הכנסות',
        "kpi_expenses": 'סה"כ הוצאות',
        "kpi_invest": "💎 השקעות מצטברות",
        "kpi_wealth": "📈 סך הון שנצבר",
        "kpi_rate": "שיעור חיסכון ממוצע",
        "months_analyzed": "חודשים",
        "tab_trends": "📈 מגמות",
        "tab_categories": "🗂️ קטגוריות",
        "tab_story": "📖 הסיפור החודשי",
        "tab_txns": "🔎 טרנזקציות",
        # trends
        "wealth_title": "צבירת הון לאורך זמן",
        "wealth_cash": "חיסכון מצטבר (מזומן)",
        "wealth_invest": "השקעות מצטברות",
        "wealth_total": "סך הון",
        "ie_title": "הכנסות מול הוצאות",
        "income": "הכנסות",
        "expenses": "הוצאות",
        "net": "חיסכון נטו",
        "rate_title": "שיעור חיסכון חודשי",
        "rate": "שיעור חיסכון",
        "target": "יעד (20%)",
        "amount_axis": "סכום (₪)",
        "month_axis": "חודש",
        # categories
        "cat_level": "רמת פירוט",
        "level_cat": "קטגוריה ראשית",
        "level_sub": "תת-קטגוריה",
        "heatmap_title": "הוצאות לפי {level} וחודש",
        "fv_title": "הוצאות קבועות מול משתנות",
        "fixed": "קבועות (מחויבות)",
        "variable": "משתנות (ניתנות לשליטה)",
        "fixed_share": "אחוז קבועות",
        "merchants_title": "בתי עסק מובילים (סך הכל)",
        "merchant": "בית עסק",
        "total": 'סה"כ',
        "count": "מספר עסקאות",
        "avg": "ממוצע",
        "drill_title": "צלילה לקטגוריה",
        "pick_category": "בחרו קטגוריה",
        "cat_trend": "מגמת {cat} לאורך החודשים",
        "cat_txns": "עסקאות בקטגוריה זו",
        # anomalies
        "anom_title": "היכן החודש חורג מהממוצע",
        "anom_pick": "חודש להשוואה",
        "anom_this": "החודש",
        "anom_avg": "ממוצע שאר החודשים",
        "anom_delta": "פער",
        # story
        "story_pick": "בחרו חודש",
        "story_missing": "אין סיפור שמור לחודש זה.",
        # transactions
        "filters": "מסננים",
        "f_month": "חודש",
        "f_owner": "בעלים",
        "f_source": "מקור",
        "f_category": "קטגוריה",
        "f_search": "חיפוש בתיאור",
        "f_type": "סוג",
        "type_all": "הכל",
        "type_expense": "הוצאות",
        "type_income": "הכנסות",
        "show_excluded": 'כלול עסקאות מסומנות "לא לספור"',
        "rows_shown": "מוצגות {n} עסקאות · סכום נטו: ₪{sum:,.0f}",
        "download": "⬇️ הורדה כ-CSV",
        "col_date": "תאריך",
        "col_desc": "תיאור",
        "col_amount": "סכום",
        "col_owner": "בעלים",
        "col_source": "מקור",
        "col_category": "קטגוריה",
        "col_sub": "תת-קטגוריה",
        "col_excluded": "לא נספר",
    },
    "en": {
        "title": "📊 Family Financial Dashboard",
        "subtitle": "The full financial picture in one place — no new analysis required",
        "no_data": "No data yet. Run an analysis on the main page to populate the dashboard.",
        "kpi_savings": "💰 Cumulative Savings (cash)",
        "kpi_income": "Total Income",
        "kpi_expenses": "Total Expenses",
        "kpi_invest": "💎 Cumulative Investments",
        "kpi_wealth": "📈 Total Wealth Built",
        "kpi_rate": "Avg Savings Rate",
        "months_analyzed": "months",
        "tab_trends": "📈 Trends",
        "tab_categories": "🗂️ Categories",
        "tab_story": "📖 Monthly Story",
        "tab_txns": "🔎 Transactions",
        "wealth_title": "Wealth Accumulation Over Time",
        "wealth_cash": "Cumulative savings (cash)",
        "wealth_invest": "Cumulative investments",
        "wealth_total": "Total wealth",
        "ie_title": "Income vs Expenses",
        "income": "Income",
        "expenses": "Expenses",
        "net": "Net savings",
        "rate_title": "Monthly Savings Rate",
        "rate": "Savings rate",
        "target": "Target (20%)",
        "amount_axis": "Amount (₪)",
        "month_axis": "Month",
        "cat_level": "Detail level",
        "level_cat": "Main category",
        "level_sub": "Sub-category",
        "heatmap_title": "Spend by {level} and month",
        "fv_title": "Fixed vs Variable Spending",
        "fixed": "Fixed (committed)",
        "variable": "Variable (controllable)",
        "fixed_share": "Fixed share",
        "merchants_title": "Top Merchants (all-time)",
        "merchant": "Merchant",
        "total": "Total",
        "count": "# Txns",
        "avg": "Avg",
        "drill_title": "Category Drill-down",
        "pick_category": "Pick a category",
        "cat_trend": "{cat} trend across months",
        "cat_txns": "Transactions in this category",
        "anom_title": "Where This Month Deviates From Average",
        "anom_pick": "Month to compare",
        "anom_this": "This month",
        "anom_avg": "Avg of other months",
        "anom_delta": "Delta",
        "story_pick": "Pick a month",
        "story_missing": "No saved story for this month.",
        "filters": "Filters",
        "f_month": "Month",
        "f_owner": "Owner",
        "f_source": "Source",
        "f_category": "Category",
        "f_search": "Search description",
        "f_type": "Type",
        "type_all": "All",
        "type_expense": "Expenses",
        "type_income": "Income",
        "show_excluded": 'Include "don\'t count" transactions',
        "rows_shown": "Showing {n} transactions · net: ₪{sum:,.0f}",
        "download": "⬇️ Download CSV",
        "col_date": "Date",
        "col_desc": "Description",
        "col_amount": "Amount",
        "col_owner": "Owner",
        "col_source": "Source",
        "col_category": "Category",
        "col_sub": "Sub-category",
        "col_excluded": "Excluded",
    },
}


def d(key: str, **kw) -> str:
    L = st.session_state.lang
    text = DASH.get(L, DASH["en"]).get(key, key)
    return text.format(**kw) if kw else text


L = st.session_state.lang
is_rtl = L == "he"
_dir = "rtl" if is_rtl else "ltr"
_align = "right" if is_rtl else "left"

# ── Theme colours (match app.py) ──
C_PURPLE, C_TEAL, C_GREEN, C_RED, C_GOLD, C_BLUE = (
    "#6c5ce7", "#00b894", "#00ca72", "#e17055", "#ffd700", "#0984e3",
)

# ── RTL / styling ──
st.markdown(
    f"""
<style>
    /* Dark navy theme, scoped to this page (matches app.py's look) */
    .stApp {{ background: #1f2347; }}
    .main .block-container {{ direction: {_dir}; max-width: 1300px; color: #e8e8f0; }}
    .main .block-container p, .main .block-container li,
    .main .block-container span {{ color: #e8e8f0; }}
    .main .block-container h1, .main .block-container h2,
    .main .block-container h3, .main .block-container h4 {{ color: #ffffff !important; }}
    section[data-testid="stSidebar"] {{ direction: {_dir}; }}
    .stTabs [data-baseweb="tab-list"] {{ direction: {_dir}; }}
    .stTabs [data-baseweb="tab"] {{ color: #c5c8e6; }}
    .stDataFrame {{ direction: ltr; }}

    /* Widget labels stay light on the dark background */
    label, div[role="radiogroup"] label p {{ color: #d0d3ee !important; }}

    /* KPI cards */
    div[data-testid="stMetric"] {{
        background: #262a4d; border-radius: 12px; padding: 14px 18px;
        border: 1px solid #34395e;
    }}
    div[data-testid="stMetric"] label,
    div[data-testid="stMetricLabel"] p {{ color: #b8bce0 !important; }}
    div[data-testid="stMetricValue"] {{ color: #ffffff; }}
    div[data-testid="stMetricDelta"] {{ color: #9aa0d0; }}
    div[data-testid="stMetricLabel"] {{ direction: {_dir}; }}

    /* Monthly story card */
    .story-card {{
        direction: {_dir}; text-align: {_align};
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border-radius: 15px; padding: 8px 30px; margin: 12px 0;
        line-height: 1.9; font-size: 1.08em;
    }}
    .story-card h1, .story-card h2, .story-card h3 {{ color: {C_GOLD} !important; }}
    .story-card p, .story-card li, .story-card span {{ color: #ffffff !important; }}
    .story-card strong {{ color: {C_GOLD} !important; }}
    .story-card hr {{ border-color: rgba(255,255,255,0.25); }}
</style>
""",
    unsafe_allow_html=True,
)

# ── Header + language toggle ──
h1, h2 = st.columns([6, 1])
with h1:
    st.markdown(f"## {d('title')}")
    st.caption(d("subtitle"))
with h2:
    choice = st.selectbox(
        "🌐", ["עברית", "English"],
        index=0 if L == "he" else 1,
        key="lang_dashboard_page", label_visibility="collapsed",
    )
    new_lang = "he" if choice == "עברית" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

# ── Load everything (read-only) ──
ledger = dd.load_ledger()
summary = dd.monthly_summary()

if ledger.empty or summary.empty:
    st.info(d("no_data"))
    st.stop()

months = dd.available_months(ledger)


def fmt_shekel(v: float) -> str:
    return f"₪{v:,.0f}"


# ── KPI row ──
last = summary.iloc[-1]
avg_rate = summary["savings_rate"].mean()
k = st.columns(5)
k[0].metric(d("kpi_savings"), fmt_shekel(last["cum_net_savings"]))
k[1].metric(d("kpi_invest"), fmt_shekel(last["cum_investments"]))
k[2].metric(d("kpi_wealth"), fmt_shekel(last["cum_wealth"]))
k[3].metric(d("kpi_income"), fmt_shekel(summary["income"].sum()))
k[4].metric(
    d("kpi_rate"),
    f"{avg_rate:.1f}%",
    delta=f"{len(months)} {d('months_analyzed')}",
    delta_color="off",
)

st.markdown("---")

tab_trends, tab_cats, tab_story, tab_txns = st.tabs(
    [d("tab_trends"), d("tab_categories"), d("tab_story"), d("tab_txns")]
)

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — TRENDS
# ══════════════════════════════════════════════════════════════════════════
with tab_trends:
    # Wealth accumulation
    st.markdown(f"### {d('wealth_title')}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=summary["Month"], y=summary["cum_net_savings"], name=d("wealth_cash"),
        mode="lines+markers", stackgroup="one", line=dict(color=C_TEAL, width=0),
    ))
    fig.add_trace(go.Scatter(
        x=summary["Month"], y=summary["cum_investments"], name=d("wealth_invest"),
        mode="lines+markers", stackgroup="one", line=dict(color=C_PURPLE, width=0),
    ))
    fig.add_trace(go.Scatter(
        x=summary["Month"], y=summary["cum_wealth"], name=d("wealth_total"),
        mode="lines+markers+text", line=dict(color=C_GOLD, width=3),
        text=[fmt_shekel(v) for v in summary["cum_wealth"]], textposition="top center",
        textfont=dict(color=C_GOLD),
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=d("month_axis"), yaxis_title=d("amount_axis"),
        legend=dict(orientation="h", y=-0.2), margin=dict(l=0, r=0, t=10, b=0), height=380,
    )
    st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {d('ie_title')}")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=summary["Month"], y=summary["income"], name=d("income"), marker_color=C_TEAL))
        fig2.add_trace(go.Bar(x=summary["Month"], y=summary["expenses"], name=d("expenses"), marker_color=C_RED))
        fig2.add_trace(go.Scatter(
            x=summary["Month"], y=summary["net_savings"], name=d("net"),
            mode="lines+markers", line=dict(color=C_GOLD, width=3),
        ))
        fig2.update_layout(
            template="plotly_dark", barmode="group", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", yaxis_title=d("amount_axis"),
            legend=dict(orientation="h", y=-0.2), margin=dict(l=0, r=0, t=10, b=0), height=340,
        )
        st.plotly_chart(fig2, width="stretch")
    with c2:
        st.markdown(f"### {d('rate_title')}")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=summary["Month"], y=summary["savings_rate"], name=d("rate"),
            marker_color=C_PURPLE,
            text=[f"{v:.0f}%" for v in summary["savings_rate"]], textposition="outside",
        ))
        fig3.add_hline(
            y=20, line_dash="dash", line_color=C_GOLD,
            annotation_text=d("target"), annotation_position="top left",
        )
        fig3.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="%", legend=dict(orientation="h", y=-0.2),
            margin=dict(l=0, r=0, t=10, b=0), height=340,
        )
        st.plotly_chart(fig3, width="stretch")

# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — CATEGORIES
# ══════════════════════════════════════════════════════════════════════════
with tab_cats:
    level_label = st.radio(
        d("cat_level"), [d("level_cat"), d("level_sub")],
        horizontal=True, key="cat_level_radio",
    )
    level = "Category" if level_label == d("level_cat") else "Sub_Category"
    disp = cat_display if level == "Category" else sub_display

    pivot = dd.category_monthly(ledger, level=level)
    if not pivot.empty:
        st.markdown(f"### {d('heatmap_title', level=level_label)}")
        heat = pivot.copy()
        heat.index = [disp(i, L) for i in heat.index]
        fig_h = px.imshow(
            heat, text_auto=".0f", aspect="auto", color_continuous_scale="Purples",
            labels=dict(x=d("month_axis"), y="", color="₪"),
        )
        fig_h.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0), height=max(320, 26 * len(heat)),
        )
        st.plotly_chart(fig_h, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {d('fv_title')}")
        fv = dd.fixed_vs_variable(ledger)
        fig_fv = go.Figure()
        fig_fv.add_trace(go.Bar(x=fv["Month"], y=fv["Fixed"], name=d("fixed"), marker_color=C_PURPLE))
        fig_fv.add_trace(go.Bar(x=fv["Month"], y=fv["Variable"], name=d("variable"), marker_color=C_TEAL))
        fig_fv.add_trace(go.Scatter(
            x=fv["Month"], y=fv["fixed_share"], name=d("fixed_share"), yaxis="y2",
            mode="lines+markers+text", line=dict(color=C_GOLD, width=2),
            text=[f"{v:.0f}%" for v in fv["fixed_share"]], textposition="top center",
        ))
        fig_fv.update_layout(
            template="plotly_dark", barmode="stack", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", yaxis_title=d("amount_axis"),
            yaxis2=dict(overlaying="y", side="right", range=[0, 100], showgrid=False, title="%"),
            legend=dict(orientation="h", y=-0.2), margin=dict(l=0, r=0, t=10, b=0), height=360,
        )
        st.plotly_chart(fig_fv, width="stretch")
    with c2:
        st.markdown(f"### {d('merchants_title')}")
        mt = dd.merchant_totals(ledger, top_n=12)
        fig_m = px.bar(
            mt.sort_values("total"), x="total", y="Description", orientation="h",
            color="total", color_continuous_scale="Teal",
        )
        fig_m.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title=d("amount_axis"), yaxis_title="", coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0), height=360,
        )
        st.plotly_chart(fig_m, width="stretch")

    st.markdown("---")

    # Anomalies (only meaningful with >=2 months)
    if len(months) >= 2:
        st.markdown(f"### {d('anom_title')}")
        anom_month = st.selectbox(d("anom_pick"), months, index=len(months) - 1, key="anom_month")
        anom = dd.category_anomalies(ledger, anom_month)
        if not anom.empty:
            anom_disp = anom.copy()
            anom_disp["Category"] = anom_disp["Category"].apply(lambda x: cat_display(x, L))
            fig_a = go.Figure(go.Bar(
                x=anom["delta"], y=anom_disp["Category"], orientation="h",
                marker_color=[C_RED if v > 0 else C_GREEN for v in anom["delta"]],
                text=[f"{'+' if v > 0 else ''}{v:,.0f}" for v in anom["delta"]],
                textposition="outside",
            ))
            fig_a.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title=d("anom_delta") + " (₪)", yaxis_title="",
                margin=dict(l=0, r=0, t=10, b=0), height=max(300, 40 * len(anom)),
            )
            fig_a.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_a, width="stretch")

    st.markdown("---")

    # Drill-down
    st.markdown(f"### {d('drill_title')}")
    cats = sorted(dd.real_spend(ledger)["Category"].unique().tolist())
    pick_label = st.selectbox(
        d("pick_category"), cats, format_func=lambda c: cat_display(c, L), key="drill_cat",
    )
    sub = dd.real_spend(ledger)
    sub = sub[sub["Category"] == pick_label]
    if not sub.empty:
        trend = sub.pivot_table(
            index="Month", columns="Sub_Category", values="AbsAmount", aggfunc="sum", fill_value=0.0
        )
        trend.columns = [sub_display(c, L) for c in trend.columns]
        fig_t = px.bar(trend, barmode="group", color_discrete_sequence=px.colors.qualitative.Bold)
        fig_t.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title=d("cat_trend", cat=cat_display(pick_label, L)),
            xaxis_title=d("month_axis"), yaxis_title=d("amount_axis"),
            legend=dict(orientation="h", y=-0.25), margin=dict(l=0, r=0, t=40, b=0), height=340,
        )
        st.plotly_chart(fig_t, width="stretch")

        st.markdown(f"**{d('cat_txns')}**")
        show = sub[["Date", "Description", "AbsAmount", "Owner", "Source", "Sub_Category"]].copy()
        show["Date"] = show["Date"].dt.strftime("%Y-%m-%d")
        show["Sub_Category"] = show["Sub_Category"].apply(lambda x: sub_display(x, L))
        show = show.rename(columns={
            "Date": d("col_date"), "Description": d("col_desc"), "AbsAmount": d("col_amount"),
            "Owner": d("col_owner"), "Source": d("col_source"), "Sub_Category": d("col_sub"),
        })
        st.dataframe(
            show.sort_values(d("col_amount"), ascending=False),
            width="stretch", hide_index=True,
        )

# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — STORY
# ══════════════════════════════════════════════════════════════════════════
with tab_story:
    story_months = [m for m in months if dd.load_story(m)]
    if not story_months:
        st.info(d("story_missing"))
    else:
        pick = st.selectbox(d("story_pick"), story_months, index=len(story_months) - 1, key="story_month")
        row = summary[summary["Month"] == pick]
        if not row.empty:
            r = row.iloc[0]
            s = st.columns(4)
            s[0].metric(d("income"), fmt_shekel(r["income"]))
            s[1].metric(d("expenses"), fmt_shekel(r["expenses"]))
            s[2].metric(d("net"), fmt_shekel(r["net_savings"]))
            s[3].metric(d("rate"), f"{r['savings_rate']:.0f}%")
        story_md = dd.load_story(pick)
        # Convert the markdown narrative to HTML and inject it inside the styled
        # card in ONE call — three separate st.markdown() calls would NOT nest,
        # leaving the card empty. markdown-it-py is already a dependency.
        story_html = MarkdownIt("commonmark", {"breaks": True, "html": True}).render(story_md)
        st.markdown(f'<div class="story-card">{story_html}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — TRANSACTION EXPLORER
# ══════════════════════════════════════════════════════════════════════════
with tab_txns:
    st.markdown(f"### {d('filters')}")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_months = st.multiselect(d("f_month"), months, default=months, key="tx_months")
    with f2:
        owners = sorted(ledger["Owner"].dropna().unique().tolist())
        sel_owners = st.multiselect(d("f_owner"), owners, default=owners, key="tx_owners")
    with f3:
        sources = sorted(ledger["Source"].dropna().unique().tolist())
        sel_sources = st.multiselect(d("f_source"), sources, default=sources, key="tx_sources")
    with f4:
        cats = sorted(ledger["Category"].dropna().unique().tolist())
        sel_cats = st.multiselect(
            d("f_category"), cats, default=cats,
            format_func=lambda c: cat_display(c, L), key="tx_cats",
        )

    g1, g2, g3 = st.columns([2, 1, 1])
    with g1:
        search = st.text_input(d("f_search"), key="tx_search")
    with g2:
        tx_type = st.radio(
            d("f_type"), [d("type_all"), d("type_expense"), d("type_income")],
            horizontal=True, key="tx_type",
        )
    with g3:
        show_excluded = st.checkbox(d("show_excluded"), value=False, key="tx_excluded")

    view = ledger.copy()
    view = view[view["Month"].isin(sel_months)]
    view = view[view["Owner"].isin(sel_owners)]
    view = view[view["Source"].isin(sel_sources)]
    view = view[view["Category"].isin(sel_cats)]
    if not show_excluded:
        view = view[~view["Excluded"]]
    if search:
        view = view[view["Description"].astype(str).str.contains(search, case=False, na=False)]
    if tx_type == d("type_expense"):
        view = view[view["Amount"] < 0]
    elif tx_type == d("type_income"):
        view = view[view["Amount"] > 0]

    st.markdown(d("rows_shown", n=len(view), sum=view["Amount"].sum()))

    disp = view[["Date", "Description", "Amount", "Owner", "Source", "Category", "Sub_Category", "Excluded"]].copy()
    disp = disp.sort_values("Date", ascending=False)
    disp["Date"] = disp["Date"].dt.strftime("%Y-%m-%d")
    disp["Category"] = disp["Category"].apply(lambda x: cat_display(x, L))
    disp["Sub_Category"] = disp["Sub_Category"].apply(lambda x: sub_display(x, L))
    disp = disp.rename(columns={
        "Date": d("col_date"), "Description": d("col_desc"), "Amount": d("col_amount"),
        "Owner": d("col_owner"), "Source": d("col_source"), "Category": d("col_category"),
        "Sub_Category": d("col_sub"), "Excluded": d("col_excluded"),
    })
    st.dataframe(disp, width="stretch", hide_index=True, height=460)

    st.download_button(
        d("download"),
        data=disp.to_csv(index=False).encode("utf-8-sig"),
        file_name="transactions.csv",
        mime="text/csv",
    )
