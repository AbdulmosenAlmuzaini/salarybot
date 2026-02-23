import json
import logging
from groq import Groq
from src.config import Config
from datetime import datetime

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.DEFAULT_MODEL

    def _heuristic_parse(self, message: str, user_language: str):
        """Simple regex-based parsing for common direct patterns like 'بنزين 140'"""
        import re
        message = message.strip()
        
        # Pattern 1: [Category/Description] [Amount] [Optional Currency]
        # Example: "بنزين 140", "Lunch 45 ريال"
        match1 = re.search(r'^([^\d\s]+)\s+(\d+(?:\.\d+)?)(?:\s+.*)?$', message)
        
        # Pattern 2: [Amount] [Optional Currency] [Category/Description]
        # Example: "140 بنزين", "45 on lunch"
        match2 = re.search(r'^(\d+(?:\.\d+)?)(?:\s+[^\d\s]+)?\s+([^\d\s]+.*)$', message)
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Mapping common keywords to categories
        cat_map = {
            'بنزين': 'fuel', 'fuel': 'fuel', 'petrol': 'fuel', 'وقود': 'fuel',
            'اكل': 'food', 'food': 'food', 'lunch': 'food', 'dinner': 'food', 'قهوة': 'food', 'coffee': 'food',
            'سوبرماركت': 'shopping', 'شوبينج': 'shopping', 'shopping': 'shopping',
            'فاتورة': 'bills', 'bill': 'bills', 'كهرباء': 'bills', 'مويه': 'bills', 'نت': 'bills',
            'ايجار': 'rent', 'rent': 'rent',
            'علاج': 'health', 'مستشفى': 'health', 'صيدلية': 'health',
            'كريم': 'transport', 'اوبر': 'transport', 'taxi': 'transport'
        }

        found_data = None
        if match1:
            desc = match1.group(1)
            amount = match1.group(2)
            found_data = (desc, amount)
        elif match2:
            amount = match2.group(1)
            desc = match2.group(2)
            found_data = (desc, amount)

        if found_data:
            desc, amount = found_data
            # Detect category from description
            category = 'other'
            for kw, cat in cat_map.items():
                if kw in desc.lower():
                    category = cat
                    break
            
            return {
                "type": "expense", # Heuristic assumes expense by default for simple patterns
                "category": category,
                "amount": float(amount),
                "description": desc,
                "date": today
            }
        return None

    def parse_transaction(self, message: str, user_language: str = 'en'):
        # 1. Try Heuristic Parse First for speed and reliability in simple cases
        heuristic_result = self._heuristic_parse(message, user_language)
        if heuristic_result:
            print(f"DEBUG - Heuristic match found: {heuristic_result}")
            return heuristic_result

        # 2. Fallback to AI for complex sentences
        today = datetime.now().strftime('%Y-%m-%d')
        prompt = f"""
        Analyze the following personal accounting message in {'Arabic' if user_language == 'ar' else 'English'}:
        "{message}"

        Return ONLY a JSON object with these keys:
        - "type": "income" or "expense"
        - "category": (English only: food, bills, salary, transport, fuel, shopping, health, rent, other)
        - "amount": numeric value
        - "description": summarized description (in {'Arabic' if user_language == 'ar' else 'English'})
        - "date": YYYY-MM-DD (Default to: {today})

        Strict rules:
        - Output MUST be valid JSON.
        - No markdown code blocks.
        - No extra explanation.
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a specialized accounting data extractor. You convert natural language into structured JSON. You support Arabic and English. Be extremely concise."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            print(f"DEBUG - Raw AI Response: {response_content}")
            
            data = json.loads(response_content.strip())
            
            # Simple validation
            required_keys = ["type", "category", "amount", "description", "date"]
            if all(key in data for key in required_keys):
                return data
            else:
                print(f"DEBUG - Missing keys in AI response")
                return None
                
        except Exception as e:
            print(f"DEBUG - Error in AI parsing: {e}")
            return None
