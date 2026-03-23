"""
Bootstrap the vector memory database with demo merchant classifications.
This ensures the AI will recognize the demo merchants instantly.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.memory_manager import MemoryManager

# Fix SSL certificates
from utils.ssl_fix import setup_ssl_certificates
setup_ssl_certificates()

load_dotenv()


def bootstrap_demo_memory():
    """Load demo classifications into the vector database"""
    
    print("=" * 60)
    print("🧠 BOOTSTRAPPING DEMO MEMORY")
    print("=" * 60)
    
    # Load demo classifications
    demo_file = "data/demo/demo_classifications.json"
    
    if not os.path.exists(demo_file):
        print(f"❌ Error: {demo_file} not found!")
        print("   Run: python scripts/generate_demo_data.py first")
        return
    
    with open(demo_file, 'r', encoding='utf-8') as f:
        classifications = json.load(f)
    
    print(f"\n📋 Loaded {len(classifications)} merchant classifications")
    
    # Initialize memory manager
    memory = MemoryManager()
    
    # Save each merchant to memory
    print("\n💾 Saving to vector database...")
    success_count = 0
    
    for merchant_name, data in classifications.items():
        try:
            memory.save_merchant_to_memory(
                merchant_name=merchant_name,
                category=data['category'],
                sub_category=data['sub_category']
            )
            success_count += 1
            print(f"  ✓ [{success_count}/{len(classifications)}] {merchant_name[:40]}...")
        except Exception as e:
            print(f"  ✗ Failed: {merchant_name} - {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ BOOTSTRAP COMPLETE!")
    print(f"   Successfully saved {success_count}/{len(classifications)} merchants")
    print("=" * 60)
    print("\n💡 The AI will now instantly recognize these demo merchants!")
    print("   No LLM calls needed - pure vector search magic 🚀")
    print("=" * 60)


if __name__ == "__main__":
    bootstrap_demo_memory()
