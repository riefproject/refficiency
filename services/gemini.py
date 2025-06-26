# -*- coding: utf-8 -*-
"""Provides a service layer for interacting with the Google Gemini API.

This module uses the legacy 'google-genai' library to interpret natural
language queries from a financial tracking bot and convert them into
structured JSON data. It handles prompt construction, API communication,
and response parsing.
"""

from google import genai
import json
import logging
from config.settings import GEMINI_API_KEY
from datetime import datetime
from models.category import TransactionCategory

# Setup a logger for this module
logger = logging.getLogger(__name__)

# Initialize the Gemini client at the module level for reuse.
# This client is configured with the API key from settings.
client = genai.Client(api_key=GEMINI_API_KEY)


class GeminiService:
    """Encapsulates all logic for communication with the Gemini API.

    This service class manages the API client, constructs detailed prompts
    for financial transaction parsing, processes user input, and parses
    the structured JSON output from the language model.
    """

    def __init__(self):
        """Initializes the GeminiService instance."""
        self.client = client
        self.model_name = "gemini-1.5-flash-latest"

    def get_prompt(self) -> str:
        """Dynamically generates the system prompt for the Gemini API.

        The prompt is constructed with real-time data, including the current
        date and a list of available transaction categories. It provides
        strict rules and examples to guide the language model in performing
        its JSON conversion task accurately.

        Returns:
            str: A formatted string containing the complete system prompt.
        """
        today_date = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Fetch available categories from the Enum to include in the prompt
        categories = [cat.value for cat in TransactionCategory]
        categories_str = ", ".join(categories)

        return f"""
        You are an intelligent assistant for Reefficiency financial tracking bot.
        Your task is to analyze user text and convert it into structured JSON format.
        Today's date: {today_date}. Current month: {current_month}. Current year: {current_year}.

        Available standard categories: {categories_str}

        IMPORTANT RULES:
        1. If user mentions multiple items, create SEPARATE transactions for each item.
        2. Use ONLY the standard categories provided above.
        3. Map Indonesian keywords to appropriate English categories.
        4. For multiple transactions, return an array of transaction objects.

        There are two types of intent: 'catat' (record transaction) and 'laporan' (request report).

        For 'catat' intent, extract these entities:
        - "transaction_type": must be 'income' or 'expense' (English only).
        - "category": use only from the standard categories list above.
        - "amount": amount as integer. Convert 'ribu', 'juta', 'k' to full numbers.
        - "description": (optional) additional description.
        - "date": (optional) date in YYYY-MM-DD format. If not specified, use null.
        - "transactions": array of transaction objects if multiple items are detected.

        For 'laporan' intent, extract these entities:
        - "period": 'monthly' or 'yearly' (English only).
        - "year": (optional) report year in YYYY format.
        - "month": (optional) report month as number (1-12).

        Examples for SINGLE transaction:
        Input: "catat pengeluaran bensin 150 ribu"
        Output: {{"intent": "catat", "entities": {{"transaction_type": "expense", "category": "transportation", "amount": 150000, "description": "bensin", "date": null}}}}

        Examples for MULTIPLE transactions:
        Input: "saya beli baju 100 ribu dan celana 50 ribu"
        Output: {{"intent": "catat", "entities": {{"transactions": [{{"transaction_type": "expense", "category": "shopping_clothing", "amount": 100000, "description": "baju", "date": null}}, {{"transaction_type": "expense", "category": "shopping_clothing", "amount": 50000, "description": "celana", "date": null}}]}}}}

        Report examples:
        Input: "laporan bulan ini"
        Output: {{"intent": "laporan", "entities": {{"period": "monthly", "year": {current_year}, "month": {current_month}}}}}

        If you cannot understand the request, return JSON with intent 'unclear'.
        Output should be ONLY valid JSON without any additional text or markdown formatting.
        """

    async def process_text(self, text: str) -> dict:
        """Processes raw user text and returns structured data from Gemini.

        This method takes a user's natural language string, combines it with
        the system prompt, sends the request to the Gemini API, and then
        parses and cleans the response. It handles errors gracefully by
        returning a dictionary with an 'error' intent.

        Args:
            text (str): The raw user input string to be analyzed.

        Returns:
            dict: A dictionary representing the structured output from the API.
                  The structure depends on the detected intent ('catat',
                  'laporan', 'unclear', or 'error').
        """
        system_prompt = self.get_prompt()
        full_prompt = f"{system_prompt}\n\nUser Input: \"{text}\"\nJSON Output:"

        try:
            logger.info(f"Sending request to Gemini for text: '{text}'")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            raw_response_text = response.text
            logger.info(f"Raw Gemini response: {raw_response_text}")

            # Clean the output to ensure it's valid JSON
            cleaned_response = raw_response_text.strip().replace('```json', '').replace('```', '').strip()
            logger.info(f"Cleaned response: {cleaned_response}")

            parsed_response = json.loads(cleaned_response)
            logger.info(f"Successfully parsed JSON: {parsed_response}")

            return parsed_response
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}. Raw response: {raw_response_text if 'raw_response_text' in locals() else 'No response'}")
            return {"intent": "error", "details": f"JSON parsing error: {str(e)}"}
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing with Gemini: {e}")
            return {"intent": "error", "details": str(e)}
