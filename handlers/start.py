from telegram import Update
from telegram.ext import ContextTypes
from services.auth import auth_service
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not auth_service.user_is_allowed(user_id):
        await update.message.reply_text("Maaf, Anda tidak diizinkan menggunakan bot ini.",parse_mode='Markdown')
        logger.warning(f"⚠️ Akses ditolak untuk /start dari user ID: {user_id}")
        return

    await update.message.reply_text(
        "Halo! Saya bot pencatat keuangan.\n\n"
        "*📝 Perintah yang tersedia:*\n\n"
        "*Mencatat Transaksi:*\n"
        "/catat `jenis kategori jumlah [deskripsi]`\n"
        "Contoh:\n"
        "/catat `pengeluaran makanan 50000 Nasi Padang`\n"
        "/catat `pemasukan gaji 5000000 Gaji bulanan`\n\n"
        "*Melihat Laporan:*\n"
        "/laporan `[bulan]` - Laporan bulan terakhir\n"
        "/laporan `[tahun]` - Laporan tahun terakhir\n"
        "/laporan `[bulan] [tahun]` - Laporan spesifik\n\n"
        "Contoh:\n"
        "/laporan `januari`\n"
        "/laporan `2024`\n"
        "/laporan `februari 2024`\n\n"
        "Jenis transaksi: `pengeluaran` atau `pemasukan`",
        parse_mode='Markdown'
    )