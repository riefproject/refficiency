import gspread
import logging
from config.settings import GOOGLE_SHEETS_CREDENTIALS_PATH, GOOGLE_SHEET_NAME

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.gc = None
        self.sh = None
        
    def init_connection(self):
        if not GOOGLE_SHEETS_CREDENTIALS_PATH or not GOOGLE_SHEET_NAME:
            logger.error("❌ Google Sheets credentials or sheet name not set in environment variables")
            return False
            
        try:
            logger.info("🔄 Attempting to connect to Google Sheets...")
            self.gc = gspread.service_account(filename=GOOGLE_SHEETS_CREDENTIALS_PATH)
            self.sh = self.gc.open(GOOGLE_SHEET_NAME).sheet1
            logger.info(f"✅ Connected to Google Sheets: {GOOGLE_SHEET_NAME}")
            return True
            
        except Exception as e:
            # ubah log error ke bahasa inggris
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            self.gc = None
            self.sh = None
            return False
    
    def ensure_connection(self):
        if self.gc is None or self.sh is None:
            return self.init_connection()
        return True
    
    def add_transaction(self, transaction_data):
        """Menambahkan transaksi ke sheet"""
        if not self.ensure_connection():
            raise Exception("Koneksi Google Sheets tidak tersedia")
            
        try:
            # Dapatkan atau buat header
            headers = self.sh.row_values(1)
            if not headers:
                headers = ["Tanggal", "Kategori", "Deskripsi", "Pemasukan", "Pengeluaran"]
                self.sh.append_row(headers)
                logger.info("✅ Header created in Google Sheets")
            
            # Debug: log data yang akan ditambahkan
            logger.info(f"📊 Adding transaction data: {transaction_data}")
            logger.info(f"📋 Current headers: {headers}")
            
            # Siapkan data baris
            new_row = [""] * len(headers)
            for key, value in transaction_data.items():
                if key in headers:
                    index = headers.index(key)
                    # Khusus untuk tanggal, pastikan formatnya benar
                    if key == "Tanggal" and value:
                        # Jika value adalah string datetime, ambil bagian tanggal saja
                        if " " in str(value):
                            value = str(value).split(" ")[0]
                    new_row[index] = str(value) if value else ""
                    logger.debug(f"Mapping {key} -> {value} at index {index}")
            
            logger.info(f"📝 Final row data: {new_row}")
            self.sh.append_row(new_row)
            logger.info("✅ Transaction successfully added to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error menambahkan transaksi: {e}")
            raise

# Instance global
sheets_service = GoogleSheetsService()