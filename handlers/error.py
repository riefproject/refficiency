def error_handler(error_type, message):
    """Handle different types of errors with appropriate formatting"""
    print(f"Error [{error_type}]: {message}")
    return False

def unknown(message="Unknown error occurred"):
    """Handle unknown errors"""
    print(f"Unknown Error: {message}")
    return False