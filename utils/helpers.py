from telegram import Update
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class MessageHelper:
    """Helper untuk mengirim pesan dengan formatting yang konsisten"""
    
    @staticmethod
    async def send_message(update: Update, text: str, parse_mode: str = 'Markdown'):
        """Kirim pesan dengan parse mode default Markdown"""
        try:
            await update.message.reply_text(text, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"❌ Error saat mengirim pesan: {e}")
            # Fallback tanpa parse mode jika ada error
            try:
                await update.message.reply_text(text)
            except Exception as fallback_error:
                logger.error(f"❌ Error fallback saat mengirim pesan: {fallback_error}")
    
    @staticmethod
    async def send_error(update: Update, message: str):
        """Kirim pesan error dengan format konsisten"""
        await MessageHelper.send_message(update, f"❌ {message}")
    
    @staticmethod
    async def send_success(update: Update, message: str):
        """Kirim pesan sukses dengan format konsisten"""
        await MessageHelper.send_message(update, f"✅ {message}")
    
    @staticmethod
    async def send_info(update: Update, message: str):
        """Kirim pesan info dengan format konsisten"""
        await MessageHelper.send_message(update, f"ℹ️ {message}")
    
    @staticmethod
    async def send_warning(update: Update, message: str):
        """Kirim pesan warning dengan format konsisten"""
        await MessageHelper.send_message(update, f"⚠️ {message}")
    
    @staticmethod
    def format_currency(amount: int) -> str:
        """Format angka menjadi currency Indonesia"""
        return f"Rp {amount:,}"
    
    @staticmethod
    def bold(text: str) -> str:
        """Format text menjadi bold"""
        return f"*{text}*"
    
    @staticmethod
    def code(text: str) -> str:
        """Format text menjadi inline code"""
        return f"`{text}`"
    
    @staticmethod
    def italic(text: str) -> str:
        """Format text menjadi italic"""
        return f"_{text}_"

# Alias untuk kemudahan
msg = MessageHelper