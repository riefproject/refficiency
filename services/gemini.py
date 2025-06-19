import google.generativeai as genai
import json
import logging
from config.settings import GEMINI_API_KEY
from datetime import datetime
from models.category import TransactionCategory

# Setup logger for this service
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

class GeminiService:
    def __init__(self):
        self.model = model

    def get_prompt(self):
        today_date = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get available categories for the prompt
        categories = [cat.value for cat in TransactionCategory]
        categories_str = ", ".join(categories)
        
        return f"""
        You are an intelligent assistant for Reefficiency financial tracking bot.
        Your task is to analyze user text and convert it into structured JSON format.
        Today's date: {today_date}. Current month: {current_month}. Current year: {current_year}.
        
        Available standard categories: {categories_str}
        
        IMPORTANT RULES:
        1. If user mentions multiple items, create SEPARATE transactions for each item
        2. Use ONLY the standard categories provided above
        3. Map Indonesian keywords to appropriate English categories
        4. For multiple transactions, return an array of transaction objects
        
        There are two types of intent: 'catat' (record transaction) and 'laporan' (request report).

        For 'catat' intent, extract these entities:
        - "transaction_type": must be 'income' or 'expense' (English only)
        - "category": use only from the standard categories list above
        - "amount": amount as integer. Convert 'ribu', 'juta', 'k' to full numbers
        - "description": (optional) additional description
        - "date": (optional) date in YYYY-MM-DD format. If not specified, use null
        - "transactions": array of transaction objects if multiple items detected

        For 'laporan' intent, extract these entities:
        - "period": 'monthly' or 'yearly' (English only)
        - "year": (optional) report year in YYYY format
        - "month": (optional) report month as number (1-12)

        Examples for SINGLE transaction:
        Input: "catat pengeluaran bensin 150 ribu"
        Output: {{"intent": "catat", "entities": {{"transaction_type": "expense", "category": "transportation", "amount": 150000, "description": "bensin", "date": null}}}}

        Examples for MULTIPLE transactions:
        Input: "saya beli baju 100 ribu dan celana 50 ribu"
        Output: {{"intent": "catat", "entities": {{"transactions": [{{"transaction_type": "expense", "category": "shopping_clothing", "amount": 100000, "description": "baju", "date": null}}, {{"transaction_type": "expense", "category": "shopping_clothing", "amount": 50000, "description": "celana", "date": null}}]}}}}

        Input: "beli laptop 15 juta dan mouse 500 ribu"
        Output: {{"intent": "catat", "entities": {{"transactions": [{{"transaction_type": "expense", "category": "electronics", "amount": 15000000, "description": "laptop", "date": null}}, {{"transaction_type": "expense", "category": "electronics", "amount": 500000, "description": "mouse", "date": null}}]}}}}

        Report examples:
        Input: "laporan bulan ini"
        Output: {{"intent": "laporan", "entities": {{"period": "monthly", "year": {current_year}, "month": {current_month}}}}}

        If you cannot understand the request, return JSON with intent 'unclear'.
        Output should be ONLY valid JSON without additional text.
        """

    async def process_text(self, text: str) -> dict:
        prompt = self.get_prompt()
        full_prompt = f"{prompt}\n\nUser Input: \"{text}\"\nJSON Output:"

        try:
            logger.info(f"Sending to Gemini: {text}")
            response = self.model.generate_content(full_prompt)
            logger.info(f"Raw Gemini response: {response.text}")
            
            # Clean output to keep only JSON
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            logger.info(f"Cleaned response: {cleaned_response}")
            
            parsed_response = json.loads(cleaned_response)
            logger.info(f"Parsed JSON: {parsed_response}")
            
            return parsed_response
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}. Raw response: {response.text if 'response' in locals() else 'No response'}")
            return {"intent": "error", "details": f"JSON parsing error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing with Gemini: {e}")
            return {"intent": "error", "details": str(e)}