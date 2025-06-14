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
                "Format: `\\/catat jenis kategori jumlah [deskripsi] [tanggal]`\n"
                "Contoh:\n"
                "• `\\/catat pengeluaran makanan 50000 Nasi Padang`\n"
                "• `\\/catat pemasukan gaji 5000000 THR 2025-06-10`\n"
                "Tanggal format: YYYY-MM-DD (opsional, default hari ini)",
                parse_mode='Markdown'
            )
            return

        # Parse argumen - cek apakah ada tanggal di akhir
        tanggal_input = None
        
        # Cek apakah argumen terakhir adalah tanggal (format YYYY-MM-DD)
        if len(args) >= 4:
            last_arg = args[-1]
            if len(last_arg) == 10 and last_arg.count('-') == 2:
                try:
                    # Validasi format tanggal
                    datetime.strptime(last_arg, "%Y-%m-%d")
                    tanggal_input = last_arg
                    args = args[:-1]  # Hapus tanggal dari args
                except ValueError:
                    # Bukan tanggal valid, treat sebagai deskripsi
                    pass

        # Parse argumen normal
        jenis_transaksi = args[0].lower()
        kategori = args[1]
        jumlah_str = args[2]
        deskripsi = " ".join(args[3:]) if len(args) > 3 else "-"

        # Tentukan tanggal
        if tanggal_input:
            tanggal_final = tanggal_input
        else:
            tanggal_final = datetime.now().strftime("%Y-%m-%d")

        # Konversi jumlah
        try:
            jumlah = int(jumlah_str.replace(",", "").replace(".", ""))
        except ValueError:
            await update.message.reply_text("Jumlah harus berupa angka positif.",parse_mode='Markdown')
            return

        # Buat objek transaksi
        transaction = Transaction(
            tanggal=tanggal_final,
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
        
        tanggal_display = tanggal_input if tanggal_input else "Hari ini"
        
        await update.message.reply_text(
            f"✅ Berhasil dicatat:\n"
            f"Tanggal: {tanggal_display}\n"
            f"Jenis: {jenis_transaksi.capitalize()}\n"
            f"Kategori: {kategori}\n"
            f"Jumlah: {jumlah:,}\n"
            f"Deskripsi: {deskripsi}",
            parse_mode='Markdown'
        )
        logger.info(f"📝 Transaksi dicatat: {user_id} - {tanggal_final} - {jenis_transaksi} - {kategori} - {jumlah}")

    except ValueError as e:
        await update.message.reply_text(f"Error: {e}", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Terjadi error saat mencatat: {e}", parse_mode='Markdown')
        logger.error(f"❌ Error saat mencatat untuk user {user_id}: {e}", exc_info=True)