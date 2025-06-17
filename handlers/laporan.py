"""
Laporan Handler
==============

Handler untuk generate berbagai jenis laporan keuangan.
"""

import logging
from datetime import datetime
from calendar import month_name
from services.gsheets import GoogleSheetsService

logger = logging.getLogger(__name__)

class LaporanService:
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service
    
    def generate_report(self, period: str, year: int = None, month: int = None) -> str:
        """
        Generate laporan berdasarkan period yang diminta.
        
        Args:
            period: 'bulanan' atau 'tahunan'
            year: tahun laporan (optional, default tahun sekarang)
            month: bulan laporan untuk laporan bulanan (1-12)
        
        Returns:
            str: Formatted report text
        """
        try:
            if not self.sheets_service.ensure_connection():
                return "❌ Tidak dapat terhubung ke Google Sheets untuk mengambil data laporan."
            
            current_year = datetime.now().year
            target_year = year or current_year
            
            if period == 'bulanan':
                return self._generate_monthly_report(target_year, month)
            elif period == 'tahunan':
                return self._generate_annual_report(target_year)
            else:
                return "❌ Jenis laporan tidak dikenali. Gunakan 'bulanan' atau 'tahunan'."
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"❌ Terjadi kesalahan saat membuat laporan: {str(e)}"
    
    def _generate_monthly_report(self, year: int, month: int = None) -> str:
        """Generate laporan bulanan."""
        try:
            current_month = datetime.now().month
            target_month = month or current_month
            
            if not (1 <= target_month <= 12):
                return "❌ Bulan tidak valid. Gunakan angka 1-12."
            
            # Format sheet name (M/YY)
            year_short = str(year)[2:]  # Get last 2 digits
            sheet_name = f"{target_month}/{year_short}"
            month_name_str = month_name[target_month]
            
            try:
                worksheet = self.sheets_service.spreadsheet.worksheet(sheet_name)
            except:
                return f"📊 Tidak ada data transaksi untuk {month_name_str} {year}."
            
            # Get summary data
            summary = self.sheets_service._get_sheet_summary(worksheet)
            
            # Get all transactions for detailed breakdown
            all_data = worksheet.get_all_records()
            
            # Build report
            report = f"📊 *LAPORAN BULANAN - {month_name_str.upper()} {year}*\n"
            report += "=" * 40 + "\n\n"
            
            # Summary section
            report += "💰 *RINGKASAN KEUANGAN*\n"
            report += f"- Total Pemasukan: Rp {summary['total_income']:,.0f}\n"
            report += f"- Total Pengeluaran: Rp {summary['total_expenditure']:,.0f}\n"
            report += f"- Selisih Bersih: Rp {summary['net_difference']:,.0f}\n\n"
            
            # Category breakdown
            if summary['categories']:
                report += "📈 *PENGELUARAN PER KATEGORI*\n"
                sorted_categories = sorted(summary['categories'].items(), key=lambda x: x[1], reverse=True)
                for category, amount in sorted_categories:
                    percentage = (amount / summary['total_expenditure'] * 100) if summary['total_expenditure'] > 0 else 0
                    report += f"- {category}: Rp {amount:,.0f} ({percentage:.1f}%)\n"
                report += "\n"
            
            # Recent transactions (last 5)
            if all_data:
                report += "📝 *5 TRANSAKSI TERAKHIR*\n"
                recent_transactions = all_data[-5:] if len(all_data) >= 5 else all_data
                for transaction in reversed(recent_transactions):
                    tanggal = transaction.get('Tanggal', '')
                    kategori = transaction.get('Kategori', '')
                    deskripsi = transaction.get('Deskripsi', '')
                    pemasukan = transaction.get('Pemasukan', '')
                    pengeluaran = transaction.get('Pengeluaran', '')
                    
                    if pemasukan:
                        report += f"- {tanggal} | {kategori} | +Rp {pemasukan:,.0f}"
                    elif pengeluaran:
                        report += f"- {tanggal} | {kategori} | -Rp {pengeluaran:,.0f}"
                    
                    if deskripsi:
                        report += f" | {deskripsi}"
                    report += "\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            return f"❌ Gagal membuat laporan bulanan: {str(e)}"
    
    def _generate_annual_report(self, year: int) -> str:
        """Generate laporan tahunan."""
        try:
            # Get all monthly data for the year
            monthly_data = self.sheets_service.get_monthly_sheets()
            year_data = {k: v for k, v in monthly_data.items() if v['year'] == year}
            
            if not year_data:
                return f"📊 Tidak ada data transaksi untuk tahun {year}."
            
            # Calculate annual totals
            total_income = 0
            total_expenditure = 0
            all_categories = {}
            monthly_summaries = {}
            
            for sheet_name, data in year_data.items():
                month_num = data['month']
                summary = data['data']
                
                total_income += summary['total_income']
                total_expenditure += summary['total_expenditure']
                
                # Aggregate categories
                for category, amount in summary['categories'].items():
                    all_categories[category] = all_categories.get(category, 0) + amount
                
                # Store monthly summary
                monthly_summaries[month_num] = summary
            
            net_difference = total_income - total_expenditure
            
            # Build report
            report = f"📊 *LAPORAN TAHUNAN - {year}*\n"
            report += "----------------------------------------------------\n\n"
            
            # Annual summary
            report += "💰 *RINGKASAN TAHUNAN*\n"
            report += f"- Total Pemasukan\t: Rp {total_income:,.0f}\n"
            report += f"- Total Pengeluaran\t: Rp {total_expenditure:,.0f}\n"
            report += f"- Selisih Bersih\t: Rp {net_difference:,.0f}\n\n"
            
            # Monthly breakdown
            report += "📅 *BREAKDOWN BULANAN*\n"
            for month_num in range(1, 13):
                month_name_str = month_name[month_num][:3]  # Abbreviated month name
                if month_num in monthly_summaries:
                    summary = monthly_summaries[month_num]
                    report += f"- {month_name_str}: +Rp {summary['total_income']:,.0f} | -Rp {summary['total_expenditure']:,.0f} | "
                    report += f"Net: Rp {summary['net_difference']:,.0f}\n"
                else:
                    report += f"- {month_name_str}: Tidak ada data\n"
            report += "\n"
            
            # Top categories
            if all_categories:
                report += "📈 *TOP 5 KATEGORI PENGELUARAN*\n"
                sorted_categories = sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[:5]
                for i, (category, amount) in enumerate(sorted_categories, 1):
                    percentage = (amount / total_expenditure * 100) if total_expenditure > 0 else 0
                    report += f"{i}. {category}: Rp {amount:,.0f} ({percentage:.1f}%)\n"
                report += "\n"
            
            # Financial health indicators
            report += "🏥 *INDIKATOR KESEHATAN KEUANGAN*\n"
            if total_income > 0:
                savings_rate = (net_difference / total_income * 100)
                if savings_rate > 20:
                    health_status = "Sangat Baik ✅"
                elif savings_rate > 10:
                    health_status = "Baik 👍"
                elif savings_rate > 0:
                    health_status = "Cukup ⚠️"
                else:
                    health_status = "Perlu Perbaikan ❌"
                
                report += f"- Tingkat Tabungan: {savings_rate:.1f}% ({health_status})\n"
                report += f"- Rata-rata Pengeluaran/Bulan: Rp {total_expenditure/12:,.0f}\n"
                report += f"- Rata-rata Pemasukan/Bulan: Rp {total_income/12:,.0f}\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating annual report: {e}")
            return f"❌ Gagal membuat laporan tahunan: {str(e)}"

# Create service instance that can be imported
laporan_service = None

def get_laporan_service(sheets_service: GoogleSheetsService) -> LaporanService:
    """Get or create laporan service instance."""
    global laporan_service
    if laporan_service is None:
        laporan_service = LaporanService(sheets_service)
    return laporan_service