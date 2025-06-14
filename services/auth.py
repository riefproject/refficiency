import logging
from config.settings import get_allowed_user_ids

# Set up a logger for this module to provide visibility into the script's operations.
logger = logging.getLogger(__name__)

# --- AUTHENTICATION SERVICE ---

class AuthService:
    """
    A simple service to handle user authorization based on a predefined list of user IDs.
    """
    def __init__(self):
        """
        Initializes the AuthService by loading the list of allowed user IDs from settings.
        """
        self.allowed_user_ids = get_allowed_user_ids()
        if not self.allowed_user_ids:
             logger.warning("⚠️ AuthService initialized, but the list of allowed users is empty. All actions will be denied.")
        
    def user_is_allowed(self, user_id: int) -> bool:
        """
        Checks if a given user ID is present in the list of allowed users.
        
        Args:
            user_id (int): The ID of the user attempting to perform an action.
            
        Returns:
            bool: True if the user is allowed, False otherwise.
        """
        # This check handles the case where the list of allowed IDs is not configured or empty.
        if not self.allowed_user_ids:
            logger.warning(f"Access denied for user_id: {user_id} because the allowed user list is empty.")
            return False

        is_allowed = user_id in self.allowed_user_ids
        if not is_allowed:
             logger.warning(f"🚫 Access denied for user_id: {user_id}. Not in the allowed list.")
        
        return is_allowed

# Create a single instance of the AuthService to be used throughout the application.
auth_service = AuthService()
