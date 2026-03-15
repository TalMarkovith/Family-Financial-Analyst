import pandas as pd
import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

load_dotenv()

from tools.maps_lookup import get_merchant_context
from tools.memory_manager import MemoryManager
from agents.prompts import FINANCIAL_TAXONOMY_PROMPT

def classify_dataframe(df):
    """
    Takes the unified DataFrame and adds Category and Sub-Category columns.
    Uses Azure AI Search vector database for intelligent memory.
    """
    print("Starting AI Classification Process with Vector Memory...")
    
    # Initialize Memory Manager (Azure AI Search)
    memory = MemoryManager()
    
    # Initialize Azure OpenAI Client for LLM classification
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    categories = []
    sub_categories = []
    
    total_transactions = len(df)
    memory_hits = 0
    llm_calls = 0
    
    # Batch save: collect new LLM classifications to save AFTER the loop
    # This prevents cross-pollution (e.g. "בראד קלאב נורדאו" saved mid-run
    # then "שופרסל שלי נורדאו" matching it instead of "שופרסל")
    pending_saves = []
    
    # Layer 0.5: Known keyword constants — substring matches BEFORE vector search.
    # These are your bootstrap constants that may not score above threshold
    # due to appended branch/location info (e.g. "הו"ק לאורן...לסניף 14-350")
    KEYWORD_CONSTANTS = [
        # (keyword_substring,              category,        sub_category)
        ('הו"ק לאורן',                     'Housing_Fixed', 'Rent_Mortgage'),
        ('דסק-משכנתא',                     'Housing_Fixed', 'Rent_Mortgage'),
        ('אנליסט',                         'Investments',   'Savings_Analyst_Brokerage'),
        ('דור פארק',                       'Transportation', 'Car_Gas_Tolls'),
        ('דור אנרגיה',                     'Transportation', 'Car_Gas_Tolls'),
        ('סלקום אנר',                      'Housing_Fixed', 'Utilities_Arnona_Elec_Water_Gas'),
        ('שטראוס מים',                     'Housing_Fixed', 'Utilities_Arnona_Elec_Water_Gas'),
        ('מי גבעתיים',                     'Housing_Fixed', 'Utilities_Arnona_Elec_Water_Gas'),
        ('ביטוח לאומי',                    'Insurance_Health', 'Insurances'),
        ('מוסדות חינוך',                   'Kids_Family',   'Gan_Education'),
        ('ויצו',                           'Kids_Family',   'Gan_Education'),
    ]

    for index, row in df.iterrows():
        merchant = str(row['Description']).strip()
        
        # Guard: skip garbage merchant names (nan, empty, pandas Series strings)
        if not merchant or merchant.lower() == 'nan' or 'dtype:' in merchant or len(merchant) < 2:
            print(f"[{index+1}/{total_transactions}] ⏭️  Skipping garbage: '{merchant[:40]}'")
            categories.append('Unknown')
            sub_categories.append('Unknown')
            continue
        
        print(f"[{index+1}/{total_transactions}] Processing: {merchant[:40]}...")
        
        # 0. Quick check for salary keywords (Hebrew)
        merchant_lower = merchant.lower()
        salary_keywords = ['משכורת', 'משכ', 'שכר']
        is_salary = any(keyword in merchant_lower for keyword in salary_keywords)
        
        if is_salary:
            # Determine which salary based on keywords
            if 'תל' in merchant_lower or 'tal' in merchant_lower:
                cat, sub_cat = 'Income', 'Tal_Salary'
            elif 'רעות' in merchant_lower or 'reut' in merchant_lower:
                cat, sub_cat = 'Income', 'Reut_Salary'
            else:
                # Default to Other_Income if we can't determine whose salary
                cat, sub_cat = 'Income', 'Other_Income_Bit'
            
            print(f"   ✓ Salary detected! Auto-classified as {sub_cat}")
            categories.append(cat)
            sub_categories.append(sub_cat)
            memory_hits += 1
            continue
        
        # 0.5. Keyword constants — substring match for known recurring charges
        # Catches entries like "הו"ק לאורן ויפאת שפי לסניף 14-350" that have
        # appended branch info and score just below vector threshold (0.8892)
        keyword_matched = False
        for keyword, kw_cat, kw_sub in KEYWORD_CONSTANTS:
            if keyword in merchant:
                cat, sub_cat = kw_cat, kw_sub
                print(f"   ✓ Keyword match! '{keyword}' → {cat}/{sub_cat}")
                categories.append(cat)
                sub_categories.append(sub_cat)
                memory_hits += 1
                keyword_matched = True
                break
        if keyword_matched:
            continue
        
        # 1. Check Vector Memory First (semantic similarity search)
        # Threshold 0.89 = calibrated sweet spot (tested with real data):
        #   Good matches:  שופרסל שלי נורדאו ↔ שופרסל = 0.9044, הו"ק rent = 0.8892
        #   False positives: גל שיטרית ↔ שטראוס = 0.8719, דור פארק ↔ סופר פארם = 0.8796
        memory_result = memory.find_similar_merchant(merchant, threshold=0.89)
        
        if memory_result:
            # Found a similar merchant in memory!
            cat = memory_result['category']
            sub_cat = memory_result['sub_category']
            matched_name = memory_result['matched_name']
            print(f"   ✓ Memory hit! Matched with '{matched_name}' → {cat}/{sub_cat}")
            memory_hits += 1
        
        # 2. If not in memory, ask the LLM with Maps context
        else:
            print(f"   → No confident memory match. Fetching Maps context...")
            maps_context = get_merchant_context(merchant)
            
            print(f"   → Asking LLM for classification...")
            
            # Format the prompt with merchant and maps data
            formatted_prompt = FINANCIAL_TAXONOMY_PROMPT.format(
                merchant_name=merchant,
                maps_data=maps_context
            )
            
            try:
                response = client.chat.completions.create(
                    model=deployment_name,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You output strict JSON."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    temperature=0.1
                )
                
                llm_result = json.loads(response.choices[0].message.content)
                cat = llm_result.get('category', 'Unknown')
                sub_cat = llm_result.get('sub_category', 'Unknown')
                
                # Save to vector memory for future semantic matching
                # Only save valid classifications (not Unknown/Error)
                # Deferred: save AFTER the loop to prevent cross-pollution
                if cat not in ('Unknown', 'Error') and sub_cat not in ('Unknown', 'Error'):
                    amount = row.get('Amount', 0)
                    pending_saves.append((merchant, cat, sub_cat, amount))
                    print(f"   ✓ LLM: {cat}/{sub_cat} → queued for memory save")
                else:
                    print(f"   ⚠️ LLM returned {cat}/{sub_cat} — NOT saving to memory")
                llm_calls += 1
                
            except Exception as e:
                print(f"   ✗ Error classifying: {e}")
                cat, sub_cat = "Error", "Error"

        categories.append(cat)
        sub_categories.append(sub_cat)

    # Add the new columns to the DataFrame
    df['Category'] = categories
    df['Sub_Category'] = sub_categories
    
    # DON'T auto-save to memory anymore — return pending_saves for human review
    # The app will show a review table and only save approved entries
    
    print(f"\n📊 Classification Complete!")
    print(f"   - Total transactions: {total_transactions}")
    print(f"   - Memory hits: {memory_hits} ({memory_hits/total_transactions*100:.1f}%)")
    print(f"   - New LLM calls: {llm_calls}")
    print(f"   - Pending human review: {len(pending_saves)} new merchants")
    
    return df, pending_saves


def save_approved_to_memory(approved_list):
    """
    Save user-approved classifications to vector memory.
    Called after the user reviews and confirms new merchant classifications.
    
    Args:
        approved_list: list of dicts with keys: merchant_name, category, sub_category
    """
    if not approved_list:
        return 0
    
    memory = MemoryManager()
    saved = 0
    for item in approved_list:
        try:
            memory.save_merchant_to_memory(
                item['merchant_name'],
                item['category'],
                item['sub_category']
            )
            print(f"   ✅ Saved: {item['merchant_name']} → {item['category']}/{item['sub_category']}")
            saved += 1
        except Exception as e:
            print(f"   ⚠️ Failed to save '{item['merchant_name']}': {e}")
    
    print(f"💾 Saved {saved}/{len(approved_list)} approved merchants to memory")
    return saved

# Example Usage:
# df = parse_isracard("data/raw/3172_12_2025.csv")
# classified_df = classify_dataframe(df)
# classified_df.to_csv("data/processed/classified_ledger.csv", index=False)