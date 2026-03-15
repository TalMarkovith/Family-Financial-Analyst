import os
import uuid
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

load_dotenv()

class MemoryManager:
    def __init__(self):
        # 1. Initialize OpenAI for Embeddings
        self.embedding_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        # We are using your specific deployment name here!
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

        # 2. Initialize Azure AI Search Client
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        search_key = os.getenv("AZURE_SEARCH_API_KEY")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(search_key)
        )

    def get_embedding(self, text: str) -> list:
        """Converts merchant name into a vector."""
        response = self.embedding_client.embeddings.create(
            input=text,
            model=self.embedding_deployment
        )
        return response.data[0].embedding

    def find_similar_merchant(self, merchant_name: str, threshold: float = 0.85):
        """Searches the vector database for a semantic match."""
        vector = self.get_embedding(merchant_name)
        
        try:
            # Perform Vector Search
            results = self.search_client.search(
                search_text=None,
                vector_queries=[{
                    "vector": vector,
                    "k": 1, # Get the closest match
                    "fields": "merchant_vector",
                    "kind": "vector"
                }]
            )
            
            for result in results:
                score = result['@search.score']
                matched = result.get('merchant_name', '?')
                # Always log the top match and its score for debugging
                print(f"      Memory top match: '{matched}' (score={score:.4f}, threshold={threshold})")
                
                # If the semantic similarity is higher than our threshold, it's a match!
                if score >= threshold:
                    return {
                        "category": result['category'],
                        "sub_category": result['sub_category'],
                        "matched_name": result['merchant_name']
                    }
            return None
            
        except Exception as e:
            print(f"Memory search failed (Index might not exist yet): {e}")
            return None

    def save_merchant_to_memory(self, merchant_name: str, category: str, sub_category: str):
        """Saves a new classification into the vector database."""
        vector = self.get_embedding(merchant_name)
        
        document = {
            "id": str(uuid.uuid4()), # Generate a unique ID
            "merchant_name": merchant_name,
            "category": category,
            "sub_category": sub_category,
            "merchant_vector": vector
        }
        
        try:
            self.search_client.upload_documents(documents=[document])
            print(f"[{merchant_name}] saved to Long-Term Memory.")
        except Exception as e:
            print(f"Failed to save to memory: {e}")