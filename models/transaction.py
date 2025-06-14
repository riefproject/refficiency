from datetime import datetime
from dataclasses import dataclass

@dataclass
class Transaction:
    def __init__(self, tanggal, jenis, kategori, jumlah, deskripsi):
        self.tanggal = tanggal
        self.jenis = jenis
        self.kategori = kategori
        self.jumlah = jumlah
        self.deskripsi = deskripsi
    
    def to_sheet_data(self):
        """Return data sebagai dictionary untuk mapping ke header"""
        pemasukan = self.jumlah if self.jenis.lower() == "pemasukan" else ""
        pengeluaran = self.jumlah if self.jenis.lower() == "pengeluaran" else ""
        
        return {
            "Tanggal": self.tanggal,
            "Kategori": self.kategori,
            "Deskripsi": self.deskripsi,
            "Pemasukan": pemasukan,
            "Pengeluaran": pengeluaran
        }
    
    def validate(self):
        if self.jenis.lower() not in ["pemasukan", "pengeluaran"]:
            raise ValueError("Jenis transaksi harus 'pemasukan' atau 'pengeluaran'")
        if self.jumlah <= 0:
            raise ValueError("Jumlah harus lebih dari 0")