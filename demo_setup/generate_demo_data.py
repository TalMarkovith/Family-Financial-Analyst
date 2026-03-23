"""
Demo Data Generator for Family Financial Analyst
Generates a full year of realistic Israeli family financial transactions
to showcase the system's AI classification and analysis capabilities.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class DemoDataGenerator:
    def __init__(self):
        # Define realistic Israeli merchants by category
        self.merchants = {
            'Income': {
                'Tal_Salary': [
                    ('בנק פועלים משכורת טל', 22000, 23000),
                ],
                'Reut_Salary': [
                    ('בנק לאומי משכורת רעות', 18000, 19000),
                ],
                'Other_Income_Bit': [
                    ('ביט החזר מס', 500, 2000),
                    ('החזר ביטוח לאומי', 300, 800),
                ]
            },
            'Housing_Fixed': {
                'Rent_Mortgage': [
                    ('הו"ק לאורן ויפאת שפי', 6500, 6500),
                    ('דסק-משכנתא', 5800, 5800),
                ],
                'Utilities_Arnona_Elec_Water_Gas': [
                    ('חברת חשמל', 450, 650),
                    ('מי גבעתיים', 180, 220),
                    ('סלקום אנרגיה גז', 150, 200),
                    ('עיריית גבעתיים ארנונה', 580, 620),
                ],
                'Communication': [
                    ('סלקום טלפון', 89, 99),
                    ('פרטנר אינטרנט', 120, 150),
                    ('הוט חבילה דיגיטלית', 180, 200),
                ],
                'Maintenance_Vaad_Cleaner': [
                    ('ועד בית', 450, 500),
                    ('ניקיון חודשי', 300, 350),
                ]
            },
            'Insurance_Health': {
                'Insurances': [
                    ('ביטוח לאומי', 1200, 1400),
                ],
                'Kupat_Holim': [
                    ('קרן מכבי', 280, 320),
                ],
                'Private_Medical': [
                    ('מנורה מבטחים בריאות', 450, 550),
                ]
            },
            'Health': {
                'Medical_Insurance': [
                    ('מכבי שירותי בריאות', 200, 300),
                ],
                'sport_club_gym': [
                    ('הולמס פלייס', 299, 399),
                    ('upapp חדר כושר', 149, 199),
                ]
            },
            'Pharm': {
                'Pharm': [
                    ('סופר-פארם', 80, 250),
                    ('דראגסטור קוסמטיקה', 60, 180),
                    ('ניו-פארם', 70, 200),
                ]
            },
            'Kids_Family': {
                'Gan_Education': [
                    ('מוסדות חינוך גבעתיים', 1800, 2200),
                    ('ויצו גן ילדים', 1500, 1800),
                    ('פעילות חוג ריקוד', 180, 250),
                ],
                'Baby_Equipment_Pharm': [
                    ('בייבי לאב', 150, 400),
                    ('יולדות ותינוקות', 100, 350),
                    ('תינוק בר', 80, 250),
                ],
                'Kids_Clothing_Toys': [
                    ('זארה ילדים', 150, 400),
                    ('נקסט ילדים', 200, 450),
                    ('צעצועי גמילות', 100, 300),
                    ('חנות הצעצועים', 120, 350),
                ]
            },
            'Transportation': {
                'Car_Gas_Tolls': [
                    ('דור אלון תחנת דלק', 250, 350),
                    ('פז תדלוק', 240, 340),
                    ('סונול אנרגיה', 260, 360),
                    ('דלק מוטור', 245, 345),
                ],
                'Public_Transit_Taxi': [
                    ('YANGO נסיעה', 35, 80),
                    ('גט-טקסי', 40, 90),
                    ('רב-קו אוטובוס', 20, 45),
                ],
                'Parking_Tolls': [
                    ('פנגו חניה', 15, 40),
                    ('חניון עזריאלי', 25, 50),
                ],
                'Car_Maintenance_Licensing': [
                    ('מוסך הכל לרכב', 300, 800),
                    ('רישוי רכב', 1200, 1400),
                    ('ביטוח רכב חובה', 850, 950),
                ]
            },
            'Food': {
                'Groceries_Supermarket': [
                    ('שופרסל שלי נורדאו', 300, 600),
                    ('רמי לוי שיווק השיכון', 250, 550),
                    ('מחסני השוק', 200, 450),
                    ('AM:PM מיני מרקט', 30, 80),
                    ('כלל מרקט', 150, 350),
                    ('יינות ביתן', 80, 200),
                    ('שוק הכרמל פירות', 60, 150),
                ],
                'Coffee_Restaurants': [
                    ('ארומה קפה', 25, 60),
                    ('קפה גרג', 30, 70),
                    ('רולדין', 20, 50),
                    ('קפה לנדוור', 28, 65),
                ]
            },
            'Food_Delivery': {
                'Dining_Restaurants_Wolt': [
                    ('וולט משלוחים', 80, 180),
                    ('וולט WOLT', 70, 160),
                    ('מסעדת לחם בשר', 120, 250),
                    ('טאבולה', 100, 200),
                    ('נחמן', 90, 180),
                    ('בנדיקט', 110, 220),
                    ('פיצה האט', 80, 150),
                    ('בורגר סאלון', 85, 160),
                ]
            },
            'Variable_Daily': {
                'Home_Furniture_Decor': [
                    ('איקאה', 200, 800),
                    ('פנדה הום', 150, 600),
                    ('זארה הום', 100, 400),
                ],
                'Clothing_Shoes': [
                    ('זארה תל אביב', 200, 600),
                    ('מנגו אופנה', 180, 550),
                    ('H&M דיזנגוף', 150, 450),
                    ('קסטרו', 170, 500),
                    ('נעלי שופרא', 250, 450),
                ],
                'Gifts_Events': [
                    ('זר פור יו', 150, 300),
                    ('סטימצקי ספרים', 80, 200),
                    ('חנות מתנות', 100, 250),
                ],
                'General_Shopping': [
                    ('דיזיין ועיצוב', 100, 300),
                    ('קניון עזריאלי', 150, 400),
                ]
            },
            'Leisure_Grooming': {
                'Subscriptions': [
                    ('SPOTIFY', 19.90, 19.90),
                    ('נטפליקס NETFLIX', 54.90, 54.90),
                    ('OPENAI CHATGPT', 20, 20),
                    ('אפל Apple iCloud', 9.90, 9.90),
                ],
                'Personal_Care_Hair_Nails': [
                    ('מספרה סטייל', 120, 180),
                    ('ציפורניים מניקור', 100, 150),
                    ('ספא קוסמטיקה', 200, 400),
                ],
                'Hobbies_Entertainment_Vacation': [
                    ('סינמה סיטי', 80, 120),
                    ('תאטרון הבימה', 150, 300),
                    ('כרטיס טיסה', 800, 2500),
                    ('מלון לילה אחד', 400, 800),
                ]
            },
            'Leisure': {
                'Tal_Specials': [
                    ('פלייסטיישן PLAYSTATION', 199, 299),
                    ('חנות גיימינג', 150, 400),
                    ('ספורט זקס ציוד', 200, 500),
                ]
            },
            'Home': {
                'Direct_Online_Shopping': [
                    ('ALIEXPRESS', 50, 200),
                    ('KSP קיי אס פי', 150, 600),
                    ('AMAZON', 100, 400),
                ]
            },
            'Investments': {
                'Savings_Analyst_Brokerage': [
                    ('אנליסט השקעות', 2000, 5000),
                ]
            },
            'Rio': {
                'Rio_Food': [
                    ('אנימל חנות חיות', 150, 300),
                    ('פטזון ריו', 100, 250),
                ],
                'Rio_Health': [
                    ('וטרינר ריו', 200, 500),
                ],
                'Rio_Accessories': [
                    ('צעצועים לכלבים', 50, 150),
                ]
            }
        }
        
        # Monthly frequency for each category (how many transactions per month)
        self.frequency = {
            'Income': {'Tal_Salary': 1, 'Reut_Salary': 1, 'Other_Income_Bit': 0.3},
            'Housing_Fixed': {
                'Rent_Mortgage': 1, 'Utilities_Arnona_Elec_Water_Gas': 3,
                'Communication': 3, 'Maintenance_Vaad_Cleaner': 2
            },
            'Insurance_Health': {'Insurances': 1, 'Kupat_Holim': 1, 'Private_Medical': 1},
            'Health': {'Medical_Insurance': 0.5, 'sport_club_gym': 1},
            'Pharm': {'Pharm': 4},
            'Kids_Family': {
                'Gan_Education': 1, 'Baby_Equipment_Pharm': 3, 'Kids_Clothing_Toys': 2
            },
            'Transportation': {
                'Car_Gas_Tolls': 6, 'Public_Transit_Taxi': 8, 'Parking_Tolls': 10,
                'Car_Maintenance_Licensing': 0.3
            },
            'Food': {'Groceries_Supermarket': 20, 'Coffee_Restaurants': 12},
            'Food_Delivery': {'Dining_Restaurants_Wolt': 8},
            'Variable_Daily': {
                'Home_Furniture_Decor': 1, 'Clothing_Shoes': 2,
                'Gifts_Events': 0.5, 'General_Shopping': 1.5
            },
            'Leisure_Grooming': {
                'Subscriptions': 1, 'Personal_Care_Hair_Nails': 1,
                'Hobbies_Entertainment_Vacation': 0.5
            },
            'Leisure': {'Tal_Specials': 0.5},
            'Home': {'Direct_Online_Shopping': 2},
            'Investments': {'Savings_Analyst_Brokerage': 1},
            'Rio': {'Rio_Food': 4, 'Rio_Health': 0.2, 'Rio_Accessories': 0.5}
        }
    
    def generate_transaction(self, merchant_data, date, owner):
        """Generate a single transaction"""
        merchant_name, min_amount, max_amount = merchant_data
        amount = round(random.uniform(min_amount, max_amount), 2)
        
        return {
            'Date': date,
            'Description': merchant_name,
            'Amount': amount,
            'Owner': owner,
            'Source': random.choice(['Max', 'Isracard', 'Bank Discount'])
        }
    
    def generate_monthly_transactions(self, year, month):
        """Generate all transactions for a specific month"""
        transactions = []
        
        # Determine number of days in month
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - datetime(year, month, 1)).days
        
        for category, subcategories in self.merchants.items():
            for sub_category, merchant_list in subcategories.items():
                # Get frequency for this subcategory
                freq = self.frequency.get(category, {}).get(sub_category, 1)
                
                # CRITICAL: Guarantee at least 1 transaction for salaries!
                if category == 'Income' and 'Salary' in sub_category:
                    num_transactions = 1  # Always exactly 1 salary per month
                else:
                    num_transactions = int(np.random.poisson(freq))
                
                for _ in range(num_transactions):
                    # Random day in month
                    day = random.randint(1, days_in_month)
                    date = datetime(year, month, day).strftime('%Y-%m-%d')
                    
                    # Random merchant from this subcategory
                    merchant_data = random.choice(merchant_list)
                    
                    # Determine owner
                    if category == 'Income':
                        if 'Tal' in sub_category:
                            owner = 'Tal'
                        elif 'Reut' in sub_category:
                            owner = 'Reut'
                        else:
                            owner = random.choice(['Tal', 'Reut'])
                    else:
                        owner = random.choice(['Tal', 'Reut', 'Shared'])
                    
                    transaction = self.generate_transaction(merchant_data, date, owner)
                    
                    # Income is positive, expenses are negative
                    if category != 'Income':
                        transaction['Amount'] = -transaction['Amount']
                    
                    transactions.append(transaction)
        
        return transactions
    
    def generate_yearly_data(self, year=2025):
        """Generate a full year of transactions"""
        all_transactions = []
        
        print(f"🎬 Generating demo data for {year}...")
        
        for month in range(1, 13):
            print(f"  📅 Month {month:02d}/{year}...")
            monthly_transactions = self.generate_monthly_transactions(year, month)
            all_transactions.extend(monthly_transactions)
            print(f"     Generated {len(monthly_transactions)} transactions")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_transactions)
        
        # Sort by date
        df = df.sort_values('Date').reset_index(drop=True)
        
        print(f"\n✅ Generated {len(df)} total transactions for {year}")
        print(f"   💰 Total Income: ₪{df[df['Amount'] > 0]['Amount'].sum():,.2f}")
        print(f"   💸 Total Expenses: ₪{df[df['Amount'] < 0]['Amount'].abs().sum():,.2f}")
        
        return df
    
    def export_to_csv(self, df, output_dir='data/demo'):
        """Export data to CSV files by month and source"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n📁 Exporting to {output_dir}...")
        
        # Export by month and source for realistic demo
        df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
        
        files_created = []
        
        for month_period in df['Month'].unique():
            month_df = df[df['Month'] == month_period].copy()
            month_str = str(month_period)
            
            for source in month_df['Source'].unique():
                source_df = month_df[month_df['Source'] == source].copy()
                source_df = source_df.drop('Month', axis=1)
                
                # Create realistic filename
                filename = f"{month_str}_{source.replace(' ', '_')}.csv"
                filepath = os.path.join(output_dir, filename)
                source_df.to_csv(filepath, index=False, encoding='utf-8-sig')
                files_created.append(filename)
        
        print(f"✅ Created {len(files_created)} CSV files")
        print(f"   Files: {output_dir}/")
        
        # Also create a single master file
        master_file = os.path.join(output_dir, 'full_year_2025.csv')
        df.drop('Month', axis=1).to_csv(master_file, index=False, encoding='utf-8-sig')
        print(f"   Master file: {master_file}")
        
        return files_created
    
    def create_demo_classifications(self, output_dir='data/demo'):
        """Create pre-classified data to showcase the memory system"""
        classifications = {}
        
        for category, subcategories in self.merchants.items():
            for sub_category, merchant_list in subcategories.items():
                for merchant_data in merchant_list:
                    merchant_name = merchant_data[0]
                    classifications[merchant_name] = {
                        'category': category,
                        'sub_category': sub_category
                    }
        
        # Save to JSON
        output_file = os.path.join(output_dir, 'demo_classifications.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(classifications, f, ensure_ascii=False, indent=2)
        
        print(f"\n📋 Created classification reference: {output_file}")
        print(f"   Contains {len(classifications)} merchant classifications")
        
        return classifications


def main():
    print("=" * 60)
    print("🎬 FAMILY FINANCIAL ANALYST - DEMO DATA GENERATOR")
    print("=" * 60)
    
    generator = DemoDataGenerator()
    
    # Generate 2025 data
    df = generator.generate_yearly_data(year=2025)
    
    # Export to files
    files = generator.export_to_csv(df)
    
    # Create classification reference
    generator.create_demo_classifications()
    
    print("\n" + "=" * 60)
    print("✨ DEMO DATA GENERATION COMPLETE!")
    print("=" * 60)
    print("\n📖 HOW TO USE:")
    print("1. Run the app: streamlit run app.py")
    print("2. Upload files from data/demo/ folder")
    print("3. Watch the AI classify and analyze automatically")
    print("4. See beautiful visualizations and insights")
    print("\n💡 Perfect for your LinkedIn demo video!")
    print("=" * 60)


if __name__ == "__main__":
    main()
