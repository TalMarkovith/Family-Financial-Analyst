import os
import googlemaps
from openai import AzureOpenAI

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

class ClassifierAgent:
    def __init__(self):
        # Initialize Google Maps Client
        self.gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
        
        # Initialize Azure AI Foundry Client
        self.llm_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2023-05-15"
        )
        
        # Layer 1: Fixed Constants
        self.known_expenses = {
            'הו"ק לאורן ויפאת שפי': ('Fixed', 'Housing', 'Rent'),
            'דסק-משכנתא': ('Fixed', 'Housing', 'Mortgage'),
            'בנק פועלים משכורת': ('Income', 'Salary', 'Tal/Reut')
        }

    def _get_maps_context(self, merchant_name):
        # Tool: Ask Google Maps what this place is
        try:
            places_result = self.gmaps.places(query=f"{merchant_name} ישראל")
            if places_result['status'] == 'OK':
                # Return the types of the first result (e.g., ['pet_store', 'store'])
                return places_result['results'][0].get('types', [])
        except Exception as e:
            print(f"Maps lookup failed for {merchant_name}")
        return None

    def _get_llm_classification(self, merchant_name, maps_context):
        # Tool: Use GPT-4o to categorize
        prompt = f"""
        You are a family financial analyst. Categorize the following Israeli transaction.
        Transaction Name: {merchant_name}
        Google Maps Data: {maps_context}
        
        Choose from these main categories: [Groceries, Dining, Baby/Gan, Transportation, Home, Pets, Shopping, Other]
        Return ONLY the category name.
        """
        
        response = self.llm_client.chat.completions.create(
            model="gpt-4o", # Your deployment name here
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

    def classify_transaction(self, merchant_name):
        # Step 1: Check knowns
        for key, category in self.known_expenses.items():
            if key in merchant_name:
                return category
                
        # Step 2: Get Maps Context
        maps_context = self._get_maps_context(merchant_name)
        
        # Step 3: Ask LLM
        return self._get_llm_classification(merchant_name, maps_context)

def process_and_classify(df):
    """
    Process and classify a DataFrame of transactions.
    This function is called by app.py for the Streamlit interface.
    
    Args:
        df: pandas DataFrame with transaction data
        
    Returns:
        tuple: (classified_df, pending_reviews)
            - classified_df: DataFrame with added Category and Sub_Category columns
            - pending_reviews: list of (merchant_name, category, sub_category) for human review
    """
    from tools.classify_dataframe import classify_dataframe
    return classify_dataframe(df)

# Usage Example:
# agent = ClassifierAgent()
# category = agent.classify_transaction('אנימל שופ')