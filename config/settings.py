import os
import logging
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
ALLOWED_IDS_STR = os.getenv("ALLOWED_TELEGRAM_IDS", "")

# Setup logging
def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        level=logging.INFO
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger(__name__)

# Proses ID pengguna yang diizinkan
def get_allowed_user_ids():
    ALLOWED_USER_IDS = []
    if ALLOWED_IDS_STR:
        try:
            ALLOWED_USER_IDS = [int(user_id.strip()) for user_id in ALLOWED_IDS_STR.split(',')]
        except ValueError:
            logging.error("⚠️ Error: Format ALLOWED_TELEGRAM_IDS tidak valid.")
    return ALLOWED_USER_IDS