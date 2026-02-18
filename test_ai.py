import sys
import os
# Add current directory to path so we can import src
sys.path.append(os.getcwd())

from src.ai_service import AIService
from src.config import Config

def test_ai():
    ai = AIService()
    test_messages = [
        "سحبت 50 ريال من الصرافة",
        "سددت فاتورة كهرباء 320 ريال"
    ]
    
    for msg in test_messages:
        print(f"\nTesting message: {msg}")
        result = ai.parse_transaction(msg, 'ar')
        print(f"Result: {result}")

if __name__ == "__main__":
    test_ai()
