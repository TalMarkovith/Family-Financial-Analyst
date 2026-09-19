import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import pandas as pd

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

load_dotenv()

from tools.analysis_history import get_comparison_insights, save_monthly_analysis
from tools.balance_tracker import update_balance

class FinancialAnalystAgent:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def generate_monthly_story(self, current_df: pd.DataFrame, month_year: str = None, lang: str = 'he') -> str:
        """Analyzes the classified dataframe and generates a narrative story."""
        
        # ── Sign convention: negative = expense, positive = income/refund ──
        # ── Excluded=True transactions are SKIPPED from all calculations ──
        
        # Ensure Excluded column exists
        if 'Excluded' not in current_df.columns:
            current_df = current_df.copy()
            current_df['Excluded'] = False
        
        # Filter out excluded rows from ALL calculations
        active_df = current_df[~current_df['Excluded'].fillna(False).astype(bool)]
        excluded_count = len(current_df) - len(active_df)
        
        # 1. Income = all positive amounts (salaries, refunds, credits)
        income_df = active_df[active_df['Amount'] > 0]
        income = income_df['Amount'].sum()  # Already positive
        
        # 2. Separate Investments from regular expenses
        # Investments are money going out but NOT consumption — they're wealth allocation.
        # Match by Category='Investments' OR the known אנליסט keyword as fallback.
        investments_df = active_df[
            (active_df['Amount'] < 0) &  # Investments are money going out
            (
                (active_df['Category'] == 'Investments') |
                (active_df['Description'].str.contains('אנליסט', case=False, na=False))
            )
        ]
        
        expenses_df = active_df[
            (active_df['Amount'] < 0) &  # Only money going out
            (~active_df.index.isin(investments_df.index))
        ]
        
        # 3. Calculate totals
        # Expenses are negative, use abs() for display
        expenses = expenses_df['Amount'].abs().sum()
        investments = investments_df['Amount'].abs().sum()
        
        # Debug output
        print(f"\n💰 Financial Breakdown:")
        if excluded_count > 0:
            print(f"  ⚠️  Excluded from calculations: {excluded_count} transactions (marked 'Don't Count')")
        print(f"  Total Income: ₪{income:,.2f}")
        print(f"  Total Expenses: ₪{expenses:,.2f} ({len(expenses_df)} transactions)")
        print(f"  Total Investments: ₪{investments:,.2f} ({len(investments_df)} transactions)")
        if len(investments_df) > 0:
            print(f"  Investment transactions:")
            for _, inv in investments_df.iterrows():
                print(f"    - {inv['Description']}: ₪{abs(inv['Amount']):,.2f}")
        
        # 4. Net Savings = Income - Expenses (investments are separate, NOT subtracted)
        # Investments are lump-sum transfers to brokerage accounts — they represent
        # wealth allocation, not consumption. The "savings" metric should show
        # how much more you earned than you spent on living expenses.
        net_savings = income - expenses
        savings_rate = (net_savings / income * 100) if income > 0 else 0
        
        print(f"  Net Savings: ₪{net_savings:,.2f} ({savings_rate:.1f}%)")
        
        # 5. Groupings for the prompt
        expenses_by_category = expenses_df.groupby('Category')['Amount'].apply(lambda x: x.abs().sum()).sort_values(ascending=False)
        top_subcategories = expenses_df.groupby('Sub_Category')['Amount'].apply(lambda x: x.abs().sum()).sort_values(ascending=False).head(10)
        
        investments_breakdown = ""
        if investments > 0:
            investments_by_desc = investments_df.groupby('Description')['Amount'].apply(lambda x: x.abs().sum()).sort_values(ascending=False)
            investments_breakdown = "\n**💎 השקעות וחסכונות לטווח ארוך (לא נספרים כהוצאות!):**\n"
            for desc, amount in investments_by_desc.items():
                if amount > 0:
                    investments_breakdown += f"- {desc}: ₪{amount:,.2f}\n"
            investments_breakdown += f"**סה\"כ השקעות שבוצעו החודש:** ₪{investments:,.2f}\n"
        
        expense_details = "**פירוט הוצאות שוטפות לפי קטגוריה:**\n"
        for category, amount in expenses_by_category.items():
            if amount > 0:
                expense_details += f"- {category}: ₪{amount:,.2f}\n"
        
        expense_details += "\n**תתי-קטגוריות בולטות בהוצאות:**\n"
        for subcategory, amount in top_subcategories.items():
            if amount > 0:
                expense_details += f"- {subcategory}: ₪{amount:,.2f}\n"
        
        expense_details += investments_breakdown
        
        # History integration
        comparison_text = ""
        if month_year:
            comparison_text = get_comparison_insights(month_year, income, expenses, net_savings, savings_rate)
            save_monthly_analysis(
                month_year=month_year, income=income, expenses=expenses,
                net_savings=net_savings, savings_rate=savings_rate,
                top_expenses=top_subcategories.to_dict()
            )
            # Update running balance
            update_balance(month_year, income, expenses, investments, net_savings)
        
        month_context_he = f" לחודש {month_year}" if month_year else ""
        month_context_en = f" for {month_year}" if month_year else ""

        # Investment messaging is decided in CODE, not by an LLM conditional.
        # LLMs cannot reliably evaluate "if investments > savings" and will
        # otherwise parrot "you invested a massive ₪0.00" when nothing was
        # invested. So: only surface investments when there actually were any.
        if investments > 0:
            invest_line_he = f"\n            - 💎 **הון שהופקד להשקעות החודש:** ₪{investments:,.2f}"
            invest_guidance_he = (
                f'2. החודש הופקדו ₪{investments:,.2f} להשקעות — ציין זאת כניהול הון חיובי. '
                f'אל תמציא מהיכן הגיע הכסף.\n'
                f'            3. לעולם אל תציג את ההשקעות כהפסד או כגירעון בעו"ש.'
            )
            invest_line_en = f"\n            - 💎 **Capital invested this month:** ₪{investments:,.2f}"
            invest_guidance_en = (
                f'2. ₪{investments:,.2f} was invested this month — note it as positive capital '
                f'management. Do not invent where the money came from.\n'
                f'            3. Never present investments as a loss or account deficit.'
            )
        else:
            invest_line_he = ""
            invest_guidance_he = (
                '2. החודש לא בוצעו השקעות. אל תזכיר השקעות כלל, אל תברך על השקעה, '
                'ובשום אופן אל תכתוב שהושקע סכום כלשהו (גם לא ₪0).'
            )
            invest_line_en = ""
            invest_guidance_en = (
                '2. No investments were made this month. Do NOT mention investments at all, '
                'do not congratulate on investing, and never state that any amount was invested (not even ₪0).'
            )

        # 5. Build prompt based on language
        if lang == 'he':
            prompt = f"""
            אתה **האנליסט הפיננסי המשפחתי** של טל ורעות. 
            שים לב! "חיסכון נטו" מוגדר כפער בין ההכנסות להוצאות המחיה. ההשקעות הן סעיף נפרד וחיובי.

            📊 **תמונת המצב הפיננסית האמיתית{month_context_he}:**
            - 💰 **הכנסות החודש:** ₪{income:,.2f}
            - 💸 **הוצאות מחיה שוטפות:** ₪{expenses:,.2f}
            - 🎯 **חיסכון חודשי נטו (הכנסות פחות הוצאות):** ₪{net_savings:,.2f} ({savings_rate:.1f}% שיעור חיסכון!){invest_line_he}

            {expense_details}
            {comparison_text}

            **הנחיות קריטיות לכתיבת הניתוח:**
            1. חגוג את החיסכון החודשי! (₪{net_savings:,.2f}). זה מראה שהם חיים הרבה מתחת לרמת ההכנסה שלהם.
            {invest_guidance_he}
            4. הצג 5-8 סעיפי הוצאות בולטים.
            5. כתוב הכל בעברית מימין לשמאל (RTL) בפורמט Markdown נקי ונעים עם אימוג'ים.
            6. אל תמציא מספרים. השתמש רק בנתונים המדויקים שסיפקתי למעלה.
            """
        else:  # English
            prompt = f"""
            You are the **Family Financial Analyst** for Tal & Reut.
            Note: "Net Savings" = Income minus living expenses. Investments are a separate, positive item.

            📊 **Financial Snapshot{month_context_en}:**
            - 💰 **Monthly Income:** ₪{income:,.2f}
            - 💸 **Living Expenses:** ₪{expenses:,.2f}
            - 🎯 **Net Monthly Savings (Income minus Expenses):** ₪{net_savings:,.2f} ({savings_rate:.1f}% savings rate!){invest_line_en}

            {expense_details}
            {comparison_text}

            **Critical writing guidelines:**
            1. Celebrate the monthly savings! (₪{net_savings:,.2f}). This shows they live well below their income level.
            {invest_guidance_en}
            4. Highlight 5-8 notable expense categories.
            5. Write in clean Markdown format with emojis.
            6. Do NOT invent numbers. Use ONLY the exact data provided above.
            """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2 
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ Could not generate analyst insights: {e}"