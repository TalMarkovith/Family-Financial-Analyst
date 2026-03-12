import sys
import os

# Ensure Python can find your tools folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.memory_manager import MemoryManager

def bootstrap_core_merchants():
    print("🚀 Initializing Memory Bootstrap...")
    memory = MemoryManager()
    
    # First, check what's already in the database
    print("📊 Checking existing merchants in vector database...")
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential
    from dotenv import load_dotenv
    
    load_dotenv()
    
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
    
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(search_key)
    )
    
    # Get existing merchant names
    existing_merchants = set()
    try:
        results = search_client.search(
            search_text="*",
            select=["merchant_name"],
            top=1000
        )
        for result in results:
            existing_merchants.add(result['merchant_name'])
        print(f"ℹ️  Found {len(existing_merchants)} existing merchants in database")
    except Exception as e:
        print(f"⚠️  Could not fetch existing merchants: {e}")
    
    # Here we define your family's "Core Constants" based on your taxonomy
    # Format: ("Exact Merchant Name from Credit Card", "Category", "Sub_Category")
    core_merchants = [
        # 1. Housing & Fixed
        ('הו"ק לאורן ויפאת שפי', 'Housing_Fixed', 'Rent_Mortgage'),
        ('דסק-משכנתא חיוב', 'Housing_Fixed', 'Rent_Mortgage'),
        ('מי גבעתיים- מפעלי מי', 'Housing_Fixed', 'Utilities_Arnona_Elec_Water_Gas'),
        ('ח-ן שרות סלקום', 'Housing_Fixed', 'Communication'),
        ('שטראוס מים בע"מ', 'Housing_Fixed', 'Utilities_Arnona_Elec_Water_Gas'), # Tami 4
        (' סלקום אנר', 'Housing_Fixed', 'Utilities_Arnona_Elec_Water_Gas'),
        
        # 2. Income & Investments
        ('בנק פועלים משכורת', 'Income', 'Income'),
        ('הע. לאנליסט בית הש', 'Investments', 'Savings_Analyst_Brokerage'),
        ('הע. לאנליסט קרן הש', 'Investments', 'Savings_Analyst_Brokerage'),
        
        # 3. Kids & Health
        ('סופר פארם', 'Pharm', 'Pharm'),
        ('בי דראגסטורס', 'Pharm', '_Pharm'),
        ('הראל-ביטוח בריאות', 'Insurance', 'Medical_Private_Insurance'),
        ('קרן מכבי', 'Health', 'Medical_Insurance'),
        ('upapp', 'Health', 'sport_club_gym'),
        ('כלל ביטוח חיים הו"ק', 'Insurance', 'Life_Insurance'),
        ('מגדל חיים/בריאות', 'Insurance', 'Life_Insurance'),
        ('איילון ביטוח חיים וב', 'Insurance', 'Life_Insurance'),
        
        # 4. Known Variable Daily
        ('רולדין', 'Food', 'Coffee_Restaurants'),
        ('YANGO TAXI', 'Transportation', 'Public_Transit_Taxi'),
        ('SPOTIFY', 'Leisure_Grooming', 'Subscriptions'),
        ('OPENAI *CHATGPT', 'Leisure_Grooming', 'Subscriptions'),
        ('wolt', 'Food_Delivery', 'Dining_Restaurants_Wolt'),
        ('פנגו', 'Transportation', 'Parking_Tolls'),
        ('קיי אס פי', 'Home', 'Direct_Online_Shopping'),
        ('aliexpress', 'Home', 'Direct_Online_Shopping'),
        ('אורט-דן גורמה', 'Leisure', 'Tal_Specials'),
        ('אנימל דופ', 'Rio', 'Rio_Food'),
        ('שופרסל', 'Food', 'Groceries_Supermarket'),
        ('רמי לוי אינטרנט', 'Food', 'Groceries_Supermarket'),
    ]

    print(f"Adding {len(core_merchants)} core merchants to Azure AI Search...")
    
    success_count = 0
    skipped_count = 0
    failed_merchants = []
    
    for idx, (merchant, cat, sub_cat) in enumerate(core_merchants, 1):
        try:
            # Skip if already exists
            if merchant in existing_merchants:
                print(f"[{idx}/{len(core_merchants)}] ⏭️  Skipping (exists): {merchant[:30]}...")
                skipped_count += 1
                continue
                
            print(f"[{idx}/{len(core_merchants)}] Processing: {merchant[:30]}...")
            # The save_merchant_to_memory function creates the vector and uploads it
            memory.save_merchant_to_memory(merchant, cat, sub_cat)
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to add '{merchant}': {e}")
            failed_merchants.append((merchant, str(e)))
            
    print(f"\n✅ Bootstrap Complete!")
    print(f"   - Added: {success_count} new merchants")
    print(f"   - Skipped: {skipped_count} (already exist)")
    print(f"   - Failed: {len(failed_merchants)}")
    print(f"   - Total in DB: {len(existing_merchants) + success_count}")
    
    if failed_merchants:
        print(f"\n⚠️  Failed merchants:")
        for merchant, error in failed_merchants:
            print(f"  - {merchant}: {error}")

if __name__ == "__main__":
    bootstrap_core_merchants()