# Family Financial Analyst

Streamlit app that turns bank and credit-card exports into expense analysis and insights in Hebrew.
- `app.py`: file ingestion and the AI analyst.
- `pages/1_📊_Dashboard.py`: read-only view of expenses.
- `pages/2_💼_Investments.py`: read-only view of investments.
- `tools/`: ingestion, classification and dashboard data helpers.

Run with `python3 -m streamlit run app.py` (configurations in `.claude/launch.json`).

## Investments and long-term savings

Investment management for Tal and Reut (pensions, provident and study funds, investment provident funds, the Excellence brokerage account and insurance) is also done in sessions here. The data does **not** live in this repo. It lives in a separate folder:

`~/projects/tal-reut-investment/`
| Path | What it holds |
|---|---|
| `03_ניתוח/portfolio_data.json` | **Source of truth.** One entry per product: owner, provider, category, track, balance, monthly deposit, fees and as-of date. Also the brokerage holdings and the insurance policies. |
| `scripts/build_all.py` | Run after editing the JSON. Rebuilds `03_ניתוח/ניתוח תיק משפחתי.xlsx`, `04_דשבורד/dashboard.html` and `03_ניתוח/portfolio_summary.json`. |
| `03_ניתוח/portfolio_summary.json` | Computed totals. The investments page reads this file. Override its path with `INVESTMENTS_SUMMARY_PATH`. |
| `01_מקורות/` | Raw source documents: advisor reports, Excellence exports, recordings. |
| `02_תמלולים/` | Meeting transcripts and summaries. Read the latest summary first for current status and open action items. |
| `README.md` | Folder layout and the update workflow. |

To update the investments:
1. Edit `portfolio_data.json` in the investments folder, not this repo.
2. Run `python3 scripts/build_all.py` from `~/projects/tal-reut-investment`.
3. The investments page picks up the change within a minute, because the page caches data for 60s.

Never copy investment data into this repo. `.gitignore` already excludes `*.json` and `*.xlsx`; keep it that way.

## Privacy rules (all financial data)
- Never write ID numbers, bank/account/policy numbers, phone numbers or one-time codes into analysis files, the JSON or this repo. Use internal ids such as `גמל-ט-א`.
- Before processing a new document, ask the user to redact those fields. If a transcript or file contains them, mask them before saving.
- Never ask for or use the user's login credentials for any financial site. The user signs in themselves. Work from the reports they export.
- Do not publish financial data to Artifacts or any external service. Dashboards stay local files.
- You are not a licensed financial advisor. Map, compute and explain; decisions belong to the user and their agent.
