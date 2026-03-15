"""
Test script: Check actual similarity scores between
credit card transaction names and the bootstrap merchants in Azure AI Search.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.memory_manager import MemoryManager

def test_scores():
    memory = MemoryManager()
    
    # Test cases: real transaction names we've seen
    test_merchants = [
        # Should match שופרסל → Food
        "שופרסל שלי נורדאו",
        "שופרסל שלי גבעתיים",
        "שופרסל דיל אקסטרא",
        
        # Should match סופר פארם → Pharm
        "סופרפארם קניון גבעתיים",
        "סופר פארם בית הורד גבעתיי",
        "סופר-פארם נורדאו",
        
        # Should match הו"ק לאורן ויפאת שפי → Housing_Fixed
        'הו"ק לאורן ויפאת שפי לסניף 14-350',
        
        # Should NOT match anything well (new merchants)
        "גל שיטרית פיצוציית גנים",
        "בראד קלאב נורדאו",
        "מאפה הכיכר",
        "מקס 20 אבן גבירול",
        "מור פירות וירקות",
        "גנה בר יהודה",
        "לובליאנה בע\"מ",
        "דור פארק המדע",
        "ביטוח לאומי - ילדים",
        "מוסדות חינוך - עיריית תל",
    ]
    
    print("=" * 90)
    print(f"{'Transaction':<45} {'Top Match':<30} {'Score':>8}")
    print("=" * 90)
    
    for merchant in test_merchants:
        vector = memory.get_embedding(merchant)
        try:
            results = memory.search_client.search(
                search_text=None,
                vector_queries=[{
                    "vector": vector,
                    "k": 3,  # Get top 3 matches
                    "fields": "merchant_vector",
                    "kind": "vector"
                }]
            )
            
            matches = []
            for result in results:
                score = result['@search.score']
                matched = result.get('merchant_name', '?')
                cat = result.get('category', '?')
                matches.append((matched, cat, score))
            
            if matches:
                top = matches[0]
                print(f"{merchant:<45} {top[0]:<25} [{top[1]:<15}] {top[2]:.4f}")
                # Show 2nd match if exists
                if len(matches) > 1:
                    m2 = matches[1]
                    print(f"{'  (2nd)':<45} {m2[0]:<25} [{m2[1]:<15}] {m2[2]:.4f}")
            else:
                print(f"{merchant:<45} {'NO RESULTS':<30} {'N/A':>8}")
                
        except Exception as e:
            print(f"{merchant:<45} ERROR: {e}")
    
    print("=" * 90)
    print("\nThreshold guide:")
    print("  0.85 = Old threshold (too loose, many false positives)")
    print("  0.88 = Moderate (may still get some false positives)")
    print("  0.90 = Strict (good matches only)")
    print("  0.92 = Very strict (current setting)")
    print("  0.95 = Ultra strict (only near-exact)")

if __name__ == "__main__":
    test_scores()
