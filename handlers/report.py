from telegram import Update
from telegram.ext import ContextTypes
from services.auth import auth_service
from services.gsheets import sheets_service
from datetime import datetime, timedelta
import logging
import calendar

logger = logging.getLogger(__name__)

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not auth_service.user_is_allowed(user_id):
        await update.message.reply_text("Maaf, Anda tidak diizinkan menggunakan bot ini.",parse_mode='Markdown')
        logger.warning(f"⚠️ Akses ditolak untuk /laporan dari user ID: {user_id}")
        return

    try:
        args = context.args
        now = datetime.now()
        
        if len(args) == 0:
            await update.message.reply_text(
                "Format salah. Gunakan:\n"
                "`/laporan [bulan]` - Laporan bulan terakhir\n"
                "`/laporan [tahun]` - Laporan tahun terakhir\n"
                "`/laporan [bulan] [tahun]` - Laporan bulan dan tahun spesifik\n\n"
                "Contoh:\n"
                "`/laporan januari`\n"
                "`/laporan 2024`\n"
                "`/laporan februari 2024`",
                parse_mode='Markdown'
            )
            return

        if len(args) == 1:
            # Cek apakah input adalah tahun atau bulan
            arg = args[0].lower()
            
            # Coba parse sebagai tahun
            try:
                year = int(arg)
                if year < 1900 or year > 2100:
                    raise ValueError("Tahun tidak valid")
                
                # Laporan tahunan
                await generate_yearly_report(update, year, now)
                return
                
            except ValueError:
                # Bukan tahun, anggap sebagai bulan
                month_num = parse_month_name(arg)
                if month_num is None:
                    await update.message.reply_text(
                        "Format bulan tidak valid. Gunakan nama bulan dalam bahasa Indonesia.\n"
                        "Contoh: januari, februari, maret, dst.",
                        parse_mode='Markdown'
                    )
                    return
                
                # Tentukan tahun (tahun lalu jika bulan sudah lewat tahun ini)
                if month_num > now.month:
                    year = now.year - 1
                else:
                    year = now.year
                
                await generate_monthly_report(update, month_num, year, now)
                return

        elif len(args) == 2:
            # Format: bulan tahun
            month_name = args[0].lower()
            month_num = parse_month_name(month_name)
            
            if month_num is None:
                await update.message.reply_text(
                    "Format bulan tidak valid. Gunakan nama bulan dalam bahasa Indonesia.\n"
                    "Contoh: januari, februari, maret, dst.",
                    parse_mode='Markdown'
                )
                return
            
            try:
                year = int(args[1])
                if year < 1900 or year > 2100:
                    raise ValueError("Tahun tidak valid")
            except ValueError:
                await update.message.reply_text("Format tahun tidak valid.",parse_mode='Markdown')
                return
            
            # Cek apakah bulan dan tahun sudah berlangsung
            target_date = datetime(year, month_num, 1)
            if target_date > now:
                month_name_cap = calendar.month_name[month_num]
                await update.message.reply_text(
                    f"❌ Bulan {month_name_cap} dan tahun {year} belum berlangsung.",
                    parse_mode='Markdown'
                )
                return
            
            await generate_monthly_report(update, month_num, year, now)
            return

        else:
            await update.message.reply_text("Terlalu banyak parameter. Maksimal 2 parameter.",parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"Terjadi error saat membuat laporan: {e}",parse_mode='Markdown')
        logger.error(f"❌ Error saat membuat laporan untuk user {user_id}: {e}", exc_info=True)

def parse_month_name(month_name):
    """Konversi nama bulan Indonesia ke nomor bulan"""
    months = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
    }
    return months.get(month_name.lower())

def get_month_name(month_num):
    """Konversi nomor bulan ke nama bulan Indonesia"""
    months = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    return months.get(month_num, 'Unknown')

