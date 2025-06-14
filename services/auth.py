import logging
from config.settings import get_allowed_user_ids

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.allowed_user_ids = get_allowed_user_ids()
        
    def user_is_allowed(self, user_id: int) -> bool:
        """Memeriksa apakah user diizinkan"""
        if not self.allowed_user_ids:
            logger.warning(f"Akses ditolak untuk {user_id} karena ALLOWED_USER_IDS kosong.")
            return False
        return user_id in self.allowed_user_ids

# Instance global
auth_service = AuthService()