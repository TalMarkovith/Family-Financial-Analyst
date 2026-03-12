import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

# Fix SSL certificates for corporate proxy (Netskope)
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

# Import the updated prompt from your prompts file
from agents.prompts import FINANCIAL_TAXONOMY_PROMPT
from tools.maps_lookup import get_merchant_context

# Load the environment variables from the .env file
load_dotenv()

# Initialize the Azure OpenAI Client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2025-01-01-preview" # Update this if your Azure Foundry uses a different API version
)

def test_classification(merchant_name, maps_context="None"):
    """
    Sends the merchant name and maps context to Azure OpenAI for categorization.
    """
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    # Inject the specific transaction and context into the prompt
    formatted_prompt = FINANCIAL_TAXONOMY_PROMPT.format(
        merchant_name=merchant_name, 
        maps_data=maps_context
    )
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            response_format={ "type": "json_object" }, # Forces pure JSON output
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output strict JSON."},
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.1 # Low temperature for consistent, analytical results
        )
        
        # Parse the string response into an actual Python dictionary to format it nicely
        result_str = response.choices[0].message.content
        return json.dumps(json.loads(result_str), indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"Error connecting to Azure OpenAI: {e}"

if __name__ == "__main__":
    print("--- Starting End-to-End Agent Intelligence Test ---\n")
    
    # Define the tricky merchants from your Isracard file
    merchants_to_test = [
        "פנדה הום בע\"מ",
        "שירותי בר בארועים",
        "אנימל שופ" # Added another one just to see how it handles English/Hebrew mix
    ]
    
    for merchant in merchants_to_test:
        print(f"Testing Merchant: {merchant}")
        
        # Step 1: The Agent uses the Maps Tool
        print("-> Fetching Google Maps Context...")
        real_maps_context = get_merchant_context(merchant)
        print(f"-> Maps Returned: {real_maps_context}")
        
        # Step 2: The Agent sends the data to Azure AI Foundry
        print("-> Analyzing with LLM...")
        result = test_classification(
            merchant_name=merchant, 
            maps_context=real_maps_context
        )
        print(f"-> Result:\n{result}\n")
        print("-" * 40 + "\n")
    
    # TEST 2: Bar Services
    # Simulating what Maps might say about the Bar service
    simulated_maps_context_bar = "['event_planner', 'bar', 'food']"
    
    print(f"Testing Merchant: שירותי בר בארועים")
    print(f"Maps Context: {simulated_maps_context_bar}")
    test_2 = test_classification(
        merchant_name="שירותי בר בארועים", 
        maps_context=simulated_maps_context_bar
    )
    print(f"Result:\n{test_2}\n")