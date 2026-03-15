# tools/translations.py
# EN/HE translations for all UI strings

TRANSLATIONS = {
    'en': {
        # Landing page
        'app_title': 'Family Financial Analytics',
        'app_subtitle': 'AI-powered family expense tracker with intelligent categorization and insights.<br>Upload your bank & credit card files, and let the AI analyst tell your financial story.',
        'select_month': 'Select Month to Analyze',
        'which_month': 'Which month?',
        'start_analysis': '📊 Start Analysis',
        'smart_class_title': 'SMART CLASSIFICATION',
        'smart_class_1': 'Azure OpenAI GPT-4',
        'smart_class_2': 'Vector memory learns',
        'smart_class_3': 'Hebrew merchants',
        'visual_title': 'VISUAL INSIGHTS',
        'visual_1': 'Month comparisons',
        'visual_2': 'Interactive charts',
        'visual_3': 'Pattern detection',
        'analyst_title': 'AI ANALYST',
        'analyst_1': 'Personalized insights',
        'analyst_2': 'Recommendations',
        'analyst_3': 'Investment tips',
        
        # Sidebar
        'monthly_setup': '📅 Monthly Analysis Setup',
        'analyzing_month': 'Which month are you analyzing?',
        'month_help': 'Select the month you want to analyze. Transactions will be filtered to this month.',
        'income_header': '💰 Income for This Month',
        'income_desc': '**Enter the actual income amounts:**',
        'tal_salary': "Tal's Salary (₪)",
        'reut_salary': "Reut's Salary (₪)",
        'other_income': 'Other Income (₪)',
        'total_income': '✅ Total Income: ₪{amount}',
        'no_income': '⚠️ No income entered',
        'file_upload': '📤 File Upload',
        'upload_label': 'Upload Credit Card & Bank files',
        'run_button': 'Run Financial Analyst Agent 🚀',
        'back_home': '← Back to Home',
        
        # Dashboard header
        'dashboard_title': '💰 Family Financial Analyst',
        'dashboard_subtitle': 'AI-powered insights for Tal & Reut',
        
        # Progress
        'progress_saving': 'Files saved. Starting Ingestion Agent...',
        'progress_filtering': 'Filtering transactions for selected month...',
        'progress_classifying': 'Data Normalized. Starting Intelligence Agent...',
        'progress_income': 'Adding manual income...',
        'progress_history': 'Updating Historical Timeline...',
        'progress_story': 'Analyst is writing the story...',
        'progress_complete': 'Complete!',
        
        # Classification results
        'classified_count': '🔍 Classified {count} transactions',
        'added_income': '✅ Added ₪{amount} in manual income',
        'no_income_warning': '⚠️ No income entered - analysis will show expenses only',
        'filtered_count': '✅ Filtered to {count} transactions for {month}',
        'loaded_total': '📅 Loaded {count} total transactions',
        'date_range': '📅 Date range: {min_date} to {max_date}',
        'dates_converting': '⚠️ Dates not in datetime format, converting...',
        'invalid_dates': '⚠️ {count} dates are invalid and will be excluded',
        'no_transactions': 'No transactions found for {month}. Please check your files or select a different month.',
        'select_month_error': 'Please select a month to analyze!',
        
        # Review panel
        'review_title': '🔍 Review New Classifications',
        'review_desc': 'These <strong>{count}</strong> merchants are new — classified by Maps API + LLM. Review and correct before saving to memory. Next time they\'ll be auto-classified!',
        'col_merchant': 'Merchant',
        'col_amount': 'Amount',
        'col_type': 'Type',
        'col_category': 'Category',
        'col_subcategory': 'Sub-Category',
        'type_expense': 'Expense',
        'type_income': 'Income',
        'btn_approve': '✅ Approve & Save to Memory',
        'btn_skip': '⏭️ Skip Review (Don\'t Save)',
        'approve_success': '✅ Saved {count} merchants to memory! Story regenerated with corrections.',
        
        # Tabs
        'tab_story': "📊 This Month's Story",
        'tab_history': '📈 Historical Timeline',
        'tab_raw': '🗄️ Raw Ledger',
        'story_header': '🤖 AI Financial Story',
        'visual_breakdown': '📊 Visual Breakdown',
        'expenses_by_cat': '📊 Expenses by Category',
        'top_expenses': '💸 Top 10 Expenses',
        'pinned_insights': '📌 Pinned Insights',
        'income_vs_expenses': '💰 Income vs Expenses Trend',
        'category_over_time': '📊 Category Breakdown Over Time',
        'raw_data': '🗄️ Raw Transaction Data',
        'pin_story': '📌 Pin Story',
        
        # Balance box
        'running_balance': '💎 Cumulative Balance',
        'balance_label': 'All-Time Net Balance',
        'balance_delta': '{rate}% avg savings rate',
        
        # Reset
        'reset_title': '🗑️ Reset All Data',
        'reset_warning': '⚠️ This will delete all saved data, uploaded files, and learned merchants. Bootstrap memory will be preserved.',
        'reset_confirm': '🗑️ Yes, Delete Everything',
        'reset_success': '✅ All data has been reset! Reloading...',
        'reset_memory_result': '🧠 Memory: kept {kept} bootstrap, deleted {deleted} learned entries',
    },
    'he': {
        # Landing page
        'app_title': 'אנליסט פיננסי משפחתי',
        'app_subtitle': 'מעקב הוצאות משפחתי מבוסס AI עם קטלוג חכם ותובנות.<br>העלו את קבצי הבנק וכרטיסי האשראי, וה-AI ינתח את הסיפור הפיננסי שלכם.',
        'select_month': 'בחרו חודש לניתוח',
        'which_month': 'איזה חודש?',
        'start_analysis': '📊 התחל ניתוח',
        'smart_class_title': 'סיווג חכם',
        'smart_class_1': 'Azure OpenAI GPT-4',
        'smart_class_2': 'זיכרון וקטורי לומד',
        'smart_class_3': 'מזהה בתי עסק בעברית',
        'visual_title': 'תובנות ויזואליות',
        'visual_1': 'השוואה חודשית',
        'visual_2': 'גרפים אינטראקטיביים',
        'visual_3': 'זיהוי דפוסים',
        'analyst_title': 'אנליסט AI',
        'analyst_1': 'תובנות מותאמות אישית',
        'analyst_2': 'המלצות',
        'analyst_3': 'טיפים להשקעות',
        
        # Sidebar
        'monthly_setup': '📅 הגדרות ניתוח חודשי',
        'analyzing_month': 'איזה חודש אתם מנתחים?',
        'month_help': 'בחרו את החודש לניתוח. העסקאות יסוננו לחודש זה.',
        'income_header': '💰 הכנסות החודש',
        'income_desc': '**הזינו את סכומי ההכנסה:**',
        'tal_salary': 'משכורת טל (₪)',
        'reut_salary': 'משכורת רעות (₪)',
        'other_income': 'הכנסות אחרות (₪)',
        'total_income': '✅ סה"כ הכנסות: ₪{amount}',
        'no_income': '⚠️ לא הוזנו הכנסות',
        'file_upload': '📤 העלאת קבצים',
        'upload_label': 'העלו קבצי כרטיסי אשראי ובנק (עו"ש)',
        'run_button': 'הפעל אנליסט פיננסי 🚀',
        'back_home': '→ חזרה לדף הבית',
        
        # Dashboard header
        'dashboard_title': '💰 אנליסט פיננסי משפחתי',
        'dashboard_subtitle': 'תובנות מבוססות AI עבור טל ורעות',
        
        # Progress
        'progress_saving': 'קבצים נשמרו. מתחיל עיבוד...',
        'progress_filtering': 'מסנן עסקאות לחודש הנבחר...',
        'progress_classifying': 'נתונים מנורמלים. מפעיל סוכן סיווג...',
        'progress_income': 'מוסיף הכנסות ידניות...',
        'progress_history': 'מעדכן ציר זמן היסטורי...',
        'progress_story': 'האנליסט כותב את הסיפור...',
        'progress_complete': 'הושלם!',
        
        # Classification results
        'classified_count': '🔍 סווגו {count} עסקאות',
        'added_income': '✅ נוספו ₪{amount} הכנסות ידניות',
        'no_income_warning': '⚠️ לא הוזנו הכנסות - הניתוח יציג הוצאות בלבד',
        'filtered_count': '✅ סוננו {count} עסקאות לחודש {month}',
        'loaded_total': '📅 נטענו {count} עסקאות בסה"כ',
        'date_range': '📅 טווח תאריכים: {min_date} עד {max_date}',
        'dates_converting': '⚠️ תאריכים לא בפורמט תקין, ממיר...',
        'invalid_dates': '⚠️ {count} תאריכים לא תקינים ויוסרו',
        'no_transactions': 'לא נמצאו עסקאות לחודש {month}. בדקו את הקבצים או בחרו חודש אחר.',
        'select_month_error': 'יש לבחור חודש לניתוח!',
        
        # Review panel
        'review_title': '🔍 סקירת סיווגים חדשים',
        'review_desc': '<strong>{count}</strong> בתי עסק חדשים — סווגו ע"י Maps API + LLM. בדקו ותקנו לפני שמירה בזיכרון. בפעם הבאה הם יסווגו אוטומטית!',
        'col_merchant': 'בית עסק',
        'col_amount': 'סכום',
        'col_type': 'סוג',
        'col_category': 'קטגוריה',
        'col_subcategory': 'תת-קטגוריה',
        'type_expense': 'הוצאה',
        'type_income': 'הכנסה',
        'btn_approve': '✅ אשר ושמור בזיכרון',
        'btn_skip': '⏭️ דלג (בלי שמירה)',
        'approve_success': '✅ נשמרו {count} בתי עסק בזיכרון! הסיפור נוצר מחדש עם התיקונים.',
        
        # Tabs
        'tab_story': '📊 הסיפור החודשי',
        'tab_history': '📈 ציר זמן היסטורי',
        'tab_raw': '🗄️ נתונים גולמיים',
        'story_header': '🤖 סיפור פיננסי AI',
        'visual_breakdown': '📊 פירוט ויזואלי',
        'expenses_by_cat': '📊 הוצאות לפי קטגוריה',
        'top_expenses': '💸 10 ההוצאות הגדולות',
        'pinned_insights': '📌 תובנות שנשמרו',
        'income_vs_expenses': '💰 מגמת הכנסות מול הוצאות',
        'category_over_time': '📊 פירוט קטגוריות לאורך זמן',
        'raw_data': '🗄️ נתוני עסקאות גולמיים',
        'pin_story': '📌 שמור סיפור',
        
        # Balance box
        'running_balance': '💎 מאזן מצטבר',
        'balance_label': 'מאזן נטו כולל',
        'balance_delta': '{rate}% ממוצע חיסכון',
        
        # Reset
        'reset_title': '🗑️ איפוס כל הנתונים',
        'reset_warning': '⚠️ פעולה זו תמחק את כל הנתונים השמורים, הקבצים שהועלו, והעסקים שנלמדו. זיכרון הבסיס יישמר.',
        'reset_confirm': '🗑️ כן, מחק הכל',
        'reset_success': '✅ כל הנתונים אופסו! טוען מחדש...',
        'reset_memory_result': '🧠 זיכרון: נשמרו {kept} בסיס, נמחקו {deleted} נלמדים',
    }
}

