MESSAGES = {
    'id': {
        'welcome': "🎉 Selamat datang di Reefficiency Bot!\n\nSaya siap membantu Anda mencatat dan melacak keuangan dengan mudah.\n\nSilakan pilih bahasa:",
        'language_set': '✅ Bahasa telah diatur ke Bahasa Indonesia',
        'catat_success': '✅ Transaksi berhasil dicatat!',
        'catat_success_multiple': '✅ {count} transaksi berhasil dicatat!',
        'error_catat': '❌ Gagal mencatat transaksi',
        'error_general': '❌ Terjadi kesalahan. Silakan coba lagi.',
        'unclear_intent': '❓ Maaf, saya tidak memahami maksud Anda. Silakan coba lagi dengan format yang lebih jelas.',
        'report_generated': '📊 Laporan keuangan berhasil dibuat',
        'no_data_found': '📭 Tidak ada data transaksi untuk periode yang diminta',
    },
    'en': {
        'welcome': "🎉 Welcome to Reefficiency Bot!\n\nI'm ready to help you record and track your finances easily.\n\nPlease select your language:",
        'language_set': '✅ Language has been set to English',
        'catat_success': '✅ Transaction recorded successfully!',
        'catat_success_multiple': '✅ {count} transactions recorded successfully!',
        'error_catat': '❌ Failed to record transaction',
        'error_general': '❌ An error occurred. Please try again.',
        'unclear_intent': '❓ Sorry, I don\'t understand your request. Please try again with a clearer format.',
        'report_generated': '📊 Financial report generated successfully',
        'no_data_found': '📭 No transaction data found for the requested period',
    }
}

CATEGORY_TRANSLATIONS = {
    'salary': {'id': 'Gaji', 'en': 'Salary'},
    'freelance': {'id': 'Freelance', 'en': 'Freelance'},
    'investment': {'id': 'Investasi', 'en': 'Investment'},
    'business': {'id': 'Bisnis', 'en': 'Business'},
    'bonus': {'id': 'Bonus', 'en': 'Bonus'},
    'other_income': {'id': 'Pemasukan Lain', 'en': 'Other Income'},
    'food_dining': {'id': 'Makanan & Restoran', 'en': 'Food & Dining'},
    'transportation': {'id': 'Transportasi', 'en': 'Transportation'},
    'healthcare': {'id': 'Kesehatan', 'en': 'Healthcare'},
    'utilities': {'id': 'Utilitas', 'en': 'Utilities'},
    'entertainment': {'id': 'Hiburan', 'en': 'Entertainment'},
    'shopping_clothing': {'id': 'Belanja & Pakaian', 'en': 'Shopping & Clothing'},
    'electronics': {'id': 'Elektronik', 'en': 'Electronics'},
    'education': {'id': 'Pendidikan', 'en': 'Education'},
    'insurance': {'id': 'Asuransi', 'en': 'Insurance'},
    'rent_mortgage': {'id': 'Sewa/KPR', 'en': 'Rent/Mortgage'},
    'groceries': {'id': 'Belanja Harian', 'en': 'Groceries'},
    'travel': {'id': 'Perjalanan', 'en': 'Travel'},
    'subscriptions': {'id': 'Langganan', 'en': 'Subscriptions'},
    'other_expense': {'id': 'Pengeluaran Lain', 'en': 'Other Expense'},
}

def get_category_name(category_key: str, language: str = 'id') -> str:
    """Get translated category name"""
    return CATEGORY_TRANSLATIONS.get(category_key, {}).get(language, category_key)