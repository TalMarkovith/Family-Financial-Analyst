import streamlit as st
import os
import pandas as pd
import time
import plotly.express as px

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

from tools.credit_card_ingestion import IngestionAgent
from classifier_agent import process_and_classify 
from tools.classify_dataframe import classify_dataframe  # Import for next month income check
from tools.analyst_agent import FinancialAnalystAgent # Import our new storyteller

# --- UI Configuration ---
st.set_page_config(page_title="Family Financial Analyst", page_icon="💰", layout="wide")

st.title("Family Financial Analyst 🤖")
st.markdown("Welcome Tal and Reut! Drop your monthly statements below to generate your financial story.")

# --- Helper Function for Historical Data ---
HISTORICAL_FILE = "data/processed/historical_ledger.csv"

def load_historical_data():
    if os.path.exists(HISTORICAL_FILE):
        df = pd.read_csv(HISTORICAL_FILE)
        # Ensure Amount is numeric
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        return df
    return pd.DataFrame()

def save_to_history(new_df):
    history_df = load_historical_data()
    if not history_df.empty:
        # Append and drop exact duplicate rows to prevent double-counting if you upload the same file twice
        combined_df = pd.concat([history_df, new_df]).drop_duplicates(subset=['Date', 'Description', 'Amount', 'Owner'])
    else:
        combined_df = new_df
    
    # Ensure Amount is numeric before saving
    combined_df['Amount'] = pd.to_numeric(combined_df['Amount'], errors='coerce')
    combined_df.to_csv(HISTORICAL_FILE, index=False, encoding='utf-8-sig')
    return combined_df

# --- 1. The Upload Zone ---
with st.sidebar:
    st.header("📅 Monthly Analysis Setup")
    
    # Month selection
    from datetime import datetime
    current_date = datetime.now()
    
    # Generate list of months (last 12 months)
    month_options = []
    for i in range(12):
        date = datetime(current_date.year if i < current_date.month else current_date.year - 1, 
                       ((current_date.month - i - 1) % 12) + 1, 1)
        month_options.append(date.strftime("%Y-%m"))
    
    selected_month = st.selectbox(
        "Which month are you analyzing?",
        options=month_options,
        index=0,
        help="Select the month you want to analyze. Transactions will be filtered to this month."
    )
    
    st.markdown("---")
    
    # Manual Income Entry (not validation, actual income)
    st.subheader("💰 Income for This Month")
    st.markdown("**Enter the actual income amounts:**")
    tal_salary = st.number_input("Tal's Salary (₪)", value=0, step=1000, help="Tal's actual salary for this month")
    reut_salary = st.number_input("Reut's Salary (₪)", value=0, step=1000, help="Reut's actual salary for this month")
    other_income = st.number_input("Other Income (₪)", value=0, step=1000, help="Any other income")
    
    total_manual_income = tal_salary + reut_salary + other_income
    
    if total_manual_income > 0:
        st.success(f"✅ Total Income: ₪{total_manual_income:,.2f}")
    else:
        st.warning("⚠️ No income entered")
    
    st.markdown("---")
    
    st.header("📤 File Upload")
    uploaded_files = st.file_uploader(
        "Upload Credit Card & Bank (עו\"ש) files", 
        accept_multiple_files=True, 
        type=['csv', 'xlsx', 'pdf']
    )
    run_button = st.button("Run Financial Analyst Agent 🚀", type="primary")

# --- 2. The Trigger Logic ---
if run_button and uploaded_files:
    if not selected_month:
        st.error("Please select a month to analyze!")
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
            
        my_bar.progress(25, text="Files saved. Starting Ingestion Agent...")
        
        try:
            # Phase 1 - Ingestion
            ingestion_agent = IngestionAgent()
            raw_unified_df = ingestion_agent.run_monthly_ingestion(saved_file_paths)
            
            my_bar.progress(40, text="Filtering transactions for selected month...")
            
            # Convert dates and filter by selected month
            raw_unified_df['Date'] = pd.to_datetime(raw_unified_df['Date'], dayfirst=True, errors='coerce')
            
            # Show date parsing info
            st.info(f"📅 Loaded {len(raw_unified_df)} total transactions")
            st.info(f"Date range: {raw_unified_df['Date'].min()} to {raw_unified_df['Date'].max()}")
            
            # Filter to selected month
            year, month = map(int, selected_month.split('-'))
            raw_unified_df['Year'] = raw_unified_df['Date'].dt.year
            raw_unified_df['Month'] = raw_unified_df['Date'].dt.month
            raw_unified_df['Day'] = raw_unified_df['Date'].dt.day
            
            # Get transactions from selected month
            filtered_df = raw_unified_df[
                (raw_unified_df['Year'] == year) & (raw_unified_df['Month'] == month)
            ].copy()
            
            st.success(f"✅ Filtered to {len(filtered_df)} transactions for {selected_month}")
            
            if filtered_df.empty:
                st.error(f"No transactions found for {selected_month}. Please check your files or select a different month.")
                st.stop()
            
            my_bar.progress(50, text="Data Normalized. Starting Intelligence Agent...")
            
            # Phase 2 - Classification
            final_classified_df = process_and_classify(filtered_df)
            
            # Ensure Dates are datetime objects for plotting
            final_classified_df['Date'] = pd.to_datetime(final_classified_df['Date'], dayfirst=True, errors='coerce')
            final_classified_df['Month_Year'] = final_classified_df['Date'].dt.to_period('M').astype(str)
            
            # Add Manual Income as a transaction
            my_bar.progress(70, text="Adding manual income...")
            
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
                
                st.success(f"✅ Added ₪{total_manual_income:,.2f} in manual income")
            else:
                st.warning("⚠️ No income entered - analysis will show expenses only")
            
            # Phase 3 - Save to History
            my_bar.progress(75, text="Updating Historical Timeline...")
            full_history_df = save_to_history(final_classified_df)
            
            # Phase 4 - Generate LLM Insights
            my_bar.progress(90, text="Analyst is writing the story...")
            analyst = FinancialAnalystAgent()
            story_markdown = analyst.generate_monthly_story(final_classified_df, selected_month)
            
            my_bar.progress(100, text="Complete!")
            st.session_state['current_df'] = final_classified_df
            st.session_state['history_df'] = full_history_df
            st.session_state['story'] = story_markdown
            st.session_state['selected_month'] = selected_month
            
        except Exception as e:
            st.error(f"An error occurred during processing: {e}")
            import traceback
            st.error(traceback.format_exc())

