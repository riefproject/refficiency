# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.auth import AuthService
from config.locales import MESSAGES

auth_service = AuthService()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not auth_service.user_is_allowed(user_id):
        await update.message.reply_text("⛔️ Anda tidak diizinkan menggunakan bot ini.")
        return

    keyboard = [
        [InlineKeyboardButton("Bahasa Indonesia 🇮🇩", callback_data='set_lang_id')],
        [InlineKeyboardButton("English 🇬🇧", callback_data='set_lang_en')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Kirim pesan selamat datang dari kedua bahasa agar mudah dipahami
    welcome_text = MESSAGES['id']['welcome'] + "\n\n" + MESSAGES['en']['welcome']
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)