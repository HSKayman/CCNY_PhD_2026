"""Two-Factor Authentication utilities using TOTP (Time-based One-Time Password)."""
import pyotp
import qrcode
import io
import base64
import secrets
import json
import logging
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


def generate_secret() -> str:
    """Generate a new TOTP secret."""
    return pyotp.random_base32()


def generate_qr_code(secret: str, email: str, issuer: str = "RoboPety") -> str:
    """
    Generate a QR code as base64 string for the TOTP secret.
    
    Args:
        secret: TOTP secret
        email: User's email (used as account name)
        issuer: Service name (default: RoboPety)
        
    Returns:
        Base64-encoded PNG image string
    """
    # Create TOTP URI
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=issuer
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def verify_totp(secret: str, token: str, window: int = 2) -> bool:
    """
    Verify a TOTP token.
    
    Args:
        secret: TOTP secret
        token: Token to verify (6-digit code)
        window: Time window for verification (default: 2, meaning current, previous, and next time step)
                This accounts for clock skew between server and client
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        # Clean the token - remove any spaces or non-numeric characters
        token = str(token).strip().replace(' ', '').replace('-', '')
        
        # Ensure it's exactly 6 digits
        if len(token) != 6 or not token.isdigit():
            logger.warning(f"Invalid TOTP token format: length={len(token)}, is_digit={token.isdigit()}")
            return False
        
        totp = pyotp.TOTP(secret)
        # Verify with window (allows for clock skew)
        result = totp.verify(token, valid_window=window)
        
        if not result:
            logger.debug(f"TOTP verification failed for token (first 2 chars): {token[:2]}**, window={window}")
        
        return result
    except Exception as e:
        logger.error(f"TOTP verification error: {e}", exc_info=True)
        return False


def generate_backup_codes(count: int = 10) -> List[str]:
    codes = []
    for _ in range(count):
        # Generate 8-digit code
        code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
        codes.append(code)
    return codes


def backup_codes_to_json(codes: List[str]) -> str:
    """Convert backup codes list to JSON string for storage."""
    return json.dumps(codes)


def backup_codes_from_json(json_str: str) -> List[str]:
    """Parse backup codes from JSON string."""
    try:
        return json.loads(json_str) if json_str else []
    except (json.JSONDecodeError, TypeError):
        return []


def verify_backup_code(backup_codes_json: str, code: str) -> Tuple[bool, Optional[str]]:
    if not backup_codes_json:
        return False, None
    
    codes = backup_codes_from_json(backup_codes_json)
    
    # Check if code exists
    if code not in codes:
        return False, backup_codes_json
    
    # Remove used code
    codes.remove(code)
    updated_json = backup_codes_to_json(codes)
    
    return True, updated_json

