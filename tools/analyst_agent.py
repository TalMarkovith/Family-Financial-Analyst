import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import pandas as pd

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

load_dotenv()

from tools.analysis_history import get_comparison_insights, save_monthly_analysis

class FinancialAnalystAgent:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def generate_monthly_story(self, current_df: pd.DataFrame, month_year: str = None) -> str:
        """Analyzes the classified dataframe and generates a narrative story."""
        
        # Calculate high-level metrics
        income = current_df[current_df['Category'] == 'Income']['Amount'].sum()
        expenses = current_df[current_df['Category'] != 'Income']['Amount'].sum()
        net_savings = income - expenses
        savings_rate = (net_savings / income * 100) if income > 0 else 0
        
        # Aggregate top expense sub-categories
        top_expenses = current_df[current_df['Category'] != 'Income'].groupby('Sub_Category')['Amount'].sum().sort_values(ascending=False).head(5)
        top_expenses_str = top_expenses.to_string()
        
        # Get comparison with previous month
        comparison_text = ""
        if month_year:
            comparison_text = get_comparison_insights(month_year, income, expenses, net_savings, savings_rate)
            
            # Save this month's analysis for future comparisons
            save_monthly_analysis(
                month_year=month_year,
                income=income,
                expenses=expenses,
                net_savings=net_savings,
                savings_rate=savings_rate,
                top_expenses=top_expenses.to_dict()
            )
        
        month_context = f" for {month_year}" if month_year else ""

        prompt = f"""
        You are the **Family Financial Analyst** for Tal and Reut - an expert advisor who speaks with clarity, warmth, and actionable insights.

        📊 **Financial Snapshot{month_context}:**
        - 💰 **Total Income:** ₪{income:,.2f}
        - 💸 **Total Expenses:** ₪{expenses:,.2f}
        - 🎯 **Net Savings:** ₪{net_savings:,.2f} ({savings_rate:.1f}% savings rate)

        🔝 **Top 5 Spending Categories:**
        {top_expenses_str}

        📈 **Comparison with Previous Month:**
        {comparison_text if comparison_text else "No previous month data available for comparison."}

        **Your Mission:**
        Write an engaging, crystal-clear financial story in **Hebrew (RTL - right to left)** that includes:

        1. **פתיחה חמה** - ברכה חמה עם "כותרת" מהירה על החודש הכלכלי (האם הם הצליחו מעולה? האם יש דאגות?)
        
        2. **המספרים מספרים סיפור** - הסבר את קצב השריפה שלהם במונחים פשוטים:
           - כמה נכנס מול כמה יצא
           - האם שיעור החיסכון בריא? (20%+ מצוין, 10-20% טוב, <10% צריך תשומת לב)
           - תן פרספקטיבה (למשל: "זה אומר שחסכתם כמעט רבע מההכנסה - מעולה!")
           - **אם יש נתוני חודש קודם - הדגש את השינויים!** (עלייה/ירידה בהוצאות, שיפור בחיסכון)
        
        3. **זרקור על ההוצאות** - הדגש 2-3 דפוסים מעניינים:
           - לאן הלך רוב הכסף? (השתמש באימוג'ים כדי להפוך את זה ויזואלי)
           - האם יש הפתעות או הוצאות חריגות?
           - מהלכים חכמים שהם עשו
           - **אם יש השוואה לחודש קודם - הזכר קטגוריות שעלו או ירדו**
        
        4. **מה לעשות עם החיסכון החודש הבא** - תן המלצה ספציפית ומעשית אחת או שתיים:
           - כמה חסכתם? האם כדאי להעביר להשקעות? (קרן פנסיה, קרן השתלמות, מניות)?
           - אילו תחומים לעקוב/לצמצם
           - יעדים להציב **בהתבסס על המגמה מהחודש הקודם**
           - אם יש חוב או הוצאת יתר - תכנית להתאוששות
        
        **Style Guidelines:**
        - Write EVERYTHING in Hebrew from right to left
        - Use **bold** for key numbers and insights  
        - Add relevant emojis (💰 🎯 📈 ⚠️ ✅ 🏦 💳 🎉) to make it scannable
        - Keep it concise but impactful (3-4 short paragraphs)
        - End with encouragement and actionable next steps
        - Focus on NEXT MONTH actions, not "next year"
        - **INTEGRATE the comparison data naturally into your narrative**
        
        Format in clean Markdown with clear Hebrew sections. DO NOT use English headers.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=1
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ Could not generate analyst insights: {e}"