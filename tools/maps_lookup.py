# tools/maps_lookup.py
import os
import googlemaps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_merchant_context(merchant_name: str) -> str:
    """
    Queries the Google Places API to find the business type of an Israeli merchant.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "['Error: No Google Maps API Key found']"
        
    gmaps = googlemaps.Client(key=api_key)
    
    try:
        # We append 'ישראל' (Israel) to force the API to look locally, 
        # which is crucial for abbreviated credit card descriptions.
        query = f"{merchant_name} ישראל"
        places_result = gmaps.places(query=query)
        
        # Check if we got a valid response and at least one result
        if places_result.get('status') == 'OK' and len(places_result.get('results', [])) > 0:
            # Extract the 'types' array from the top result (e.g., ['pet_store', 'store'])
            types = places_result['results'][0].get('types', [])
            return str(types)
            
        return "['unknown_business']"
        
    except Exception as e:
        print(f"Maps API Error for {merchant_name}: {e}")
        return "['api_error']"

# Quick local test just for the tool
if __name__ == "__main__":
    print("Testing Maps Lookup...")
    print(f"פנדה הום בע\"מ: {get_merchant_context('פנדה הום בע\"מ')}")
    print(f"שירותי בר בארועים: {get_merchant_context('שירותי בר בארועים')}")