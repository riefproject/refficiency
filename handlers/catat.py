from telegram import Update
from telegram.ext import ContextTypes
from services.auth import auth_service
from services.gsheets import sheets_service
from models.transaction import Transaction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not auth_service.user_is_allowed(user_id):
        await update.message.reply_text("Maaf, Anda tidak diizinkan menggunakan bot ini.", parse_mode='Markdown')
        logger.warning(f"⚠️ Akses ditolak untuk /catat dari user ID: {user_id}")
        return

    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "Format salah. Gunakan: `\\/catat jenis kategori jumlah [deskripsi]`\n"
                "Contoh: `\\/catat pengeluaran makanan 50000 Nasi Padang`",
                parse_mode='Markdown'
            )
            return

        # Parse argumen
        jenis_transaksi = args[0].lower()
        kategori = args[1]
        jumlah_str = args[2]
        deskripsi = " ".join(args[3:]) if len(args) > 3 else "-"

        # Konversi jumlah
        try:
            jumlah = int(jumlah_str.replace(",", "").replace(".", ""))
        except ValueError:
            await update.message.reply_text("Jumlah harus berupa angka positif.",parse_mode='Markdown')
            return

        
        # Buat objek transaksi
        transaction = Transaction(
            tanggal=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Tambah jam juga
            jenis=jenis_transaksi,
            kategori=kategori,
            jumlah=jumlah,
            deskripsi=deskripsi
        )
        
        # Validasi
        transaction.validate()
        
        # Debug: log data sebelum kirim ke sheets
        sheet_data = transaction.to_sheet_data()
        logger.info(f"📊 Data untuk sheets: {sheet_data}")
        
        # Simpan ke Google Sheets
        sheets_service.add_transaction(sheet_data)
        
        await update.message.reply_text(
            f"✅ Berhasil dicatat:\n"
            f"Jenis: {jenis_transaksi.capitalize()}\n"
            f"Kategori: {kategori}\n"
            f"Jumlah: {jumlah:,}\n"
            f"Deskripsi: {deskripsi}",
            parse_mode='Markdown'
        )
        logger.info(f"📝 Transaksi dicatat: {user_id} - {jenis_transaksi} - {kategori} - {jumlah}")

    except ValueError as e:
        await update.message.reply_text(f"Error: {e}", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Terjadi error saat mencatat: {e}", parse_mode='Markdown')
        logger.error(f"❌ Error saat mencatat untuk user {user_id}: {e}", exc_info=True)