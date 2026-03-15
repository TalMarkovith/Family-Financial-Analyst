"""
Clean script: Delete ALL auto-saved (non-bootstrap) entries from Azure AI Search.
Keep only the 29 original bootstrap entries.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_key)
)

# The 29 original bootstrap merchant names (EXACT)
BOOTSTRAP_MERCHANTS = {
    'הו"ק לאורן ויפאת שפי',
    'דסק-משכנתא חיוב',
    'מי גבעתיים- מפעלי מי',
    'ח-ן שרות סלקום',
    'שטראוס מים בע"מ',
    ' סלקום אנר',
    'בנק פועלים משכורת',
    'הע. לאנליסט בית הש',
    'הע. לאנליסט קרן הש',
    'סופר פארם',
    'בי דראגסטורס',
    'הראל-ביטוח בריאות',
    'קרן מכבי',
    'upapp',
    'כלל ביטוח חיים הו"ק',
    'מגדל חיים/בריאות',
    'איילון ביטוח חיים וב',
    'רולדין',
    'YANGO TAXI',
    'SPOTIFY',
    'OPENAI *CHATGPT',
    'wolt',
    'פנגו',
    'קיי אס פי',
    'aliexpress',
    'אורט-דן גורמה',
    'אנימל דופ',
    'שופרסל',
    'רמי לוי אינטרנט',
}

# Fetch ALL documents
results = search_client.search(
    search_text="*",
    select=["id", "merchant_name", "category", "sub_category"],
    top=1000
)

to_delete = []
to_keep = []

for result in results:
    merchant = result.get('merchant_name', '')
    doc_id = result['id']
    
    if merchant in BOOTSTRAP_MERCHANTS:
        to_keep.append(merchant)
    else:
        to_delete.append({
            'id': doc_id,
            'merchant_name': merchant,
            'category': result.get('category', '?'),
            'sub_category': result.get('sub_category', '?')
        })

print(f"📊 Keeping {len(to_keep)} bootstrap entries")
print(f"🗑️  Deleting {len(to_delete)} auto-saved entries:\n")

for d in to_delete:
    print(f"  ❌ {d['merchant_name']:<45} [{d['category']}/{d['sub_category']}]")

# Perform the deletion
if to_delete:
    print(f"\n🗑️  Deleting {len(to_delete)} documents...")
    delete_docs = [{"id": d['id']} for d in to_delete]
    
    # Azure AI Search supports batch delete
    result = search_client.delete_documents(documents=delete_docs)
    
    success = sum(1 for r in result if r.succeeded)
    failed = sum(1 for r in result if not r.succeeded)
    
    print(f"✅ Deleted: {success}")
    if failed:
        print(f"❌ Failed: {failed}")
else:
    print("Nothing to delete!")

# Verify
print(f"\n📊 Verifying remaining entries...")
remaining = search_client.search(search_text="*", select=["merchant_name"], top=1000)
count = sum(1 for _ in remaining)
print(f"   Entries remaining in index: {count}")
