from datetime import datetime
from dataclasses import dataclass

# Import category model (assuming it exists)
try:
    from models.category import TransactionCategory
except ImportError:
    # Fallback if category model doesn't exist yet
    class TransactionCategory:
        @staticmethod
        def categorize(text):
            return text
        
        class OTHER_EXPENSE:
            value = "other_expense"

@dataclass
class Transaction:
    def __init__(self, tanggal, jenis, kategori, jumlah, deskripsi):
        self.tanggal = tanggal
        self.jenis = jenis
        self.kategori = self._validate_category(kategori)
        self.jumlah = jumlah
        self.deskripsi = deskripsi
    
    def _validate_category(self, kategori):
        """Validate and standardize category"""
        if isinstance(kategori, str):
            # If TransactionCategory is available, use it for validation
            if hasattr(TransactionCategory, 'categorize'):
                try:
                    # Check if it's already a valid category enum value
                    valid_categories = [cat.value for cat in TransactionCategory]
                    if kategori in valid_categories:
                        return kategori
                    # Try to map from Indonesian keywords
                    mapped_category = TransactionCategory.categorize(kategori)
                    return mapped_category.value
                except:
                    pass
            # Return as-is if no validation available
            return kategori
        return "other_expense"  # Default fallback
    
    def to_sheet_data(self):
        """Return data with English headers to match spreadsheet"""
        pemasukan = self.jumlah if self.jenis.lower() == "pemasukan" else ""
        pengeluaran = self.jumlah if self.jenis.lower() == "pengeluaran" else ""
        
        return {
            "Date": self.tanggal,           # Changed from "Tanggal"
            "Category": self.kategori,      # Changed from "Kategori"
            "Description": self.deskripsi,  # Changed from "Deskripsi"
            "Income": pemasukan,            # Changed from "Pemasukan"
            "Expenditure": pengeluaran      # Changed from "Pengeluaran"
        }
    
    def validate(self):
        if self.jenis.lower() not in ["pemasukan", "pengeluaran"]:
            raise ValueError("Jenis transaksi harus 'pemasukan' atau 'pengeluaran'")
        if self.jumlah <= 0:
            raise ValueError("Jumlah harus lebih dari 0")