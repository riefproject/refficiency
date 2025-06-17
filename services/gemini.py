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
        return f"""
        Anda adalah asisten cerdas untuk bot pencatat keuangan bernama Reefficiency.
        Tugas Anda adalah menganalisis teks dari pengguna dan mengubahnya menjadi format JSON yang terstruktur.
        Tanggal hari ini adalah: {today_date}. Jika pengguna menyebut "hari ini", gunakan tanggal ini.
        
        Ada dua jenis niat (intent) yang mungkin: 'catat' (untuk mencatat transaksi) dan 'laporan' (untuk meminta laporan).

        Untuk intent 'catat', ekstrak entitas berikut:
        - "transaction_type": harus 'pemasukan' atau 'pengeluaran'.
        - "category": kategori transaksi (misal: 'makan siang', 'gaji', 'transportasi').
        - "amount": jumlah dalam bentuk angka integer. Abaikan 'ribu', 'juta', 'k', dll dan konversikan ke angka penuh.
        - "description": (opsional) deskripsi tambahan.
        - "date": (opsional) tanggal dalam format YYYY-MM-DD. Jika tidak ada, gunakan null.

        Untuk intent 'laporan', ekstrak entitas berikut:
        - "period": bisa 'bulanan' atau 'tahunan'.
        - "year": (opsional) tahun laporan dalam format YYYY.
        - "month": (opsional) bulan laporan dalam bentuk angka (1-12).

        Contoh:
        Input Pengguna: "Tolong catat pengeluaran untuk bensin 150 ribu kemarin"
        Output JSON: {{"intent": "catat", "entities": {{"transaction_type": "pengeluaran", "category": "bensin", "amount": 150000, "description": null, "date": "2025-06-16"}}}}

        Input Pengguna: "catat pemasukan 20000 gaji"
        Output JSON: {{"intent": "catat", "entities": {{"transaction_type": "pemasukan", "category": "gaji", "amount": 20000, "description": null, "date": null}}}}

        Input Pengguna: "pemasukan dari freelance 1.2jt"
        Output JSON: {{"intent": "catat", "entities": {{"transaction_type": "pemasukan", "category": "freelance", "amount": 1200000, "description": null, "date": null}}}}
        
        Input Pengguna: "saya baru saja membeli hp baru seharga 15.000.000 dan laptop seharga 20.000.000"
        Output JSON: {{"intent": "catat", "entities": {{"transaction_type": "pengeluaran", "category": "elektronik", "amount": 35000000, "description": "hp baru dan laptop", "date": null}}}}

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