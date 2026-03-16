import streamlit as st
import os
import pandas as pd
import time
import plotly.express as px

from tools.translations import t, TRANSLATIONS, cat_display, sub_display

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

from tools.credit_card_ingestion import IngestionAgent
from classifier_agent import process_and_classify 
from tools.classify_dataframe import classify_dataframe, save_approved_to_memory
from tools.analyst_agent import FinancialAnalystAgent
from tools.balance_tracker import load_balance, get_avg_savings_rate

# Initialize session state for pinned insights
if 'pinned_insights' not in st.session_state:
    st.session_state.pinned_insights = []
    # Load pinned insights from file if exists
    pinned_file = "data/processed/pinned_insights.json"
    if os.path.exists(pinned_file):
        import json
        with open(pinned_file, 'r', encoding='utf-8') as f:
            st.session_state.pinned_insights = json.load(f)

if 'show_landing' not in st.session_state:
    st.session_state.show_landing = True

if 'lang' not in st.session_state:
    st.session_state.lang = 'he'

# --- UI Configuration ---
st.set_page_config(page_title="Family Financial Analyst", page_icon="💰", layout="wide")

# Determine language early for CSS
_lang = st.session_state.get('lang', 'he')
_is_rtl = _lang == 'he'
_dir = 'rtl' if _is_rtl else 'ltr'
_text_align = 'right' if _is_rtl else 'left'

# Dynamic RTL/LTR CSS based on language
st.markdown(f"""
<style>
    .main .block-container {{ direction: {_dir} !important; }}
    section[data-testid="stSidebar"] {{ direction: {_dir}; }}
    .stTabs [data-baseweb="tab-list"] {{ direction: {_dir}; }}
    .stDataFrame {{ direction: {_dir}; }}
    .stSelectbox, .stNumberInput, .stFileUploader {{ direction: ltr; }}
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stNumberInput {{ direction: ltr; }}
    .analyst-story {{ direction: {_dir}; text-align: {_text_align}; }}
    .analyst-story h1, .analyst-story h2, .analyst-story h3 {{ direction: {_dir}; text-align: {_text_align}; }}
    .analyst-story p {{ direction: {_dir}; text-align: {_text_align}; }}
</style>
""", unsafe_allow_html=True)

# Static CSS for modern UI
st.markdown("""
<style>
    /* Main background - Monday.com dark navy */
    .main {
        background: #1f2347 !important;
    }
    
    /* Hero section - clean white card */
    .hero-section {
        text-align: center;
        padding: 40px 30px;
        background: white;
        border-radius: 12px;
        margin: 20px 0 0 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-bottom: none;
    }
    
    .hero-title {
        font-size: 2.5em;
        font-weight: 700;
        color: #6c5ce7 !important;
        margin-bottom: 10px;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        font-size: 1.1em;
        color: #676879;
        margin-bottom: 0;
        line-height: 1.6;
    }
    
    /* Category cards - white with subtle shadow */
    .category-card {
        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
        border-radius: 12px;
        padding: 25px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3);
        transition: all 0.2s ease;
        cursor: pointer;
        height: 100%;
        border: 1px solid rgba(108, 92, 231, 0.2);
    }
    
    .category-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(108, 92, 231, 0.4);
        border-color: #6c5ce7;
    }
    
    .category-icon {
        font-size: 2.5em;
        margin-bottom: 15px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        display: none;
    }
    
    .category-title {
        font-size: 1.2em;
        font-weight: 700;
        color: white;
        margin-bottom: 18px;
        letter-spacing: -0.3px;
    }
    
    .category-item {
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        color: white;
        font-size: 0.95em;
        display: flex;
        align-items: center;
    }
    
    .category-item:last-child {
        border-bottom: none;
    }
    
    .category-item:hover {
        color: #ffd700;
    }
    
    .category-item::before {
        content: "✓";
        margin-right: 8px;
        color: #ffd700;
        font-weight: bold;
    }
    
    /* Month selector styling - purple gradient */
    .month-selector-container {
        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
        padding: 20px 25px;
        border-radius: 12px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3);
        border: 1px solid rgba(108, 92, 231, 0.2);
    }
    
    .month-selector-title {
        color: white;
        font-size: 1.2em;
        font-weight: 700;
        margin-bottom: 15px;
        letter-spacing: -0.3px;
    }
    
    /* Streamlit selectbox styling - white background with purple on focus */
    .stSelectbox > div > div {
        background: white;
        border-radius: 8px;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background-color: white !important;
        border: 2px solid #e0e0e0 !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        color: #2c3e50 !important;
        font-weight: 600 !important;
        font-size: 1.05em !important;
    }
    
    .stSelectbox [data-baseweb="select"]:focus-within {
        border-color: #6c5ce7 !important;
        box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.2) !important;
    }
    
    /* Dropdown menu styling */
    .stSelectbox [role="listbox"] {
        background-color: white !important;
        border: 2px solid #6c5ce7 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3) !important;
    }
    
    .stSelectbox [data-baseweb="popover"] {
        background-color: white !important;
    }
    
    .stSelectbox [role="option"] {
        color: #2c3e50 !important;
        font-weight: 500 !important;
        padding: 12px 16px !important;
    }
    
    .stSelectbox [role="option"]:hover {
        background-color: #f0ebff !important;
        color: #6c5ce7 !important;
        font-weight: 600 !important;
    }
    
    .stSelectbox [aria-selected="true"] {
        background-color: #6c5ce7 !important;
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar selectbox specific styling */
    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
        background-color: white !important;
        border: 2px solid #6c5ce7 !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }
    
    /* Start Analysis Button - Monday.com purple */
    .stButton > button {
        background: #6c5ce7 !important;
        color: white !important;
        border: none !important;
        padding: 14px 32px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 1.1em !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3) !important;
    }
    
    .stButton > button:hover {
        background: #5849c7 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(108, 92, 231, 0.4) !important;
    }
    
    /* Dark dashboard tiles */
    .dashboard-tile {
        background: #2c3e50;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 2px solid #34495e;
    }
    
    .tile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        color: white;
    }
    
    .tile-title {
        font-size: 1.2em;
        font-weight: 600;
        color: white;
    }
    
    .tile-badge {
        background: #00ca72;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
    }
    
    /* Pin button */
    .pin-button {
        background: #6c5ce7;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
    }
    
    .pin-button:hover {
        background: #5849c7;
    }
    
    /* Analyst story - modern design (direction set dynamically) */
    .analyst-story {
        font-size: 1.3em;
        line-height: 1.9;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .analyst-story h1, .analyst-story h2, .analyst-story h3 {
        color: #ffd700;
        font-size: 1.6em;
        margin-top: 20px;
    }
    
    .analyst-story strong {
        color: #ffd700;
        font-weight: bold;
    }
    
    .analyst-story p {
    }
    
    /* Reduce overall padding for compact view */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
</style>
""", unsafe_allow_html=True)