# --- 3. The Dashboard Display ---
if 'current_df' in st.session_state:
    curr_df = st.session_state['current_df']
    hist_df = st.session_state['history_df']
    
    # Create Tabs for a clean UI
    tab1, tab2, tab3 = st.tabs(["📊 This Month's Story", "📈 Month-over-Month Timeline", "🗄️ Raw Ledger"])
    
    with tab1:
        st.header("📖 This Month's Financial Story")
        
        # Display the analyst insights with better formatting
        st.markdown("""
        <style>
        .analyst-story {
            font-size: 1.3em;
            line-height: 1.9;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            direction: rtl;
            text-align: right;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .analyst-story h1, .analyst-story h2, .analyst-story h3 {
            color: #ffd700;
            font-size: 1.6em;
            margin-top: 20px;
            direction: rtl;
            text-align: right;
        }
        .analyst-story strong {
            color: #ffd700;
            font-weight: bold;
        }
        .analyst-story p {
            direction: rtl;
            text-align: right;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div class="analyst-story">{st.session_state["story"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📊 Visual Breakdown")
        
        # Filter out Income for the expense pie chart
        expenses_only = curr_df[curr_df['Category'] != 'Income']
        
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                expenses_only, 
                values='Amount', 
                names='Category', 
                title="Expenses by Macro Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
            fig_pie.update_layout(
                font=dict(size=14, family="Arial Black"),
                title_font=dict(size=18, color='#2c3e50'),
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            top_expenses = expenses_only.groupby('Sub_Category')['Amount'].sum().reset_index().sort_values('Amount', ascending=False).head(10)
            fig_bar = px.bar(
                top_expenses,
                x='Sub_Category', 
                y='Amount', 
                title="Top 10 Expense Sub-Categories",
                color='Amount',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(
                font=dict(size=14),
                title_font=dict(size=18, color='#2c3e50'),
                xaxis_title="Category",
                yaxis_title="Amount (₪)",
                showlegend=False
            )
            fig_bar.update_traces(texttemplate='₪%{y:,.0f}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.header("Historical Timeline")
        st.info("As you upload data each month, this chart will build a complete timeline of your family's cash flow.")
        
        if not hist_df.empty:
            # Ensure Date and Amount are properly typed
            hist_df['Date'] = pd.to_datetime(hist_df['Date'], dayfirst=True, errors='coerce')
            hist_df['Amount'] = pd.to_numeric(hist_df['Amount'], errors='coerce')
            hist_df['Month_Year'] = hist_df['Date'].dt.to_period('M').astype(str)
            
            # Separate Income vs Expenses
            hist_df['Type'] = hist_df['Category'].apply(lambda x: 'Income' if x == 'Income' else 'Expenses')
            
            # Group by Month and Type (Income vs Expenses)
            income_expense_timeline = hist_df.groupby(['Month_Year', 'Type'])['Amount'].sum().reset_index()
            
            # Line chart for Income vs Expenses
            fig_income_expense = px.line(
                income_expense_timeline,
                x='Month_Year',
                y='Amount',
                color='Type',
                title="💰 Monthly Income vs Expenses Trend",
                markers=True,
                color_discrete_map={'Income': '#27ae60', 'Expenses': '#e74c3c'}
            )
            fig_income_expense.update_traces(
                line=dict(width=4),
                marker=dict(size=12, line=dict(width=2, color='white'))
            )
            fig_income_expense.update_layout(
                xaxis_title="Month",
                yaxis_title="Amount (₪)",
                legend_title="Type",
                font=dict(size=14),
                title_font=dict(size=20, color='#2c3e50'),
                plot_bgcolor='#f8f9fa',
                paper_bgcolor='white',
                hovermode='x unified'
            )
            st.plotly_chart(fig_income_expense, use_container_width=True)
            
            st.markdown("---")
            
            # Group by Month and Category for detailed breakdown
            hist_grouped = hist_df.groupby(['Month_Year', 'Category'])['Amount'].sum().reset_index()
            
            fig_timeline = px.line(
                hist_grouped, 
                x='Month_Year', 
                y='Amount', 
                color='Category', 
                title="📊 Detailed Category Breakdown Over Time",
                markers=True,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_timeline.update_traces(
                line=dict(width=3),
                marker=dict(size=10)
            )
            fig_timeline.update_layout(
                xaxis_title="Month",
                yaxis_title="Amount (₪)",
                legend_title="Category",
                font=dict(size=14),
                title_font=dict(size=20, color='#2c3e50'),
                plot_bgcolor='#f8f9fa',
                paper_bgcolor='white',
                hovermode='x unified'
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

    with tab3:
        st.header("Data Vault")
        st.dataframe(curr_df, use_container_width=True)