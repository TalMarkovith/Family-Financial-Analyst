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

    for index, row in df.iterrows():
        merchant = str(row['Description']).strip()
        
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
        
        # 1. Check Vector Memory First (semantic similarity search)
        memory_result = memory.find_similar_merchant(merchant, threshold=0.85)
        
        if memory_result:
            # Found a similar merchant in memory!
            cat = memory_result['category']
            sub_cat = memory_result['sub_category']
            matched_name = memory_result['matched_name']
            print(f"   ✓ Memory hit! Matched with '{matched_name}'")
            memory_hits += 1
        
        # 2. If not in memory, ask the LLM with Maps context
        else:
            print(f"   → New merchant. Fetching Maps context...")
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
                memory.save_merchant_to_memory(merchant, cat, sub_cat)
                print(f"   ✓ Classified and saved to memory!")
                llm_calls += 1
                
            except Exception as e:
                print(f"   ✗ Error classifying: {e}")
                cat, sub_cat = "Error", "Error"

        categories.append(cat)
        sub_categories.append(sub_cat)

    # Add the new columns to the DataFrame
    df['Category'] = categories
    df['Sub_Category'] = sub_categories
    
    print(f"\n📊 Classification Complete!")
    print(f"   - Total transactions: {total_transactions}")
    print(f"   - Memory hits: {memory_hits} ({memory_hits/total_transactions*100:.1f}%)")
    print(f"   - New LLM calls: {llm_calls}")
    
    return df

# Example Usage:
# df = parse_isracard("data/raw/3172_12_2025.csv")
# classified_df = classify_dataframe(df)
# classified_df.to_csv("data/processed/classified_ledger.csv", index=False)