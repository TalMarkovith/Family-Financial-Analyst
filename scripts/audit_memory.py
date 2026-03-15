"""
Audit script: List ALL entries in the Azure AI Search index
to see what's been saved (bootstrap + auto-saved from LLM runs).
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

# Get ALL documents
results = search_client.search(
    search_text="*",
    select=["id", "merchant_name", "category", "sub_category"],
    top=1000
)

docs = []
for result in results:
    docs.append({
        'id': result['id'],
        'merchant_name': result.get('merchant_name', '?'),
        'category': result.get('category', '?'),
        'sub_category': result.get('sub_category', '?')
    })

print(f"\n📊 Total entries in Azure AI Search index: {len(docs)}\n")

# Group by category
from collections import defaultdict
by_cat = defaultdict(list)
for d in docs:
    by_cat[d['category']].append(d)

for cat in sorted(by_cat.keys()):
    entries = by_cat[cat]
    print(f"\n{'='*70}")
    print(f"  {cat} ({len(entries)} entries)")
    print(f"{'='*70}")
    for d in sorted(entries, key=lambda x: x['merchant_name']):
        print(f"  [{d['sub_category']:<30}] {d['merchant_name']}")

# Now flag the original bootstrap entries
print(f"\n\n{'='*70}")
print(f"  BOOTSTRAP ENTRIES (from your original list)")
print(f"{'='*70}")
bootstrap_names = [
    'הו"ק לאורן ויפאת שפי', 'דסק-משכנתא חיוב', 'מי גבעתיים- מפעלי מי',
    'ח-ן שרות סלקום', 'שטראוס מים בע"מ', ' סלקום אנר',
    'בנק פועלים משכורת', 'הע. לאנליסט בית הש', 'הע. לאנליסט קרן הש',
    'סופר פארם', 'בי דראגסטורס', 'הראל-ביטוח בריאות',
    'קרן מכבי', 'upapp', 'כלל ביטוח חיים הו"ק',
    'מגדל חיים/בריאות', 'איילון ביטוח חיים וב',
    'רולדין', 'YANGO TAXI', 'SPOTIFY', 'OPENAI *CHATGPT',
    'wolt', 'פנגו', 'קיי אס פי', 'aliexpress',
    'אורט-דן גורמה', 'אנימל דופ', 'שופרסל', 'רמי לוי אינטרנט',
]

bootstrap_found = 0
for d in docs:
    if d['merchant_name'] in bootstrap_names:
        print(f"  ✅ {d['merchant_name']:<35} → {d['category']}/{d['sub_category']}")
        bootstrap_found += 1

print(f"\nFound {bootstrap_found}/{len(bootstrap_names)} bootstrap entries")
print(f"Auto-saved entries (from LLM runs): {len(docs) - bootstrap_found}")