async def generate_monthly_report(update: Update, month: int, year: int, now: datetime):
    """Generate laporan bulanan"""
    try:
        if not sheets_service.ensure_connection():
            await update.message.reply_text("❌ Tidak dapat terhubung ke Google Sheets.",parse_mode='Markdown')
            return

        # Ambil semua data dari sheet
        all_records = sheets_service.sh.get_all_records()
        
        # Filter data berdasarkan bulan dan tahun
        monthly_data = []
        for record in all_records:
            if not record.get('Tanggal'):
                continue
                
            try:
                # Parse tanggal (format: YYYY-MM-DD HH:MM:SS)
                date_str = record['Tanggal'].split(' ')[0]  # Ambil bagian tanggal saja
                record_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if record_date.month == month and record_date.year == year:
                    monthly_data.append(record)
            except:
                continue

        # Hitung total pemasukan dan pengeluaran
        total_pemasukan = 0
        total_pengeluaran = 0
        kategori_pemasukan = {}
        kategori_pengeluaran = {}

        for record in monthly_data:
            pemasukan = record.get('Pemasukan', 0)
            pengeluaran = record.get('Pengeluaran', 0)
            kategori = record.get('Kategori', 'Lainnya')

            # Konversi ke int jika berupa string
            try:
                if pemasukan and str(pemasukan).replace(',', '').replace('.', '').isdigit():
                    pemasukan = int(str(pemasukan).replace(',', '').replace('.', ''))
                    total_pemasukan += pemasukan
                    kategori_pemasukan[kategori] = kategori_pemasukan.get(kategori, 0) + pemasukan
                else:
                    pemasukan = 0
            except:
                pemasukan = 0

            try:
                if pengeluaran and str(pengeluaran).replace(',', '').replace('.', '').isdigit():
                    pengeluaran = int(str(pengeluaran).replace(',', '').replace('.', ''))
                    total_pengeluaran += pengeluaran
                    kategori_pengeluaran[kategori] = kategori_pengeluaran.get(kategori, 0) + pengeluaran
                else:
                    pengeluaran = 0
            except:
                pengeluaran = 0

        # Format laporan
        month_name = get_month_name(month)
        saldo = total_pemasukan - total_pengeluaran
        
        report = f"*📊 LAPORAN {month_name.upper()} {year}*\n\n"
        report += f"💰 Total Pemasukan: Rp {total_pemasukan:,}\n"
        report += f"💸 Total Pengeluaran: Rp {total_pengeluaran:,}\n"
        report += f"📈 Saldo: Rp {saldo:,}\n\n"

        # Detail kategori pemasukan
        if kategori_pemasukan:
            report += "📈 *Detail Pemasukan:*\n"
            for kat, jumlah in sorted(kategori_pemasukan.items(), key=lambda x: x[1], reverse=True):
                report += f"• {kat}: Rp {jumlah:,}\n"
            report += "\n"

        # Detail kategori pengeluaran
        if kategori_pengeluaran:
            report += "*📉 Detail Pengeluaran:*\n"
            for kat, jumlah in sorted(kategori_pengeluaran.items(), key=lambda x: x[1], reverse=True):
                report += f"• {kat}: Rp {jumlah:,}\n"
            report += "\n"

        report += f"📝 Total Transaksi: {len(monthly_data)}"

        await update.message.reply_text(report, parse_mode='Markdown')
        logger.info(f"📊 Laporan bulanan dikirim: {month_name} {year} untuk user {update.effective_user.id}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error saat membuat laporan bulanan: {e}", parse_mode='Markdown')
        logger.error(f"❌ Error laporan bulanan: {e}", exc_info=True)

