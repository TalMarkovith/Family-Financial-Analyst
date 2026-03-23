# Demo Setup Scripts

This folder contains all scripts and resources for setting up demo data for LinkedIn recordings and presentations.

## Scripts

### Data Generation
- **`generate_demo_data.py`**: Creates realistic Israeli family financial data for a full year (2025)
  - Generates 1,246 transactions across 12 months
  - 100 unique Israeli merchants with authentic Hebrew names
  - Guaranteed 2 salary transactions per month
  - Output: 36 CSV files in `data/demo/` (3 sources × 12 months)

### Memory & Classification
- **`bootstrap_demo_memory.py`**: Loads 100 merchant classifications into Azure AI Search
  - Creates vector embeddings for instant recognition
  - Achieves 100% classification hit rate
  - No LLM calls needed during demo

### Data Loading
- **`preload_demo_history.py`**: Loads Jan-Nov 2025 data into the system
  - Processes and classifies all transactions
  - Updates running_balance.json and monthly_analysis_history.json
  - Leaves December for live demo upload

### Ledger Management
- **`create_realistic_ledger.py`**: Creates historical_ledger.csv with proper category distribution
  - Uses Israeli family expense patterns
  - Distributes transactions across 11 expense categories
  - Ensures connected lines in month-over-month charts

- **`create_synthetic_ledger.py`**: Creates minimal synthetic ledger from running_balance.json
  - Quick alternative for basic charts
  - Monthly summary entries only

- **`rebuild_ledger_fast.py`**: Rebuilds ledger from demo CSV files
- **`rebuild_ledger_from_demo.py`**: Full rebuild with classification
- **`quick_rebuild_ledger.py`**: Fast rebuild without classification

### Utilities
- **`cleanup_december.py`**: Removes December 2025 from all data stores
  - Cleans running_balance.json
  - Cleans monthly_analysis_history.json
  - Cleans historical_ledger.csv
  - Essential for preparing clean demo state

- **`view_full_year.py`**: Displays cumulative statistics across all loaded months
  - Shows income, expenses, investments breakdown
  - Displays month-by-month trends
  - Highlights best/worst months

## Demo Workflow

1. **Initial Setup** (one time):
   ```bash
   python3.12 demo_setup/generate_demo_data.py
   python3.12 demo_setup/bootstrap_demo_memory.py
   ```

2. **Before Recording**:
   ```bash
   python3.12 demo_setup/cleanup_december.py
   python3.12 demo_setup/create_realistic_ledger.py
   python3.12 demo_setup/preload_demo_history.py
   ```

3. **During Recording**:
   - Upload December 2025 files from `data/demo/`
   - Demonstrate instant AI classification
   - Show month-over-month comparisons
   - Highlight year-end analysis

4. **After Recording**:
   ```bash
   python3.12 demo_setup/cleanup_december.py
   ```

## Data Files

Demo data is stored in:
- **`data/demo/`**: 36 CSV files (Jan-Dec 2025) + full year CSV
- **`data/demo/demo_classifications.json`**: 100 merchant-to-category mappings

## Notes

- All scripts assume you're running from the project root directory
- December files should be kept in `data/demo/` not `data/raw/` to avoid auto-processing
- The realistic ledger uses Israeli family expense distribution (Food 30%, Housing 25%, etc.)
