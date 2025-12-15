"""Password policy validation."""
import re
from error_handlers import ValidationError

# Password policy constants
MIN_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGIT = True
REQUIRE_SPECIAL = True
SPECIAL_CHARS = r'[!@#$%^&*(),.?":{}|<>]'


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against policy.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < MIN_LENGTH:
        return False, f"Password must be at least {MIN_LENGTH} characters long"
    
    if REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if REQUIRE_SPECIAL and not re.search(SPECIAL_CHARS, password):
        return False, f"Password must contain at least one special character ({SPECIAL_CHARS})"
    
    return True, ""


def check_password_policy(password: str):
    """
    Check password policy and raise ValidationError if invalid.
    
    Args:
        password: Password to validate
        
    Raises:
        ValidationError: If password doesn't meet policy requirements
    """
    is_valid, error_message = validate_password(password)
    if not is_valid:
        raise ValidationError(error_message)


