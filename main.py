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
from handlers.laporan import get_laporan_service
from models.transaction import Transaction

# Setup awal
os.system("clear")
logger = setup_logging()

# Basis data sederhana di memori untuk menyimpan preferensi bahasa pengguna.
user_language_preferences = {}

# Inisialisasi layanan-layanan utama
try:
    gemini_service = GeminiService()
    sheets_service = GoogleSheetsService()
    laporan_service = get_laporan_service(sheets_service)  # Add laporan service
    logger.info("✅ Layanan Gemini, Google Sheets, dan Laporan berhasil diinisialisasi.")
except Exception as e:
    logger.critical(f"❌ Gagal menginisialisasi layanan: {e}")


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menangani callback dari tombol inline untuk pemilihan bahasa.
    Menyimpan preferensi bahasa pengguna dan mengirim konfirmasi.
    """
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split('_')[-1]
    user_id = query.from_user.id
    user_language_preferences[user_id] = lang_code
    logger.info(f"Pengguna {user_id} memilih bahasa: {lang_code.upper()}")

    await query.edit_message_text(text=MESSAGES[lang_code]['language_set'])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler utama yang memproses semua pesan teks dari pengguna.
    Fungsi ini meneruskan teks ke Gemini AI, lalu bertindak berdasarkan responsnya.
    """
    user_id = update.effective_user.id
    user_text = update.message.text
    logger.info(f"Menerima pesan dari {user_id}: '{user_text}'")

    lang = user_language_preferences.get(user_id, 'id')

    # Kirim teks ke Gemini untuk diproses
    structured_data = await gemini_service.process_text(user_text)
    logger.info(f"Respons terstruktur dari Gemini: {structured_data}")

    intent = structured_data.get("intent")
    entities = structured_data.get("entities", {})
    
    logger.info(f"Intent: {intent}, Entities: {entities}")

    # Logika untuk menangani setiap niat (intent) dari Gemini
    if intent == "catat":
        try:
            # Check if multiple transactions
            if "transactions" in entities:
                # Handle multiple transactions
                success_count = 0
                for tx_data in entities["transactions"]:
                    try:
                        tanggal = tx_data.get('date') or datetime.now().strftime('%Y-%m-%d')
                        
                        # Convert English transaction_type back to Indonesian for Transaction class
                        jenis = "pemasukan" if tx_data.get('transaction_type') == 'income' else "pengeluaran"
                        
                        tx = Transaction(
                            tanggal,
                            jenis,
                            tx_data.get('category'),
                            int(tx_data.get('amount')),
                            tx_data.get('description') or ""
                        )
                        tx.validate()

                        # Convert Transaction object to dictionary format expected by Google Sheets
                        transaction_dict = tx.to_sheet_data()
                        logger.info(f"Transaction data for sheets: {transaction_dict}")

                        sheets_service.add_transaction(transaction_dict)
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing individual transaction: {e}")
                        continue
                
                if success_count > 0:
                    sheets_service.update_dashboard_data()
                    await update.message.reply_text(
                        MESSAGES[lang]['catat_success_multiple'].format(count=success_count)
                    )
                else:
                    await update.message.reply_text(MESSAGES[lang]['error_catat'])
                    
            else:
                # Handle single transaction (existing logic)
                logger.info(f"Available keys in entities: {list(entities.keys())}")
                
                if not all(k in entities for k in ['transaction_type', 'category', 'amount']):
                    missing_keys = [k for k in ['transaction_type', 'category', 'amount'] if k not in entities]
                    raise ValueError(f"Data '{', '.join(missing_keys)}' tidak ditemukan dari input. Available: {list(entities.keys())}")

                # Create Transaction object using positional arguments
                tanggal = entities.get('date') or datetime.now().strftime('%Y-%m-%d')
                
                # Convert English transaction_type back to Indonesian for Transaction class
                jenis = "pemasukan" if entities.get('transaction_type') == 'income' else "pengeluaran"
                
                tx = Transaction(
                    tanggal,
                    jenis,
                    entities.get('category'),
                    int(entities.get('amount')),
                    entities.get('description') or ""
                )
                tx.validate()

                # Convert Transaction object to dictionary format expected by Google Sheets
                transaction_dict = tx.to_sheet_data()
                logger.info(f"Transaction data for sheets: {transaction_dict}")

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
        try:
            # Extract report parameters
            period = entities.get('period', 'bulanan')
            year = entities.get('year')
            month = entities.get('month')
            
            logger.info(f"Generating report: period={period}, year={year}, month={month}")
            
            # Generate report using laporan service
            report_text = laporan_service.generate_report(period, year, month)
            
            # Send report (split if too long for Telegram)
            if len(report_text) > 4096:
                # Split long reports into chunks
                chunks = [report_text[i:i+4096] for i in range(0, len(report_text), 4096)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await update.message.reply_text(chunk,  parse_mode='Markdown')
                    else:
                        await update.message.reply_text(f"*LANJUTAN {i+1}*\n\n{chunk}",  parse_mode='Markdown')
            else:
                await update.message.reply_text(report_text,  parse_mode='Markdown')
            
            logger.info(f"Laporan berhasil dikirim untuk pengguna {user_id}")
            
        except Exception as e:
            logger.error(f"Error saat membuat laporan: {e}")
            await update.message.reply_text(f"❌ Gagal membuat laporan: {str(e)}")

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