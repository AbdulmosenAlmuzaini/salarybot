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

    def parse_transaction(self, message: str, user_language: str = 'en'):
        today = datetime.now().strftime('%Y-%m-%d')
        prompt = f"""
        Analyze the following personal accounting message in {'Arabic' if user_language == 'ar' else 'English'}:
        "{message}"

        Return ONLY a JSON object with these keys:
        - "type": either "income" or "expense"
        - "category": the category of transaction (in English, e.g., "food", "bills", "salary", "transport", "other")
        - "amount": the numeric amount only
        - "description": exactly what the user wrote but summarized (normalized to English for storage if possible, otherwise keep context)
        - "date": the date of transaction in YYYY-MM-DD format. If no date is mentioned, use today's date: "{today}"

        Example Output for "Spent 50 on coffee":
        {{
            "type": "expense",
            "category": "food",
            "amount": 50,
            "description": "Coffee",
            "date": "{today}"
        }}

        Example Output for "سددت فاتورة كهرباء 320 ريال":
        {{
            "type": "expense",
            "category": "bills",
            "amount": 320,
            "description": "Electricity bill",
            "date": "{today}"
        }}

        Strict rules:
        1. Return ONLY valid JSON.
        2. No explanations or extra text.
        3. Ensure the keys are exactly as requested.
        """

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a specialized accounting data extractor. You convert natural language entries into structured JSON. You support Arabic and English."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            print(f"DEBUG - Raw AI Response: {response_content}")
            
            # Remove markdown code blocks if present
            clean_content = response_content.strip()
            if clean_content.startswith("```"):
                clean_content = clean_content.split("\n", 1)[1]
            if clean_content.endswith("```"):
                clean_content = clean_content.rsplit("\n", 1)[0]
            clean_content = clean_content.strip()

            data = json.loads(clean_content)
            
            # Simple validation to ensure keys exist
            required_keys = ["type", "category", "amount", "description", "date"]
            if all(key in data for key in required_keys):
                return data
            else:
                print(f"DEBUG - Missing keys in AI response: {data}")
                return None
                
        except Exception as e:
            print(f"DEBUG - Error calling Groq API or parsing: {e}")
            import traceback
            traceback.print_exc()
            return None
