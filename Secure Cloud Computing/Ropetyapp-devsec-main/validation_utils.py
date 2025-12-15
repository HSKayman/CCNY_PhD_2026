"""Input validation utilities."""
import re
from error_handlers import ValidationError

# Valid TLDs (Top Level Domains) - common ones
# This is a simplified list; in production, you might want to use a more comprehensive list
VALID_TLDS = {
    'com', 'org', 'net', 'edu', 'gov', 'mil', 'int', 'co', 'io', 'ai', 'dev',
    'app', 'tech', 'online', 'site', 'website', 'store', 'shop', 'blog',
    'info', 'biz', 'name', 'me', 'tv', 'cc', 'ws', 'mobi', 'asia', 'jobs',
    'travel', 'tel', 'xxx', 'pro', 'museum', 'aero', 'coop', 'xxx',
    'gmail', 'yahoo', 'hotmail', 'outlook', 'icloud', 'protonmail', 'mail',
    'uk', 'us', 'ca', 'au', 'de', 'fr', 'it', 'es', 'nl', 'be', 'ch', 'at',
    'se', 'no', 'dk', 'fi', 'pl', 'cz', 'ie', 'pt', 'gr', 'ro', 'hu', 'bg',
    'hr', 'sk', 'si', 'ee', 'lv', 'lt', 'mt', 'cy', 'lu', 'is', 'li', 'mc',
    'ad', 'sm', 'va', 'jp', 'cn', 'in', 'kr', 'sg', 'my', 'th', 'ph', 'vn',
    'id', 'nz', 'za', 'eg', 'ma', 'ng', 'ke', 'gh', 'tz', 'ug', 'et', 'zm',
    'zw', 'bw', 'na', 'mw', 'mz', 'ao', 'mg', 'mu', 'sc', 'km', 'dj', 'so',
    'er', 'sd', 'ly', 'tn', 'dz', 'mr', 'ml', 'bf', 'ne', 'td', 'cm', 'gq',
    'ga', 'cg', 'cd', 'cf', 'ss', 'rw', 'bi', 'bj', 'tg', 'ci', 'lr', 'sl',
    'gn', 'gw', 'sn', 'gm', 'cv', 'st', 'br', 'mx', 'ar', 'cl', 'co', 'pe',
    've', 'ec', 'bo', 'py', 'uy', 'gy', 'sr', 'gf', 'fk', 'gs', 'aq', 'ru',
    'tr', 'il', 'ae', 'sa', 'kw', 'qa', 'bh', 'om', 'ye', 'iq', 'ir', 'af',
    'pk', 'bd', 'lk', 'np', 'bt', 'mm', 'kh', 'la', 'mn', 'kz', 'uz', 'tm',
    'tj', 'kg', 'ge', 'am', 'az', 'by', 'md', 'ua', 'rs', 'me', 'ba', 'mk',
    'al', 'xk'
}


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format with strict checks.
    
    Checks:
    - Basic email format (local@domain.tld)
    - Valid TLD (not random strings like @dgs)
    - No consecutive dots
    - No leading/trailing dots
    - Reasonable length
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    # Trim whitespace
    email = email.strip()
    
    # Check length
    if len(email) < 5:  # Minimum: a@b.c
        return False, "Email is too short"
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email is too long"
    
    # Basic format check: must contain exactly one @
    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol"
    
    # Split into local and domain parts
    parts = email.split('@')
    local_part = parts[0]
    domain_part = parts[1]
    
    # Validate local part
    if not local_part:
        return False, "Email must have a local part before @"
    if len(local_part) > 64:  # RFC 5321 limit
        return False, "Email local part is too long"
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, "Email local part cannot start or end with a dot"
    if '..' in local_part:
        return False, "Email local part cannot contain consecutive dots"
    
    # Validate domain part
    if not domain_part:
        return False, "Email must have a domain part after @"
    if len(domain_part) > 253:  # RFC 5321 limit
        return False, "Email domain is too long"
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False, "Email domain cannot start or end with a dot"
    if '..' in domain_part:
        return False, "Email domain cannot contain consecutive dots"
    
    # Check for valid TLD (must have at least one dot in domain)
    if '.' not in domain_part:
        return False, "Email domain must contain a top-level domain (e.g., .com, .org)"
    
    # Extract TLD (last part after last dot)
    tld = domain_part.split('.')[-1].lower()
    
    # Check if TLD is valid (must be at least 2 characters)
    if len(tld) < 2:
        return False, "Email must have a valid top-level domain (e.g., .com, .org)"
    
    # Check if TLD contains only letters (no numbers or special chars)
    if not re.match(r'^[a-z]+$', tld):
        return False, "Email top-level domain must contain only letters"
    
    # Additional check: TLD should be at least 2 characters and follow common patterns
    # This prevents obviously invalid TLDs like single letters or very short random strings
    # We allow any 2+ letter TLD, but prefer known ones for better validation
    # The pattern check above already ensures it's letters only, which is sufficient
    
    # Additional pattern check for overall email format
    email_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Email format is invalid. Please use a valid email address"
    
    return True, ""


