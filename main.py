import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import TELEGRAM_BOT_TOKEN, setup_logging
from services.gsheets import sheets_service
from handlers.start import start
from handlers.catat import catat
from handlers.laporan import laporan
from handlers.error import error_handler, unknown

# Setup
os.system("clear")
logger = setup_logging()

def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("❌ TELEGRAM_BOT_TOKEN tidak ditemukan. Bot tidak bisa dijalankan.")
        return

    # Inisialisasi Google Sheets
    sheets_ok = sheets_service.init_connection()
    if not sheets_ok:
        logger.warning("⚠️ Google Sheets tidak tersedia.")

    # Setup aplikasi
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Tambahkan handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("catat", catat))
    application.add_handler(CommandHandler("laporan", laporan))
    
    # Handler untuk semua pesan teks lainnya (bukan command yang sudah didefinisikan)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    
    # Handler untuk command yang tidak dikenal (akan trigger update dashboard)
    async def handle_unknown_command(update, context):
        # Trigger auto-update dashboard setiap ada command tidak dikenal
        try:
            sheets_service.update_dashboard_data()
            logger.info("🔄 Dashboard auto-updated after unknown command received")
        except Exception as e:
            logger.warning(f"⚠️ Failed to auto-update dashboard: {e}")
        
        await unknown(update, context)
    
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    application.add_error_handler(error_handler)

    # Jalankan Bot
    logger.info("🚀 Bot mulai berjalan...")
    application.run_polling()

if __name__ == "__main__":
    main()