# Landing Page
if st.session_state.show_landing:
    L = st.session_state.lang
    
    # Language toggle at top right
    lang_col1, lang_col2 = st.columns([6, 1])
    with lang_col2:
        lang_choice = st.selectbox(
            "🌐", ['עברית', 'English'],
            index=0 if L == 'he' else 1,
            key="lang_landing",
            label_visibility="collapsed"
        )
        new_lang = 'he' if lang_choice == 'עברית' else 'en'
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
    
    L = st.session_state.lang
    dir_attr = 'rtl' if L == 'he' else 'ltr'
    
    st.markdown(f"""
    <div class="hero-section" dir="{dir_attr}">
        <h1 class="hero-title">{t('app_title', L)}</h1>
        <p class="hero-subtitle">{t('app_subtitle', L)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Running Balance Box
    balance_data = load_balance()
    if balance_data['months_analyzed']:
        avg_rate = get_avg_savings_rate(balance_data)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); 
                    border-radius: 12px; padding: 20px 25px; margin: 15px 0;
                    box-shadow: 0 4px 12px rgba(0, 184, 148, 0.3);">
            <div style="color: rgba(255,255,255,0.8); font-size: 0.9em; font-weight: 600;">{t('balance_label', L)}</div>
            <div style="color: white; font-size: 2.2em; font-weight: 700; margin: 5px 0;">₪{balance_data['total_net_savings']:,.0f}</div>
            <div style="color: rgba(255,255,255,0.9); font-size: 0.85em;">
                📅 {len(balance_data['months_analyzed'])} {'חודשים נותחו' if L == 'he' else 'months analyzed'} · 
                📈 {t('balance_delta', L, rate=f'{avg_rate:.1f}')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Month Selection
    st.markdown('<div class="month-selector-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="month-selector-title">{t("select_month", L)}</div>', unsafe_allow_html=True)
    
    from datetime import datetime
    current_date = datetime.now()
    
    month_options = []
    for i in range(12):
        date = datetime(current_date.year if i < current_date.month else current_date.year - 1, 
                       ((current_date.month - i - 1) % 12) + 1, 1)
        month_options.append(date.strftime("%Y-%m"))
    
    selected_month_landing = st.selectbox(
        t('which_month', L),
        options=month_options,
        index=0,
        label_visibility="collapsed",
        key="month_selector_landing"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="category-card">
            <div class="category-title">{t('smart_class_title', L)}</div>
            <div class="category-item">{t('smart_class_1', L)}</div>
            <div class="category-item">{t('smart_class_2', L)}</div>
            <div class="category-item">{t('smart_class_3', L)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="category-card">
            <div class="category-title">{t('visual_title', L)}</div>
            <div class="category-item">{t('visual_1', L)}</div>
            <div class="category-item">{t('visual_2', L)}</div>
            <div class="category-item">{t('visual_3', L)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="category-card">
            <div class="category-title">{t('analyst_title', L)}</div>
            <div class="category-item">{t('analyst_1', L)}</div>
            <div class="category-item">{t('analyst_2', L)}</div>
            <div class="category-item">{t('analyst_3', L)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button(t('start_analysis', L), type="primary", use_container_width=True):
        st.session_state.show_landing = False
        st.session_state.selected_month_from_landing = selected_month_landing
        st.rerun()
    
    st.stop()

# --- Helper Function for Historical Data ---
HISTORICAL_FILE = "data/processed/historical_ledger.csv"

def load_historical_data():
    if os.path.exists(HISTORICAL_FILE):
        df = pd.read_csv(HISTORICAL_FILE)
        # Ensure Amount is numeric
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            # Normalize sign convention for legacy data:
            # Old data stored CC charges as positive; new convention: negative = money out.
            # Negate ALL CC amounts so charges become negative and refunds become positive.
            # Manual_Income stays positive (money in). Bank_Discount keeps its original signs.
            if 'Source' in df.columns:
                cc_sources = ['Max', 'Isracard', 'Discount_Credit_Card']
                cc_mask = df['Source'].isin(cc_sources)
                if cc_mask.any():
                    # Check if data is in old format (most CC amounts positive = charges)
                    cc_positive_ratio = (df.loc[cc_mask, 'Amount'] > 0).mean()
                    if cc_positive_ratio > 0.5:
                        # Old format detected — negate to convert
                        df.loc[cc_mask, 'Amount'] = df.loc[cc_mask, 'Amount'] * -1
        return df
    return pd.DataFrame()

def save_to_history(new_df):
    history_df = load_historical_data()
    
    if not history_df.empty:
        # Only keep data from different months, remove duplicates from the same month
        # This prevents re-uploading the same month from duplicating data
        if 'Month_Year' not in new_df.columns:
            new_df['Month_Year'] = pd.to_datetime(new_df['Date'], errors='coerce').dt.to_period('M').astype(str)
        
        # Get the month being uploaded
        new_month = new_df['Month_Year'].iloc[0] if not new_df.empty else None
        
        if new_month:
            # Remove any existing data from this month
            history_df = history_df[~(history_df['Date'].astype(str).str.startswith(new_month[:7]))]
        
        # Append new data
        combined_df = pd.concat([history_df, new_df]).drop_duplicates(subset=['Date', 'Description', 'Amount', 'Owner'])
    else:
        combined_df = new_df
    
    # Ensure Amount is numeric before saving
    combined_df['Amount'] = pd.to_numeric(combined_df['Amount'], errors='coerce')
    
    # Remove the Month_Year column before saving (it's calculated when needed)
    if 'Month_Year' in combined_df.columns:
        combined_df = combined_df.drop(columns=['Month_Year'])
    
    combined_df.to_csv(HISTORICAL_FILE, index=False, encoding='utf-8-sig')
    return combined_df

# --- 1. The Upload Zone ---
L = st.session_state.lang

# Dashboard header with language toggle
hdr_col1, hdr_col2 = st.columns([5, 1])
with hdr_col1:
    st.markdown(f"""
    <div style="margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">{t('dashboard_title', L)}</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0;">{t('dashboard_subtitle', L)}</p>
    </div>
    """, unsafe_allow_html=True)
with hdr_col2:
    lang_choice = st.selectbox(
        "🌐", ['עברית', 'English'],
        index=0 if L == 'he' else 1,
        key="lang_dashboard",
        label_visibility="collapsed"
    )
    new_lang = 'he' if lang_choice == 'עברית' else 'en'
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

# Running Balance Box on dashboard
balance_data = load_balance()
if balance_data['months_analyzed']:
    avg_rate = get_avg_savings_rate(balance_data)
    bal_col1, bal_col2, bal_col3 = st.columns(3)
    with bal_col1:
        st.metric(
            label=t('balance_label', L),
            value=f"₪{balance_data['total_net_savings']:,.0f}",
            delta=f"{avg_rate:.1f}% {'ממוצע חיסכון' if L == 'he' else 'avg savings'}"
        )
    with bal_col2:
        st.metric(
            label='💰 ' + ('סה"כ הכנסות' if L == 'he' else 'Total Income'),
            value=f"₪{balance_data['total_income']:,.0f}"
        )
    with bal_col3:
        st.metric(
            label='💸 ' + ('סה"כ הוצאות' if L == 'he' else 'Total Expenses'),
            value=f"₪{balance_data['total_expenses']:,.0f}"
        )

if st.button(t('back_home', L), key="back_home"):
    st.session_state.show_landing = True
    st.rerun()

st.markdown("---")

with st.sidebar:
    st.header(t('monthly_setup', L))
    
    # Month selection
    from datetime import datetime
    current_date = datetime.now()
    
    # Generate list of months (last 12 months)
    month_options = []
    for i in range(12):
        date = datetime(current_date.year if i < current_date.month else current_date.year - 1, 
                       ((current_date.month - i - 1) % 12) + 1, 1)
        month_options.append(date.strftime("%Y-%m"))
    
    # Use month from landing page if available
    default_index = 0
    if 'selected_month_from_landing' in st.session_state:
        try:
            default_index = month_options.index(st.session_state.selected_month_from_landing)
        except:
            pass
    
    selected_month = st.selectbox(
        t('analyzing_month', L),
        options=month_options,
        index=default_index,
        help=t('month_help', L)
    )
    
    st.markdown("---")
    
    # Manual Income Entry (not validation, actual income)
    st.subheader(t('income_header', L))
    st.markdown(t('income_desc', L))
    tal_salary = st.number_input(t('tal_salary', L), value=0, step=1000)
    reut_salary = st.number_input(t('reut_salary', L), value=0, step=1000)
    other_income = st.number_input(t('other_income', L), value=0, step=1000)
    
    total_manual_income = tal_salary + reut_salary + other_income
    
    if total_manual_income > 0:
        st.success(t('total_income', L, amount=f"{total_manual_income:,.2f}"))
    else:
        st.warning(t('no_income', L))
    
    st.markdown("---")
    
    st.header(t('file_upload', L))
    uploaded_files = st.file_uploader(
        t('upload_label', L), 
        accept_multiple_files=True, 
        type=['csv', 'xlsx', 'pdf']
    )
    run_button = st.button(t('run_button', L), type="primary")
    
    # ── Reset All Data Section ──
    st.markdown("---")
    with st.expander(t('reset_title', L), expanded=False):
        st.markdown(t('reset_warning', L))
        if st.button(t('reset_confirm', L), type="secondary", key="reset_all_data"):
            import glob
            # 1. Delete processed files
            for f in ['data/processed/historical_ledger.csv',
                       'data/processed/running_balance.json',
                       'data/processed/pinned_insights.json',
                       'data/processed/monthly_analysis_history.json']:
                if os.path.exists(f):
                    os.remove(f)
            
            # 2. Delete raw uploaded files
            for f in glob.glob('data/raw/*'):
                os.remove(f)
            
            # 3. Clean vector memory (non-bootstrap entries)
            try:
                from scripts.clean_memory import BOOTSTRAP_MERCHANTS
                from azure.search.documents import SearchClient
                from azure.core.credentials import AzureKeyCredential
                search_client = SearchClient(
                    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
                    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
                    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
                )
                results = search_client.search(search_text="*", select=["id", "merchant_name"], top=1000)
                to_delete = [{"id": r["id"]} for r in results if r.get("merchant_name", "") not in BOOTSTRAP_MERCHANTS]
                kept = 0
                deleted = len(to_delete)
                if to_delete:
                    search_client.delete_documents(documents=to_delete)
                results2 = search_client.search(search_text="*", select=["id"], top=1000)
                kept = sum(1 for _ in results2)
                st.info(t('reset_memory_result', L, kept=kept, deleted=deleted))
            except Exception as e:
                st.warning(f"Memory cleanup error: {e}")
            
            # 4. Clear session state
            for key in ['current_df', 'history_df', 'story', 'selected_month', 
                        'pending_reviews', 'pinned_insights', 'dup_txns']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.pinned_insights = []
            
            st.success(t('reset_success', L))
            import time
            time.sleep(2)
            st.session_state.show_landing = True
            st.rerun()

# --- 2. The Trigger Logic ---
if run_button and uploaded_files:
    if not selected_month:
        st.error(t('select_month_error', L))
    else:
        progress_text = "Operation in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)
        
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        saved_file_paths = []
        
        for file in uploaded_files:
            file_path = os.path.join("data/raw", file.name)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            saved_file_paths.append(file_path)
            
        my_bar.progress(25, text=t('progress_saving', L))
        
        try:
            # Phase 1 - Ingestion
            ingestion_agent = IngestionAgent()
            raw_unified_df = ingestion_agent.run_monthly_ingestion(saved_file_paths)
            
            my_bar.progress(35, text=t('progress_filtering', L))
            
            # ── Safety: Duplicate file detection ──
            if ingestion_agent.duplicate_files:
                for dup_name, orig_name in ingestion_agent.duplicate_files:
                    st.warning(t('dup_file_desc', L, filename=dup_name, original=orig_name))
            
            # Show date info (dates are already parsed by IngestionAgent)
            st.info(t('loaded_total', L, count=len(raw_unified_df)))
            st.info(t('date_range', L, min_date=str(raw_unified_df['Date'].min())[:10], max_date=str(raw_unified_df['Date'].max())[:10]))
            
            # Ensure dates are datetime objects (should already be from ingestion)
            if not pd.api.types.is_datetime64_any_dtype(raw_unified_df['Date']):
                st.warning(t('dates_converting', L))
                raw_unified_df['Date'] = pd.to_datetime(raw_unified_df['Date'], errors='coerce')
            
            # Check for any null dates
            null_dates = raw_unified_df['Date'].isna().sum()
            if null_dates > 0:
                st.warning(t('invalid_dates', L, count=null_dates))
                raw_unified_df = raw_unified_df.dropna(subset=['Date'])
            
            # Filter to selected month
            year, month = map(int, selected_month.split('-'))
            raw_unified_df['Year'] = raw_unified_df['Date'].dt.year
            raw_unified_df['Month'] = raw_unified_df['Date'].dt.month
            raw_unified_df['Day'] = raw_unified_df['Date'].dt.day
            
            # Get transactions from selected month
            filtered_df = raw_unified_df[
                (raw_unified_df['Year'] == year) & (raw_unified_df['Month'] == month)
            ].copy()
            
            st.success(t('filtered_count', L, count=len(filtered_df), month=selected_month))
            
            if filtered_df.empty:
                st.error(t('no_transactions', L, month=selected_month))
                st.stop()
            
            # ── Safety: Duplicate transaction detection (within same upload) ──
            dup_txns = IngestionAgent.detect_duplicate_transactions(filtered_df, date_tolerance_days=0)
            if dup_txns:
                st.session_state['dup_txns'] = dup_txns
            
            # ── Safety: Check overlap with historical data ──
            history_df = load_historical_data()
            if not history_df.empty:
                history_df['Date'] = pd.to_datetime(history_df['Date'], errors='coerce')
                hist_month = history_df[
                    (history_df['Date'].dt.year == year) & (history_df['Date'].dt.month == month)
                ]
                if not hist_month.empty:
                    st.info(t('dup_file_history_desc', L, count=len(hist_month)))
            
            my_bar.progress(50, text=t('progress_classifying', L))
            
            # Phase 2 - Classification (returns df + pending reviews for human approval)
            final_classified_df, pending_reviews = process_and_classify(filtered_df)
            
            # Ensure Dates are datetime objects
            final_classified_df['Date'] = pd.to_datetime(final_classified_df['Date'], errors='coerce')
            final_classified_df['Month_Year'] = final_classified_df['Date'].dt.to_period('M').astype(str)
            
            # Debug: Show transaction count
            st.info(t('classified_count', L, count=len(final_classified_df)))
            
            # Add Manual Income as a transaction
            my_bar.progress(70, text=t('progress_income', L))
            
            if total_manual_income > 0:
                # Create income entries
                income_entries = []
                
                if tal_salary > 0:
                    income_entries.append({
                        'Date': pd.to_datetime(f"{selected_month}-01"),
                        'Description': 'Tal Salary (Manual Entry)',
                        'Amount': tal_salary,
                        'Owner': 'Tal',
                        'Source': 'Manual_Income',
                        'Category': 'Income',
                        'Sub_Category': 'Tal_Salary',
                        'Month_Year': selected_month
                    })
                
                if reut_salary > 0:
                    income_entries.append({
                        'Date': pd.to_datetime(f"{selected_month}-01"),
                        'Description': 'Reut Salary (Manual Entry)',
                        'Amount': reut_salary,
                        'Owner': 'Reut',
                        'Source': 'Manual_Income',
                        'Category': 'Income',
                        'Sub_Category': 'Reut_Salary',
                        'Month_Year': selected_month
                    })
                
                if other_income > 0:
                    income_entries.append({
                        'Date': pd.to_datetime(f"{selected_month}-01"),
                        'Description': 'Other Income (Manual Entry)',
                        'Amount': other_income,
                        'Owner': 'Joint',
                        'Source': 'Manual_Income',
                        'Category': 'Income',
                        'Sub_Category': 'Other_Income_Bit',
                        'Month_Year': selected_month
                    })
                
                # Add income to the dataframe
                income_df = pd.DataFrame(income_entries)
                final_classified_df = pd.concat([final_classified_df, income_df], ignore_index=True)
                
                st.success(t('added_income', L, amount=f"{total_manual_income:,.2f}"))
            else:
                st.warning(t('no_income_warning', L))
            
            # Phase 3 - Save to History
            my_bar.progress(75, text=t('progress_history', L))
            full_history_df = save_to_history(final_classified_df)
            
            # Phase 4 - Generate LLM Insights
            my_bar.progress(90, text=t('progress_story', L))
            analyst = FinancialAnalystAgent()
            story_markdown = analyst.generate_monthly_story(final_classified_df, selected_month, lang=L)
            
            my_bar.progress(100, text=t('progress_complete', L))
            st.session_state['current_df'] = final_classified_df
            st.session_state['history_df'] = full_history_df
            st.session_state['story'] = story_markdown
            st.session_state['selected_month'] = selected_month
            
            # Store pending reviews for the review UI
            if pending_reviews:
                # Deduplicate: keep only unique merchant names, sum amounts
                seen = {}
                for item in pending_reviews:
                    merchant, cat, sub = item[0], item[1], item[2]
                    amount = item[3] if len(item) > 3 else 0
                    if merchant not in seen:
                        seen[merchant] = (merchant, cat, sub, amount)
                st.session_state['pending_reviews'] = list(seen.values())
            else:
                st.session_state['pending_reviews'] = []
            
        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
            import traceback
            st.error(traceback.format_exc())

# ── Duplicate Transaction Review Panel ──
if 'dup_txns' in st.session_state and st.session_state['dup_txns']:
    dup_txns = st.session_state['dup_txns']
    
    st.markdown("---")
    _dir = 'rtl' if L == 'he' else 'ltr'
    _align = 'right' if L == 'he' else 'left'
    st.markdown("""
    <div dir="{dir}" style="background: linear-gradient(135deg, #2d1b1b 0%, #1a1a2e 100%); 
                border: 2px solid #e17055; border-radius: 16px; padding: 24px; margin: 16px 0;
                text-align: {align};">
        <h3 style="color: #fab1a0; margin-top: 0;">{title}</h3>
        <p style="color: #dfe6e9; font-size: 0.9rem;">
            {desc}
        </p>
    </div>
    """.format(dir=_dir, align=_align, 
               title=t('dup_txn_title', L), 
               desc=t('dup_txn_desc', L, count=len(dup_txns))), unsafe_allow_html=True)
    
    # Table header
    dup_hdr = st.columns([1.5, 3, 1.2, 1.5, 2])
    with dup_hdr[0]:
        st.markdown(f"**{t('dup_txn_col_date', L)}**")
    with dup_hdr[1]:
        st.markdown(f"**{t('dup_txn_col_merchant', L)}**")
    with dup_hdr[2]:
        st.markdown(f"**{t('dup_txn_col_amount', L)}**")
    with dup_hdr[3]:
        st.markdown(f"**{t('dup_txn_col_source', L)}**")
    with dup_hdr[4]:
        st.markdown(f"**{t('dup_txn_col_action', L)}**")
    
    st.markdown("<hr style='margin: 4px 0; border-color: #555;'>", unsafe_allow_html=True)
    
    for idx, dup in enumerate(dup_txns):
        dup_cols = st.columns([1.5, 3, 1.2, 1.5, 2])
        with dup_cols[0]:
            st.markdown(f"{dup['date']}")
        with dup_cols[1]:
            st.markdown(f"**{dup['description'][:40]}**")
        with dup_cols[2]:
            st.markdown(f"₪{abs(dup['amount']):,.0f}")
        with dup_cols[3]:
            st.markdown(f"{dup['source']}")
        with dup_cols[4]:
            action_options = [t('dup_txn_keep', L), t('dup_txn_remove', L)]
            st.selectbox(
                "Action",
                action_options,
                index=0,
                key=f"dup_action_{idx}",
                label_visibility="collapsed"
            )
    
    if st.button(t('dup_txn_confirm', L), type="primary", use_container_width=True):
        # Collect indices to remove
        indices_to_remove = []
        remove_label = t('dup_txn_remove', L)
        for idx, dup in enumerate(dup_txns):
            action = st.session_state.get(f"dup_action_{idx}", '')
            if action == remove_label:
                # Remove the SECOND occurrence (keep the first)
                if len(dup['indices']) > 1:
                    indices_to_remove.append(dup['indices'][1])
        
        if indices_to_remove and 'current_df' in st.session_state:
            df = st.session_state['current_df']
            # Only drop indices that actually exist in the dataframe
            valid_indices = [i for i in indices_to_remove if i in df.index]
            if valid_indices:
                df = df.drop(index=valid_indices).reset_index(drop=True)
                st.session_state['current_df'] = df
                
                # Regenerate story with corrected data
                analyst = FinancialAnalystAgent()
                selected_month = st.session_state.get('selected_month', '')
                story_markdown = analyst.generate_monthly_story(df, selected_month, lang=L)
                st.session_state['story'] = story_markdown
                
                # Re-save history
                full_history_df = save_to_history(df)
                st.session_state['history_df'] = full_history_df
            
            st.success(t('dup_txn_resolved', L, count=len(valid_indices)))
        else:
            st.info(t('dup_txn_none', L))
        
        st.session_state['dup_txns'] = []
        st.rerun()

# ── Human Review Panel for New Classifications ──
if 'pending_reviews' in st.session_state and st.session_state['pending_reviews']:
    reviews = st.session_state['pending_reviews']
    
    st.markdown("---")
    _dir = 'rtl' if L == 'he' else 'ltr'
    _align = 'right' if L == 'he' else 'left'
    st.markdown("""
    <div dir="{dir}" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                border: 2px solid #6c5ce7; border-radius: 16px; padding: 24px; margin: 16px 0;
                text-align: {align};">
        <h3 style="color: #a29bfe; margin-top: 0;">{title}</h3>
        <p style="color: #dfe6e9; font-size: 0.9rem;">
            {desc}
        </p>
    </div>
    """.format(dir=_dir, align=_align, title=t('review_title', L), desc=t('review_desc', L, count=len(reviews))), unsafe_allow_html=True)
    
    # Define the taxonomy for dropdowns
    TAXONOMY = {
        'Housing_Fixed': ['Rent_Mortgage', 'Utilities_Arnona_Elec_Water_Gas', 'Communication', 'Maintenance_Vaad_Cleaner'],
        'Insurance_Health': ['Insurances', 'Kupat_Holim', 'Private_Medical'],
        'Kids_Family': ['Gan_Education', 'Baby_Equipment_Pharm', 'Kids_Clothing_Toys'],
        'Transportation': ['Car_Gas_Tolls', 'Public_Transit_Taxi', 'Parking_Tolls', 'Car_Maintenance_Licensing'],
        'Variable_Daily': ['Groceries_Supermarket', 'Dining_Restaurants_Wolt', 'Home_Furniture_Decor', 'Clothing_Shoes', 'Gifts_Events', 'General_Shopping'],
        'Leisure_Grooming': ['Subscriptions', 'Personal_Care_Hair_Nails', 'Hobbies_Entertainment_Vacation'],
        'Food': ['Groceries_Supermarket', 'Coffee_Restaurants'],
        'Food_Delivery': ['Dining_Restaurants_Wolt'],
        'Pharm': ['Pharm'],
        'Health': ['Medical_Insurance', 'sport_club_gym'],
        'Insurance': ['Life_Insurance', 'Medical_Private_Insurance'],
        'Home': ['Direct_Online_Shopping'],
        'Investments': ['Savings_Analyst_Brokerage'],
        'Income': ['Tal_Salary', 'Reut_Salary', 'Other_Income_Bit'],
        'Rio': ['Rio_Food', 'Rio_Health', 'Rio_Accessories'],
        'Leisure': ['Tal_Specials'],
    }
    
    all_categories = list(TAXONOMY.keys())
    
    # Build the review table data
    review_data = []
    for i, item in enumerate(reviews):
        merchant, cat, sub = item[0], item[1], item[2]
        amount = item[3] if len(item) > 3 else 0
        # Type is determined by the amount sign (set during ingestion)
        # negative = expense, positive = income/refund
        if amount > 0:
            ai_type = 'Income'
        elif amount < 0:
            ai_type = 'Expense'
        else:
            ai_type = 'Expense'  # default for zero
        review_data.append({
            'idx': i,
            'merchant': merchant,
            'ai_category': cat,
            'ai_sub': sub,
            'amount': amount,
            'ai_type': ai_type,
        })
    
    # Table header
    hdr_cols = st.columns([3, 1.2, 1, 2, 2, 0.5])
    with hdr_cols[0]:
        st.markdown(f"**{t('col_merchant', L)}**")
    with hdr_cols[1]:
        st.markdown(f"**{t('col_amount', L)}**")
    with hdr_cols[2]:
        st.markdown(f"**{t('col_type', L)}**")
    with hdr_cols[3]:
        st.markdown(f"**{t('col_category', L)}**")
    with hdr_cols[4]:
        st.markdown(f"**{t('col_subcategory', L)}**")
    with hdr_cols[5]:
        st.markdown("**🔄**")
    
    st.markdown("<hr style='margin: 4px 0; border-color: #333;'>", unsafe_allow_html=True)
    
    # Display each merchant with editable dropdowns (type is read-only from amount sign)
    for item in review_data:
        cols = st.columns([3, 1.2, 1, 2, 2, 0.5])
        
        with cols[0]:
            st.markdown(f"**{item['merchant'][:35]}**")
        
        with cols[1]:
            st.markdown(f"₪{abs(item['amount']):,.0f}")
        
        with cols[2]:
            # Read-only type badge derived from amount sign
            if item['ai_type'] == 'Income':
                st.markdown(f"🟢 {t('type_income', L)}")
            else:
                st.markdown(f"🔴 {t('type_expense', L)}")
        
        with cols[3]:
            # Category dropdown — all categories available (type is independent of category)
            available_cats = all_categories
            
            default_cat = item['ai_category']
            cat_idx = available_cats.index(default_cat) if default_cat in available_cats else 0
            new_cat = st.selectbox(
                "Category",
                available_cats,
                index=cat_idx,
                format_func=lambda x: cat_display(x, L),
                key=f"review_cat_{item['idx']}",
                label_visibility="collapsed"
            )
        
        with cols[4]:
            sub_options = TAXONOMY.get(new_cat, ['Unknown'])
            sub_idx = sub_options.index(item['ai_sub']) if item['ai_sub'] in sub_options else 0
            new_sub = st.selectbox(
                "Sub-Category",
                sub_options,
                index=sub_idx,
                format_func=lambda x: sub_display(x, L),
                key=f"review_sub_{item['idx']}",
                label_visibility="collapsed"
            )
        
        with cols[5]:
            changed = (new_cat != item['ai_category'] or 
                      new_sub != item['ai_sub'])
            st.markdown('✏️' if changed else '✅')
    
    # Action buttons
    col_approve, col_skip = st.columns(2)
    with col_approve:
        if st.button(t('btn_approve', L), type="primary", use_container_width=True):
            approved = []
            for item in review_data:
                final_cat = st.session_state.get(f"review_cat_{item['idx']}", item['ai_category'])
                final_sub = st.session_state.get(f"review_sub_{item['idx']}", item['ai_sub'])
                
                approved.append({
                    'merchant_name': item['merchant'],
                    'category': final_cat,
                    'sub_category': final_sub,
                })
            
            # Save to memory
            saved_count = save_approved_to_memory(approved)
            
            # Update the current DataFrame with corrections
            if 'current_df' in st.session_state:
                df = st.session_state['current_df']
                for entry in approved:
                    mask = df['Description'].str.strip() == entry['merchant_name']
                    df.loc[mask, 'Category'] = entry['category']
                    df.loc[mask, 'Sub_Category'] = entry['sub_category']
                st.session_state['current_df'] = df
                
                # Regenerate the story with corrected classifications
                analyst = FinancialAnalystAgent()
                selected_month = st.session_state.get('selected_month', '')
                story_markdown = analyst.generate_monthly_story(df, selected_month, lang=L)
                st.session_state['story'] = story_markdown
                
                # Re-save history with corrected data
                full_history_df = save_to_history(df)
                st.session_state['history_df'] = full_history_df
            
            st.session_state['pending_reviews'] = []
            st.success(t('approve_success', L, count=saved_count))
            st.rerun()
    
    with col_skip:
        if st.button(t('btn_skip', L), use_container_width=True):
            st.session_state['pending_reviews'] = []
            st.rerun()

# --- 3. The Dashboard Display ---
if 'current_df' in st.session_state:
    curr_df = st.session_state['current_df']
    hist_df = st.session_state['history_df']
    
    # Filter curr_df to only show the selected month (in case of mixed data)
    if 'selected_month' in st.session_state:
        curr_df['Month_Year'] = pd.to_datetime(curr_df['Date'], errors='coerce').dt.to_period('M').astype(str)
        curr_df = curr_df[curr_df['Month_Year'] == st.session_state['selected_month']].copy()
    
    # Create Tabs for a clean UI
    tab1, tab2, tab3 = st.tabs([t('tab_story', L), t('tab_history', L), t('tab_raw', L)])
    
    with tab1:
        st.markdown(f"### {t('story_header', L)}")
        
        # Pin button for the story
        col_pin, col_empty = st.columns([1, 5])
        with col_pin:
            if st.button(t('pin_story', L), key="pin_story"):
                st.session_state.pinned_insights.append({
                    'type': 'story',
                    'content': st.session_state["story"],
                    'month': st.session_state.get('selected_month', 'Unknown')
                })
                # Save to file
                import json
                os.makedirs("data/processed", exist_ok=True)
                with open("data/processed/pinned_insights.json", 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.pinned_insights, f, ensure_ascii=False, indent=2)
                st.success("Story pinned!")
        
        st.markdown(f'<div class="analyst-story">{st.session_state["story"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"### {t('visual_breakdown', L)}")
        
        
        # Filter to expenses only (negative amounts = money out)
        # Exclude investments (Category='Investments' or אנליסט keyword)
        expenses_only = curr_df[
            (curr_df['Amount'] < 0) &
            (curr_df['Category'] != 'Investments') &
            (~curr_df['Description'].str.contains('אנליסט', case=False, na=False))
        ].copy()
        expenses_only['Amount'] = expenses_only['Amount'].abs()
        # Translate category/sub-category labels for charts
        expenses_only['Category'] = expenses_only['Category'].apply(lambda x: cat_display(x, L))
        expenses_only['Sub_Category'] = expenses_only['Sub_Category'].apply(lambda x: sub_display(x, L))
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="dashboard-tile">', unsafe_allow_html=True)
            st.markdown(f'<div class="tile-header"><span class="tile-title">{t("expenses_by_cat", L)}</span><span class="tile-badge">Updated</span></div>', unsafe_allow_html=True)
            
            # Group by category with abs amounts for the pie chart
            pie_data = expenses_only.groupby('Category')['Amount'].sum().reset_index()
            pie_data = pie_data[pie_data['Amount'] > 0]  # Remove zero/negative categories
            
            fig_pie = px.pie(
                pie_data, 
                values='Amount', 
                names='Category', 
                title="",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
            fig_pie.update_layout(
                font=dict(size=14, family="Arial Black"),
                showlegend=True,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="dashboard-tile">', unsafe_allow_html=True)
            st.markdown(f'<div class="tile-header"><span class="tile-title">{t("top_expenses", L)}</span></div>', unsafe_allow_html=True)
            
            top_expenses = expenses_only.groupby('Sub_Category')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(10)
            fig_bar = px.bar(
                top_expenses,
                x='Sub_Category', 
                y='Amount', 
                title="",
                color='Amount',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(
                font=dict(size=14, color='white'),
                xaxis_title="",
                yaxis_title="Amount (₪)",
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            fig_bar.update_traces(texttemplate='₪%{y:,.0f}', textposition='outside', textfont=dict(color='white'))
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown(f"### {t('pinned_insights', L)}")
        
        if st.session_state.pinned_insights:
            for idx, insight in enumerate(st.session_state.pinned_insights):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.info(f"**{insight['month']}**: {insight['content'][:200]}...")
                with col2:
                    if st.button("🗑️", key=f"remove_{idx}"):
                        st.session_state.pinned_insights.pop(idx)
                        # Save updated list
                        import json
                        with open("data/processed/pinned_insights.json", 'w', encoding='utf-8') as f:
                            json.dump(st.session_state.pinned_insights, f, ensure_ascii=False, indent=2)
                        st.rerun()
        else:
            st.info("No pinned insights yet. Pin stories and charts to save them here!")
        
        st.markdown("---")
        st.markdown(f"### {t('income_vs_expenses', L)}")
        
        
        if not hist_df.empty:
            # Ensure Date and Amount are properly typed
            hist_df['Date'] = pd.to_datetime(hist_df['Date'], errors='coerce')
            hist_df['Amount'] = pd.to_numeric(hist_df['Amount'], errors='coerce')
            # Remove rows with invalid dates or amounts
            hist_df = hist_df.dropna(subset=['Date', 'Amount'])
            # Remove rows with zero amounts (keep negatives — they'll be abs()'d later)
            hist_df = hist_df[hist_df['Amount'] != 0]
            hist_df['Month_Year'] = hist_df['Date'].dt.to_period('M').astype(str)
            # Remove any 'NaT' or invalid month_year values
            hist_df = hist_df[hist_df['Month_Year'] != 'NaT']
            # Exclude investment transfers (Category='Investments' or אנליסט keyword)
            hist_df = hist_df[
                (hist_df['Category'] != 'Investments') &
                (~hist_df['Description'].astype(str).str.contains('אנליסט', case=False, na=False))
            ]
            # Translate category/sub-category labels for charts and table
            hist_df['Category'] = hist_df['Category'].apply(lambda x: cat_display(x, L))
            hist_df['Sub_Category'] = hist_df['Sub_Category'].apply(lambda x: sub_display(x, L))
            # Get unique months that actually have data
            actual_months = sorted(hist_df['Month_Year'].unique())
            if len(actual_months) == 0:
                st.warning("No valid historical data found.")
            else:
                st.info(f"📅 Showing data for {len(actual_months)} months: {', '.join(actual_months)}")
            # Separate Income vs Expenses based on amount sign
            hist_df['Type'] = hist_df['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expenses')
            # Group by Month and Type (Income vs Expenses) - use abs for display
            income_expense_timeline = hist_df.groupby(['Month_Year', 'Type'])['Amount'].apply(
                lambda x: x.abs().sum()
            ).reset_index()
            # Filter to only show months that have actual data
            income_expense_timeline = income_expense_timeline[income_expense_timeline['Month_Year'].isin(actual_months)]
            if not income_expense_timeline.empty and len(actual_months) > 0:
                # Dark tile for Income vs Expenses
                st.markdown('<div class="dashboard-tile">', unsafe_allow_html=True)
                st.markdown(f'<div class="tile-header"><span class="tile-title">{t("income_vs_expenses", L)}</span><span class="tile-badge">Monthly</span></div>', unsafe_allow_html=True)
            # Line chart for Income vs Expenses
            fig_income_expense = px.line(
                income_expense_timeline,
                x='Month_Year',
                y='Amount',
                color='Type',
                title="",
                markers=True,
                color_discrete_map={'Income': '#27ae60', 'Expenses': '#e74c3c'}
            )
            fig_income_expense.update_traces(
                line=dict(width=4),
                marker=dict(size=12, line=dict(width=2, color='#2c3e50'))
            )
            fig_income_expense.update_layout(
                xaxis_title="",
                yaxis_title="Amount (₪)",
                legend_title="",
                font=dict(size=14, color='white'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    gridcolor='rgba(255,255,255,0.1)',
                    type='category',
                    categoryorder='array',
                    categoryarray=actual_months
                ),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                hovermode='x unified',
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig_income_expense, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Group by Month and Category for detailed breakdown
            hist_grouped = hist_df.groupby(['Month_Year', 'Category'])['Amount'].apply(
                lambda x: x.abs().sum()
            ).reset_index()
            
            # Filter to only actual months
            hist_grouped = hist_grouped[hist_grouped['Month_Year'].isin(actual_months)]
            
            if not hist_grouped.empty:
                # Dark tile for category breakdown
                st.markdown('<div class="dashboard-tile">', unsafe_allow_html=True)
                st.markdown(f'<div class="tile-header"><span class="tile-title">{t("category_over_time", L)}</span></div>', unsafe_allow_html=True)
                fig_timeline = px.line(
                    hist_grouped, 
                    x='Month_Year', 
                    y='Amount', 
                    color='Category', 
                    title="",
                    markers=True,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_timeline.update_traces(
                    line=dict(width=3),
                    marker=dict(size=10)
                )
                fig_timeline.update_layout(
                    xaxis_title="",
                    yaxis_title="Amount (₪)",
                    legend_title="",
                    font=dict(size=14, color='white'),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(
                        gridcolor='rgba(255,255,255,0.1)',
                        type='category',
                        categoryorder='array',
                        categoryarray=actual_months
                    ),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    hovermode='x unified',
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.header(t('raw_data', L))
        st.info(t('raw_type_header', L))
        
        # Build display dataframe with translated labels and a Type column
        table_df = curr_df.copy()
        
        # Derive Type from amount sign
        def _get_type_label(amount):
            if amount > 0:
                return t('type_income', L)
            else:
                return t('type_expense', L)
        
        table_df['_display_cat'] = table_df['Category'].apply(lambda x: cat_display(x, L))
        table_df['_display_sub'] = table_df['Sub_Category'].apply(lambda x: sub_display(x, L))
        
        type_options = [t('type_expense', L), t('type_income', L), t('type_refund', L)]
        
        # Table header
        raw_hdr = st.columns([1.2, 3, 1.2, 1, 2, 2])
        with raw_hdr[0]:
            st.markdown(f"**{t('dup_txn_col_date', L)}**")
        with raw_hdr[1]:
            st.markdown(f"**{t('col_merchant', L)}**")
        with raw_hdr[2]:
            st.markdown(f"**{t('col_amount', L)}**")
        with raw_hdr[3]:
            st.markdown(f"**{t('col_type', L)}**")
        with raw_hdr[4]:
            st.markdown(f"**{t('col_category', L)}**")
        with raw_hdr[5]:
            st.markdown(f"**{t('col_subcategory', L)}**")
        
        st.markdown("<hr style='margin: 4px 0; border-color: #333;'>", unsafe_allow_html=True)
        
        # Show each row with editable type
        for idx, row in table_df.iterrows():
            row_cols = st.columns([1.2, 3, 1.2, 1, 2, 2])
            with row_cols[0]:
                st.markdown(f"<small>{str(row['Date'])[:10]}</small>", unsafe_allow_html=True)
            with row_cols[1]:
                st.markdown(f"<small>{str(row['Description'])[:40]}</small>", unsafe_allow_html=True)
            with row_cols[2]:
                st.markdown(f"<small>₪{abs(row['Amount']):,.0f}</small>", unsafe_allow_html=True)
            with row_cols[3]:
                current_type = _get_type_label(row['Amount'])
                type_idx = type_options.index(current_type) if current_type in type_options else 0
                st.selectbox(
                    "type",
                    type_options,
                    index=type_idx,
                    key=f"raw_type_{idx}",
                    label_visibility="collapsed",
                )
            with row_cols[4]:
                st.markdown(f"<small>{row['_display_cat']}</small>", unsafe_allow_html=True)
            with row_cols[5]:
                st.markdown(f"<small>{row['_display_sub']}</small>", unsafe_allow_html=True)
        
        # Save button
        if st.button(t('raw_save_changes', L), type="primary", use_container_width=True):
            changes = 0
            expense_label = t('type_expense', L)
            income_label = t('type_income', L)
            refund_label = t('type_refund', L)
            
            df = st.session_state['current_df']
            for idx in df.index:
                new_type = st.session_state.get(f"raw_type_{idx}", '')
                old_amount = df.at[idx, 'Amount']
                
                if new_type in (income_label, refund_label) and old_amount < 0:
                    # User says this is income/refund but amount is negative → flip to positive
                    df.at[idx, 'Amount'] = abs(old_amount)
                    changes += 1
                elif new_type == expense_label and old_amount > 0:
                    # User says this is expense but amount is positive → flip to negative
                    df.at[idx, 'Amount'] = -abs(old_amount)
                    changes += 1
            
            if changes > 0:
                st.session_state['current_df'] = df
                
                # Regenerate story
                analyst = FinancialAnalystAgent()
                selected_month = st.session_state.get('selected_month', '')
                story_markdown = analyst.generate_monthly_story(df, selected_month, lang=L)
                st.session_state['story'] = story_markdown
                
                # Re-save history
                full_history_df = save_to_history(df)
                st.session_state['history_df'] = full_history_df
                
                st.success(t('raw_changes_saved', L, count=changes))
                st.rerun()
            else:
                st.info(t('raw_no_changes', L))