def t(key: str, lang: str = 'en', **kwargs) -> str:
    """Get translated string. Use kwargs for format placeholders."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


# ── Category & Sub-Category display translations ──
# Keys are the canonical English values used in the dataframe & memory.
# Values are translated display labels.

CATEGORY_DISPLAY = {
    'en': {
        'Housing_Fixed': 'Housing & Fixed',
        'Insurance_Health': 'Insurance & Health',
        'Kids_Family': 'Kids & Family',
        'Transportation': 'Transportation',
        'Variable_Daily': 'Variable Daily',
        'Leisure_Grooming': 'Leisure & Grooming',
        'Food': 'Food',
        'Food_Delivery': 'Food Delivery',
        'Pharm': 'Pharmacy',
        'Health': 'Health',
        'Insurance': 'Insurance',
        'Home': 'Home',
        'Investments': 'Investments',
        'Income': 'Income',
        'Rio': 'Rio',
        'Leisure': 'Leisure',
    },
    'he': {
        'Housing_Fixed': 'דיור וקבועות',
        'Insurance_Health': 'ביטוח ובריאות',
        'Kids_Family': 'ילדים ומשפחה',
        'Transportation': 'תחבורה',
        'Variable_Daily': 'הוצאות יומיומיות',
        'Leisure_Grooming': 'פנאי וטיפוח',
        'Food': 'מזון',
        'Food_Delivery': 'משלוחי אוכל',
        'Pharm': 'בית מרקחת',
        'Health': 'בריאות',
        'Insurance': 'ביטוח',
        'Home': 'בית',
        'Investments': 'השקעות',
        'Income': 'הכנסות',
        'Rio': 'ריו',
        'Leisure': 'פנאי',
    },
}

SUBCATEGORY_DISPLAY = {
    'en': {
        'Rent_Mortgage': 'Rent / Mortgage',
        'Utilities_Arnona_Elec_Water_Gas': 'Utilities (Arnona, Elec, Water, Gas)',
        'Communication': 'Communication',
        'Maintenance_Vaad_Cleaner': 'Maintenance (Vaad, Cleaner)',
        'Insurances': 'Insurances',
        'Kupat_Holim': 'Kupat Holim',
        'Private_Medical': 'Private Medical',
        'Gan_Education': 'Kindergarten / Education',
        'Baby_Equipment_Pharm': 'Baby Equipment & Pharmacy',
        'Kids_Clothing_Toys': 'Kids Clothing & Toys',
        'Car_Gas_Tolls': 'Car Gas & Tolls',
        'Public_Transit_Taxi': 'Public Transit & Taxi',
        'Parking_Tolls': 'Parking & Tolls',
        'Car_Maintenance_Licensing': 'Car Maintenance & Licensing',
        'Groceries_Supermarket': 'Groceries & Supermarket',
        'Dining_Restaurants_Wolt': 'Dining & Restaurants',
        'Home_Furniture_Decor': 'Home Furniture & Decor',
        'Clothing_Shoes': 'Clothing & Shoes',
        'Gifts_Events': 'Gifts & Events',
        'General_Shopping': 'General Shopping',
        'Subscriptions': 'Subscriptions',
        'Personal_Care_Hair_Nails': 'Personal Care (Hair, Nails)',
        'Hobbies_Entertainment_Vacation': 'Hobbies, Entertainment & Vacation',
        'Coffee_Restaurants': 'Coffee & Restaurants',
        'Pharm': 'Pharmacy',
        'Medical_Insurance': 'Medical Insurance',
        'sport_club_gym': 'Sport Club & Gym',
        'Life_Insurance': 'Life Insurance',
        'Medical_Private_Insurance': 'Medical Private Insurance',
        'Direct_Online_Shopping': 'Direct / Online Shopping',
        'Savings_Analyst_Brokerage': 'Savings & Brokerage',
        'Tal_Salary': "Tal's Salary",
        'Reut_Salary': "Reut's Salary",
        'Other_Income_Bit': 'Other Income (Bit)',
        'Rio_Food': 'Rio Food',
        'Rio_Health': 'Rio Health',
        'Rio_Accessories': 'Rio Accessories',
        'Tal_Specials': "Tal's Specials",
        'Unknown': 'Unknown',
    },
    'he': {
        'Rent_Mortgage': 'שכירות / משכנתא',
        'Utilities_Arnona_Elec_Water_Gas': 'ארנונה, חשמל, מים, גז',
        'Communication': 'תקשורת',
        'Maintenance_Vaad_Cleaner': 'ועד בית וניקיון',
        'Insurances': 'ביטוחים',
        'Kupat_Holim': 'קופת חולים',
        'Private_Medical': 'רפואה פרטית',
        'Gan_Education': 'גן / חינוך',
        'Baby_Equipment_Pharm': 'ציוד תינוקות ובית מרקחת',
        'Kids_Clothing_Toys': 'ביגוד וצעצועים לילדים',
        'Car_Gas_Tolls': 'דלק ואגרות',
        'Public_Transit_Taxi': 'תחבורה ציבורית ומוניות',
        'Parking_Tolls': 'חניה ואגרות',
        'Car_Maintenance_Licensing': 'טיפול ורישוי רכב',
        'Groceries_Supermarket': 'מכולת וסופרמרקט',
        'Dining_Restaurants_Wolt': 'מסעדות ווולט',
        'Home_Furniture_Decor': 'ריהוט ועיצוב הבית',
        'Clothing_Shoes': 'ביגוד ונעליים',
        'Gifts_Events': 'מתנות ואירועים',
        'General_Shopping': 'קניות כלליות',
        'Subscriptions': 'מנויים',
        'Personal_Care_Hair_Nails': 'טיפוח אישי (שיער, ציפורניים)',
        'Hobbies_Entertainment_Vacation': 'תחביבים, בידור וחופשות',
        'Coffee_Restaurants': 'קפה ומסעדות',
        'Pharm': 'בית מרקחת',
        'Medical_Insurance': 'ביטוח רפואי',
        'sport_club_gym': 'מועדון ספורט / חדר כושר',
        'Life_Insurance': 'ביטוח חיים',
        'Medical_Private_Insurance': 'ביטוח רפואי פרטי',
        'Direct_Online_Shopping': 'קניות ישירות / אונליין',
        'Savings_Analyst_Brokerage': 'חיסכון וברוקר',
        'Tal_Salary': 'משכורת טל',
        'Reut_Salary': 'משכורת רעות',
        'Other_Income_Bit': 'הכנסה אחרת (ביט)',
        'Rio_Food': 'אוכל לריו',
        'Rio_Health': 'בריאות ריו',
        'Rio_Accessories': 'אביזרים לריו',
        'Tal_Specials': 'מיוחדים של טל',
        'Unknown': 'לא ידוע',
    },
}


def cat_display(canonical: str, lang: str = 'en') -> str:
    """Return the display label for a category key."""
    return CATEGORY_DISPLAY.get(lang, CATEGORY_DISPLAY['en']).get(canonical, canonical)


def sub_display(canonical: str, lang: str = 'en') -> str:
    """Return the display label for a sub-category key."""
    return SUBCATEGORY_DISPLAY.get(lang, SUBCATEGORY_DISPLAY['en']).get(canonical, canonical)
