import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Import Konfigurasi dan Layanan
from config.settings import TELEGRAM_BOT_TOKEN, setup_logging
from config.locales import MESSAGES
from services.gsheets import GoogleSheetsService
from services.gemini import GeminiService
from handlers.start import start
from handlers.error import error_handler
from models.transaction import Transaction

# Refaktor ini mengasumsikan Anda akan mengubah handlers.laporan menjadi sebuah fungsi
# yang bisa diimpor dan dipanggil, contohnya: from handlers.laporan import generate_report
# Untuk saat ini, kita akan buat placeholder-nya.

# Setup awal
os.system("clear")
logger = setup_logging()

# Basis data sederhana di memori untuk menyimpan preferensi bahasa pengguna.
# Untuk aplikasi produksi, disarankan menggunakan database persisten.
user_language_preferences = {}

# Inisialisasi layanan-layanan utama
try:
    gemini_service = GeminiService()
    sheets_service = GoogleSheetsService()
    logger.info("✅ Layanan Gemini dan Google Sheets berhasil diinisialisasi.")
except Exception as e:
    logger.critical(f"❌ Gagal menginisialisasi layanan: {e}")
    # Jika layanan inti gagal, bot tidak bisa berjalan dengan semestinya.
    # Anda bisa memutuskan untuk keluar dari aplikasi di sini jika perlu.


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menangani callback dari tombol inline untuk pemilihan bahasa.
    Menyimpan preferensi bahasa pengguna dan mengirim konfirmasi.
    """
    query = update.callback_query
    await query.answer()  # Memberi tahu Telegram bahwa callback sudah diterima

    # Ekstrak kode bahasa dari data callback (misal: 'set_lang_id' -> 'id')
    lang_code = query.data.split('_')[-1]
    user_id = query.from_user.id
    user_language_preferences[user_id] = lang_code
    logger.info(f"Pengguna {user_id} memilih bahasa: {lang_code.upper()}")

    # Edit pesan asli untuk menampilkan pesan konfirmasi
    await query.edit_message_text(text=MESSAGES[lang_code]['language_set'])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler utama yang memproses semua pesan teks dari pengguna.
    Fungsi ini meneruskan teks ke Gemini AI, lalu bertindak berdasarkan responsnya.
    """
    user_id = update.effective_user.id
    user_text = update.message.text
    logger.info(f"Menerima pesan dari {user_id}: '{user_text}'")

    # Dapatkan preferensi bahasa pengguna, default ke 'id' jika belum ada
    lang = user_language_preferences.get(user_id, 'id')

    # Kirim teks ke Gemini untuk diproses
    structured_data = await gemini_service.process_text(user_text)
    logger.info(f"Respons terstruktur dari Gemini: {structured_data}")

    intent = structured_data.get("intent")
    entities = structured_data.get("entities", {})
    
    # Debug: Log the entities to see what's actually being returned
    logger.info(f"Intent: {intent}, Entities: {entities}")

    # Logika untuk menangani setiap niat (intent) dari Gemini
    if intent == "catat":
        try:
            # Debug: Check what keys are actually in entities
            logger.info(f"Available keys in entities: {list(entities.keys())}")
            
            # Pastikan entitas yang dibutuhkan ada
            if not all(k in entities for k in ['transaction_type', 'category', 'amount']):
                missing_keys = [k for k in ['transaction_type', 'category', 'amount'] if k not in entities]
                raise ValueError(f"Data '{', '.join(missing_keys)}' tidak ditemukan dari input. Available: {list(entities.keys())}")

            # Create Transaction object using positional arguments
            # Use today's date if no date provided
            tanggal = entities.get('date') or datetime.now().strftime('%Y-%m-%d')
            
            tx = Transaction(
                tanggal,  # positional argument 1
                entities.get('transaction_type'),  # positional argument 2
                entities.get('category'),  # positional argument 3
                int(entities.get('amount')),  # positional argument 4
                entities.get('description') or ""  # positional argument 5
            )
            tx.validate()  # Jalankan validasi pada model

            # FIXED: Convert Transaction object to dictionary format expected by Google Sheets
            transaction_dict = tx.to_sheet_data()
            logger.info(f"Transaction data for sheets: {transaction_dict}")

            # Simpan transaksi ke Google Sheets dan update dashboard
            sheets_service.add_transaction(transaction_dict)
            sheets_service.update_dashboard_data()
            logger.info(f"Transaksi berhasil dicatat untuk pengguna {user_id}")

            await update.message.reply_text(MESSAGES[lang]['catat_success'])

        except (ValueError, TypeError) as e:
            logger.error(f"Error validasi data saat mencatat: {e}")
            await update.message.reply_text(f"{MESSAGES[lang]['error_catat']}: {e}")
        except Exception as e:
            logger.error(f"Error tak terduga saat mencatat: {e}")
            await update.message.reply_text(MESSAGES[lang]['error_general'])

    elif intent == "laporan":
        logger.info(f"Niat 'laporan' terdeteksi untuk pengguna {user_id}")
        await update.message.reply_text("Fitur laporan via AI sedang dalam pengembangan. Nantikan pembaruan selanjutnya!")

    elif intent == "tidak_paham":
        logger.warning(f"Gemini tidak dapat memahami input dari {user_id}: '{user_text}'")
        await update.message.reply_text(MESSAGES[lang]['unclear_intent'])

    else:  # Termasuk intent 'error' dari Gemini
        logger.error(f"Terjadi kesalahan saat pemrosesan Gemini untuk pengguna {user_id}. Intent: {intent}, Details: {entities.get('details')}")
        await update.message.reply_text(MESSAGES[lang]['error_general'])


async def error_handler(update, context):
    logger.error(f"Error {update}: {context}")
    return True


def main():
    """Menginisialisasi dan menjalankan bot Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("❌ TELEGRAM_BOT_TOKEN tidak ditemukan. Bot tidak bisa dijalankan.")
        return

    # Inisialisasi koneksi Google Sheets saat bot dimulai
    if not sheets_service.init_connection():
        logger.warning("⚠️ Koneksi ke Google Sheets gagal saat inisialisasi.")

    # Setup aplikasi bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Daftarkan handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(set_language, pattern='^set_lang_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error handler harus didaftarkan terakhir
    application.add_error_handler(error_handler)

    # Jalankan bot
    logger.info("🚀 Bot siap dan mulai berjalan...")
    application.run_polling()


if __name__ == "__main__":
    main()
