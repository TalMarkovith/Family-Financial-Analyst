import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
)

# Load environment variables from your .env file
load_dotenv()

def create_merchant_index():
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_API_KEY")  # Changed from AZURE_SEARCH_KEY
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "merchant-memory-index")

    # Validate required environment variables
    if not endpoint:
        raise ValueError("AZURE_SEARCH_ENDPOINT is not set in .env file")
    if not key:
        raise ValueError("AZURE_SEARCH_API_KEY is not set in .env file")
    
    print(f"Endpoint: {endpoint}")
    print(f"Index name: {index_name}")

    # Initialize the Index Client
    client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    print(f"Checking index: {index_name}")

    # 1. Delete existing index if it exists (for clean deployment)
    try:
        client.delete_index(index_name)
        print(f"🗑️ Deleted existing index '{index_name}' to apply new schema.")
    except Exception:
        print(f"ℹ️ Index '{index_name}' did not exist yet. Proceeding...")

    # 2. Vector Search Configuration (HNSW for fast semantic matching)
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="my-hnsw-config")
        ],
        profiles=[
            VectorSearchProfile(
                name="my-vector-profile",
                algorithm_configuration_name="my-hnsw-config"
            )
        ]
    )

    # 3. Define the Schema Fields for Financial Memory
    fields = [
        # Unique Identifier
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        
        # The raw Hebrew merchant name from the credit card
        SearchableField(name="merchant_name", type=SearchFieldDataType.String, analyzer_name="he.microsoft"), 
        
        # The AI-determined categories (Filterable for future queries)
        SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="sub_category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        
        # The Mathematical Vector of the merchant name
        SearchField(
            name="merchant_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536, # Matches text-embedding-ada
            vector_search_profile_name="my-vector-profile"
        )
    ]

    # 4. Semantic Search Configuration
    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="merchant_name"),
            content_fields=[
                SemanticField(field_name="category"), 
                SemanticField(field_name="sub_category")
            ]
        )
    )
    semantic_search = SemanticSearch(configurations=[semantic_config])

    # 5. Build and Deploy the Index
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )

    try:
        client.create_or_update_index(index)
        print(f"✅ Index '{index_name}' created successfully in Azure!")
    except Exception as e:
        print(f"❌ Error creating index: {e}")

if __name__ == "__main__":
    try:
        create_merchant_index()
    except Exception as e:
        print(f"❌ Fatal error: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()