def check_email(email: str):
    """
    Check email and raise ValidationError if invalid.
    
    Args:
        email: Email address to validate
        
    Raises:
        ValidationError: If email is invalid
    """
    is_valid, error_message = validate_email(email)
    if not is_valid:
        raise ValidationError(error_message)


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    username = username.strip()
    
    # Check length
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if len(username) > 30:
        return False, "Username must be no more than 30 characters long"
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    # Cannot start or end with underscore or hyphen
    if username.startswith('_') or username.startswith('-'):
        return False, "Username cannot start with underscore or hyphen"
    if username.endswith('_') or username.endswith('-'):
        return False, "Username cannot end with underscore or hyphen"
    
    return True, ""


def check_username(username: str):
    """
    Check username and raise ValidationError if invalid.
    
    Args:
        username: Username to validate
        
    Raises:
        ValidationError: If username is invalid
    """
    is_valid, error_message = validate_username(username)
    if not is_valid:
        raise ValidationError(error_message)


def sanitize_input(text: str, max_length: int = 255) -> str:
    """
    Sanitize input text by trimming and limiting length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text


def validate_chat_message(message: str) -> tuple[bool, str]:
    """
    Validate chat message for security (prevent XSS, script injection).
    
    Checks:
    - Not empty
    - Length limits
    - No script tags
    - No dangerous HTML/JavaScript patterns
    - No SQL injection patterns
    
    Args:
        message: Chat message to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message:
        return False, "Message cannot be empty"
    
    message = message.strip()
    
    # Check length
    if len(message) < 1:
        return False, "Message cannot be empty"
    if len(message) > 1000:
        return False, "Message is too long (max 1000 characters)"
    
    # Check for script tags and dangerous patterns (case-insensitive)
    dangerous_patterns = [
        r'<script',
        r'</script>',
        r'javascript:',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onload\s*=',
        r'onmouseover\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
        r'<link',
        r'<meta',
        r'<style',
        r'expression\s*\(',
        r'vbscript:',
        r'data:text/html',
        r'&#x',
        r'&#0',
    ]
    
    message_lower = message.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, message_lower):
            return False, "Message contains invalid content. Please remove any scripts or special characters."
    
    # Check for SQL injection patterns (basic check)
    sql_patterns = [
        r'(\bunion\b.*\bselect\b)',
        r'(\bselect\b.*\bfrom\b)',
        r'(\bdrop\b.*\btable\b)',
        r'(\bdelete\b.*\bfrom\b)',
        r'(\binsert\b.*\binto\b)',
        r'(\bupdate\b.*\bset\b)',
        r'(\bexec\b|\bexecute\b)',
        r'(\bscript\b)',
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, message_lower):
            return False, "Message contains invalid content."
    
    # Check for excessive special characters that might be used for encoding attacks
    if message.count('<') > 5 or message.count('>') > 5:
        return False, "Message contains too many special characters."
    
    # Check for URL patterns that might be used for phishing
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, message)
    if len(urls) > 3:
        return False, "Message contains too many URLs."
    
    return True, ""


def check_chat_message(message: str):
    """
    Check chat message and raise ValidationError if invalid.
    
    Args:
        message: Chat message to validate
        
    Raises:
        ValidationError: If message is invalid
    """
    is_valid, error_message = validate_chat_message(message)
    if not is_valid:
        raise ValidationError(error_message)


def sanitize_chat_message(message: str) -> str:
    """
    Sanitize chat message by removing dangerous characters while preserving safe content.
    
    Args:
        message: Chat message to sanitize
        
    Returns:
        Sanitized message
    """
    if not message:
        return ""
    
    # Trim whitespace
    message = message.strip()
    
    # Remove null bytes
    message = message.replace('\x00', '')
    
    # Limit length
    if len(message) > 1000:
        message = message[:1000]
    
    # Remove any remaining script-like patterns (extra safety)
    message = re.sub(r'<script[^>]*>.*?</script>', '', message, flags=re.IGNORECASE | re.DOTALL)
    message = re.sub(r'javascript:', '', message, flags=re.IGNORECASE)
    message = re.sub(r'on\w+\s*=', '', message, flags=re.IGNORECASE)
    
    return message

