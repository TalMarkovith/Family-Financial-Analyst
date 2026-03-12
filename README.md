# Family Financial Analyst 💰

An intelligent family financial analysis system powered by Azure OpenAI, designed to help families track expenses, analyze spending patterns, and get actionable insights in Hebrew.

## Features

- 📊 **Multi-Source Ingestion**: Parse CSV/Excel files from Israeli banks and credit cards (Max, Isracard, Bank Discount)
- 🤖 **AI-Powered Classification**: Uses Azure OpenAI GPT-4 + vector memory for intelligent transaction categorization
- 🧠 **Semantic Memory**: Azure AI Search vector database learns from your classifications
- 📈 **Beautiful Visualizations**: Interactive charts with month-over-month comparisons
- 💬 **Hebrew Financial Analyst**: LLM-generated insights and recommendations in Hebrew (RTL)
- 🔄 **Historical Tracking**: Automatic comparison with previous months
- ✅ **Manual Income Entry**: Easy income tracking with validation

## Tech Stack

- **Python 3.12**
- **Azure OpenAI** (GPT-4o, text-embedding-ada-002)
- **Azure AI Search** (Vector database)
- **Streamlit** (Web UI)
- **Pandas** (Data processing)
- **Plotly** (Interactive visualizations)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/TalMarkovith/Family-Financial-Analyst.git
cd Family-Financial-Analyst
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your Azure credentials:
```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your_embedding_deployment

AZURE_AI_SEARCH_ENDPOINT=your_search_endpoint
AZURE_AI_SEARCH_API_KEY=your_search_key
AZURE_AI_SEARCH_INDEX_NAME=merchant-classifications
```

5. Create the vector database index:
```bash
python scripts/create_vector_db_index.py
```

6. Bootstrap with known merchants (optional):
```bash
python scripts/bootstrap_memory.py
```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

Then:
1. Select the month you want to analyze
2. Enter income amounts (Tal's salary, Reut's salary, other income)
3. Upload your bank/credit card files (CSV or Excel)
4. Click "Run Financial Analyst Agent 🚀"

## Financial Taxonomy

The system classifies transactions into:
- **Income**: Tal_Salary, Reut_Salary, Other_Income_Bit
- **Housing_Fixed**: Rent_Mortgage, Utilities, Communication, Maintenance
- **Insurance_Health**: Insurances, Kupat_Holim, Private_Medical
- **Kids_Family**: Gan_Education, Baby_Equipment_Pharm, Kids_Clothing_Toys
- **Transportation**: Car_Gas_Tolls, Public_Transit_Taxi, Car_Maintenance
- **Variable_Daily**: Groceries, Dining_Restaurants, Shopping, Gifts
- **Leisure_Grooming**: Subscriptions, Personal_Care, Hobbies_Entertainment
- **Investments**: Savings_Analyst_Brokerage

## Project Structure

```
family_financial_expense/
├── app.py                          # Streamlit web interface
├── classifier_agent.py             # Main classification orchestrator
├── agents/
│   └── prompts.py                  # LLM prompt templates
├── tools/
│   ├── credit_card_ingestion.py    # File parsing (CSV/Excel)
│   ├── classify_dataframe.py       # AI classification logic
│   ├── memory_manager.py           # Vector database operations
│   ├── analyst_agent.py            # Financial story generation
│   ├── analysis_history.py         # Month-over-month comparisons
│   └── maps_lookup.py              # Google Maps context
├── scripts/
│   ├── create_vector_db_index.py   # Setup Azure AI Search index
│   ├── bootstrap_memory.py         # Seed with known merchants
│   └── clean_duplicates.py         # Remove duplicate entries
├── utils/
│   └── ssl_fix.py                  # Corporate SSL certificate handling
└── data/
    └── processed/                   # Historical data storage
```

## Features in Detail

### Intelligent Classification
1. **Salary Auto-Detection**: Recognizes Hebrew salary keywords (משכורת)
2. **Vector Memory**: Semantic search finds similar merchants
3. **LLM Fallback**: GPT-4 classifies new merchants with Google Maps context
4. **Learning System**: Saves classifications for future use

### Month Selection & Filtering
- Analyze any of the last 12 months
- Transactions automatically filtered by selected month
- Manual income entry (no auto-detection confusion)

### Visualizations
- 📊 Expense pie chart by category
- 📈 Top 10 expense categories bar chart
- 💰 Income vs Expenses timeline (month-over-month)
- 🎨 Beautiful color schemes with RTL Hebrew support

### Financial Analyst (LLM)
- Hebrew narrative in RTL format
- Compares with previous month automatically
- Actionable recommendations for next month
- Investment suggestions based on savings

## SSL Certificate Handling

For corporate environments with SSL inspection (Netskope), the system automatically:
- Extracts root CA certificates
- Creates a combined certificate bundle
- Configures all Azure connections

## License

MIT

## Author

Tal Markovith

---

Built with ❤️ for smart family financial management
