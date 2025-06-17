import google.generativeai as genai
import json
import logging
from config.settings import GEMINI_API_KEY
from datetime import datetime

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
        
        return f"""
        Anda adalah asisten cerdas untuk bot pencatat keuangan bernama Reefficiency.
        Tugas Anda adalah menganalisis teks dari pengguna dan mengubahnya menjadi format JSON yang terstruktur.
        Tanggal hari ini adalah: {today_date}. Bulan sekarang: {current_month}. Tahun sekarang: {current_year}.
        
        Ada dua jenis niat (intent) yang mungkin: 'catat' (untuk mencatat transaksi) dan 'laporan' (untuk meminta laporan).

        Untuk intent 'catat', ekstrak entitas berikut:
        - "transaction_type": harus 'pemasukan' atau 'pengeluaran'.
        - "category": kategori transaksi (misal: 'makan siang', 'gaji', 'transportasi').
        - "amount": jumlah dalam bentuk angka integer. Abaikan 'ribu', 'juta', 'k', dll dan konversikan ke angka penuh.
        - "description": (opsional) deskripsi tambahan.
        - "date": (opsional) tanggal dalam format YYYY-MM-DD. Jika tidak ada, gunakan null.

        Untuk intent 'laporan', ekstrak entitas berikut:
        - "period": 'bulanan' atau 'tahunan'.
        - "year": (opsional) tahun laporan dalam format YYYY. Jika tidak disebutkan, gunakan tahun sekarang.
        - "month": (opsional) bulan laporan dalam bentuk angka (1-12). Hanya untuk laporan bulanan. Jika tidak disebutkan, gunakan bulan sekarang.

        Contoh untuk CATAT:
        Input: "catat pengeluaran bensin 150 ribu kemarin"
        Output: {{"intent": "catat", "entities": {{"transaction_type": "pengeluaran", "category": "bensin", "amount": 150000, "description": null, "date": "2025-06-16"}}}}

        Input: "saya baru saja membeli hp baru seharga 15.000.000 dan laptop seharga 20.000.000"
        Output: {{"intent": "catat", "entities": {{"transaction_type": "pengeluaran", "category": "elektronik", "amount": 35000000, "description": "hp baru dan laptop", "date": null}}}}

        Contoh untuk LAPORAN:
        Input: "laporan bulan ini"
        Output: {{"intent": "laporan", "entities": {{"period": "bulanan", "year": {current_year}, "month": {current_month}}}}}

        Input: "laporan tahun 2024"
        Output: {{"intent": "laporan", "entities": {{"period": "tahunan", "year": 2024, "month": null}}}}

        Input: "laporan januari 2025"
        Output: {{"intent": "laporan", "entities": {{"period": "bulanan", "year": 2025, "month": 1}}}}

        Input: "laporan bulanan februari"
        Output: {{"intent": "laporan", "entities": {{"period": "bulanan", "year": {current_year}, "month": 2}}}}

        Input: "laporan tahunan"
        Output: {{"intent": "laporan", "entities": {{"period": "tahunan", "year": {current_year}, "month": null}}}}

        Input: "minta laporan keuangan bulan lalu"
        Output: {{"intent": "laporan", "entities": {{"period": "bulanan", "year": {current_year}, "month": {current_month - 1 if current_month > 1 else 12}}}}}

        Jika Anda tidak dapat memahami permintaan pengguna, kembalikan JSON dengan intent 'tidak_paham'.
        Output harus HANYA berupa JSON yang valid tanpa teks tambahan.
        """

    async def process_text(self, text: str) -> dict:
        prompt = self.get_prompt()
        full_prompt = f"{prompt}\n\nInput Pengguna: \"{text}\"\nOutput JSON:"

        try:
            logger.info(f"Sending to Gemini: {text}")
            response = self.model.generate_content(full_prompt)
            logger.info(f"Raw Gemini response: {response.text}")
            
            # Membersihkan output agar hanya JSON yang tersisa
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