async def generate_yearly_report(update: Update, year: int, now: datetime):
    """Generate laporan tahunan"""
    try:
        # Cek apakah tahun sudah berlangsung
        if year > now.year:
            await update.message.reply_text(f"❌ Tahun {year} belum berlangsung.",parse_mode='Markdown')
            return

        if not sheets_service.ensure_connection():
            await update.message.reply_text("❌ Tidak dapat terhubung ke Google Sheets.", parse_mode='Markdown')
            return

        # Ambil semua data dari sheet
        all_records = sheets_service.sh.get_all_records()
        
        # Filter data berdasarkan tahun
        yearly_data = []
        for record in all_records:
            if not record.get('Tanggal'):
                continue
                
            try:
                # Parse tanggal (format: YYYY-MM-DD HH:MM:SS)
                date_str = record['Tanggal'].split(' ')[0]  # Ambil bagian tanggal saja
                record_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                if record_date.year == year:
                    yearly_data.append(record)
            except:
                continue

        # Hitung total pemasukan dan pengeluaran
        total_pemasukan = 0
        total_pengeluaran = 0
        monthly_summary = {}
        kategori_pemasukan = {}
        kategori_pengeluaran = {}

        for record in yearly_data:
            pemasukan = record.get('Pemasukan', 0)
            pengeluaran = record.get('Pengeluaran', 0)
            kategori = record.get('Kategori', 'Lainnya')
            
            # Ambil bulan untuk summary bulanan
            try:
                date_str = record['Tanggal'].split(' ')[0]
                record_date = datetime.strptime(date_str, '%Y-%m-%d')
                month_name = get_month_name(record_date.month)
                
                if month_name not in monthly_summary:
                    monthly_summary[month_name] = {'pemasukan': 0, 'pengeluaran': 0}
            except:
                month_name = 'Unknown'

            # Konversi ke int jika berupa string
            try:
                if pemasukan and str(pemasukan).replace(',', '').replace('.', '').isdigit():
                    pemasukan = int(str(pemasukan).replace(',', '').replace('.', ''))
                    total_pemasukan += pemasukan
                    kategori_pemasukan[kategori] = kategori_pemasukan.get(kategori, 0) + pemasukan
                    if month_name in monthly_summary:
                        monthly_summary[month_name]['pemasukan'] += pemasukan
                else:
                    pemasukan = 0
            except:
                pemasukan = 0

            try:
                if pengeluaran and str(pengeluaran).replace(',', '').replace('.', '').isdigit():
                    pengeluaran = int(str(pengeluaran).replace(',', '').replace('.', ''))
                    total_pengeluaran += pengeluaran
                    kategori_pengeluaran[kategori] = kategori_pengeluaran.get(kategori, 0) + pengeluaran
                    if month_name in monthly_summary:
                        monthly_summary[month_name]['pengeluaran'] += pengeluaran
                else:
                    pengeluaran = 0
            except:
                pengeluaran = 0

        # Format laporan
        saldo = total_pemasukan - total_pengeluaran
        
        report = f"*📊 LAPORAN TAHUN {year}*\n\n"
        report += f"💰 Total Pemasukan: Rp {total_pemasukan:,}\n"
        report += f"💸 Total Pengeluaran: Rp {total_pengeluaran:,}\n"
        report += f"📈 Saldo: Rp {saldo:,}\n\n"

        # Summary bulanan
        if monthly_summary:
            report += "*📅 Summary Bulanan:*\n"
            for month_name in ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']:
                if month_name in monthly_summary:
                    data = monthly_summary[month_name]
                    saldo_bulan = data['pemasukan'] - data['pengeluaran']
                    report += f"• {month_name}: Rp {saldo_bulan:,}\n"
            report += "\n"

        # Top 5 kategori pengeluaran
        if kategori_pengeluaran:
            report += "*🔝 Top 5 Kategori Pengeluaran:*\n"
            sorted_pengeluaran = sorted(kategori_pengeluaran.items(), key=lambda x: x[1], reverse=True)
            for i, (kat, jumlah) in enumerate(sorted_pengeluaran[:5], 1):
                report += f"{i}. {kat}: Rp {jumlah:,}\n"
            report += "\n"

        report += f"📝 Total Transaksi: {len(yearly_data)}"

        await update.message.reply_text(report,parse_mode='Markdown')
        logger.info(f"📊 Laporan tahunan dikirim: {year} untuk user {update.effective_user.id}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error saat membuat laporan tahunan: {e}",parse_mode='Markdown')
        logger.error(f"❌ Error laporan tahunan: {e}", exc_info=True)