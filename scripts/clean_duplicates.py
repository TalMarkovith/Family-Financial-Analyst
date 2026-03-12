"""
Clean up duplicate merchants from Azure AI Search vector database
"""
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.memory_manager import MemoryManager
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

def clean_duplicates():
    print("🧹 Starting duplicate cleanup...")
    
    # Connect directly to search client to list all documents
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
    
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(search_key)
    )
    
    print("📊 Fetching all documents from vector database...")
    
    # Fetch all documents
    results = search_client.search(
        search_text="*",
        select=["id", "merchant_name", "category", "sub_category"],
        top=1000
    )
    
    # Group by merchant_name to find duplicates
    merchants_map = defaultdict(list)
    total_count = 0
    
    for result in results:
        merchant_name = result['merchant_name']
        merchants_map[merchant_name].append({
            'id': result['id'],
            'category': result['category'],
            'sub_category': result['sub_category']
        })
        total_count += 1
    
    print(f"📈 Found {total_count} total documents")
    print(f"📈 Found {len(merchants_map)} unique merchants")
    
    # Find duplicates
    duplicates = {name: docs for name, docs in merchants_map.items() if len(docs) > 1}
    
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    print(f"\n⚠️  Found {len(duplicates)} merchants with duplicates:")
    
    to_delete = []
    for merchant_name, docs in duplicates.items():
        print(f"\n  '{merchant_name}': {len(docs)} copies")
        # Keep the first one, delete the rest
        for doc in docs[1:]:
            to_delete.append(doc['id'])
            print(f"    - Will delete ID: {doc['id']}")
    
    if to_delete:
        print(f"\n🗑️  Deleting {len(to_delete)} duplicate documents...")
        
        # Delete in batches
        batch_size = 100
        for i in range(0, len(to_delete), batch_size):
            batch = to_delete[i:i+batch_size]
            documents_to_delete = [{"id": doc_id} for doc_id in batch]
            try:
                search_client.delete_documents(documents=documents_to_delete)
                print(f"   Deleted batch {i//batch_size + 1} ({len(batch)} documents)")
            except Exception as e:
                print(f"   ❌ Error deleting batch: {e}")
        
        print(f"\n✅ Cleanup complete! Deleted {len(to_delete)} duplicates")
        print(f"📊 Remaining documents: {total_count - len(to_delete)}")
    else:
        print("\n✅ No duplicates to delete")

if __name__ == "__main__":
    clean_duplicates()
