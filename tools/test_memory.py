#!/usr/bin/env python3
"""Test script to investigate memory manager connection issues."""

from tools.memory_manager import MemoryManager

if __name__ == "__main__":
    try:
        print("Initializing MemoryManager...")
        memory = MemoryManager()
        print("✅ MemoryManager initialized successfully")
        
        print("\nTesting embedding generation...")
        test_text = "סופר פארם"
        embedding = memory.get_embedding(test_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
        print("\nTesting vector search...")
        result = memory.find_similar_merchant("סופר פארם")
        if result:
            print(f"✅ Found match: {result}")
        else:
            print("ℹ️ No match found (this is OK if index is empty)")
        
        print("\nTesting save to memory...")
        memory.save_merchant_to_memory(
            merchant_name="טסט מרצ'נט",
            category="Variable_Daily",
            sub_category="Groceries"
        )
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
