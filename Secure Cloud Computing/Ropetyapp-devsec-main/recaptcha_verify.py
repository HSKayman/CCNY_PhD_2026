"""Google reCAPTCHA verification."""
import requests
import logging

logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha(recaptcha_response: str, remote_ip: str = None) -> bool:
    """
    Verify Google reCAPTCHA response.
    
    Args:
        recaptcha_response: The g-recaptcha-response token from the form
        remote_ip: Optional client IP address
        
    Returns:
        True if verification succeeds, False otherwise
    """
    from secrets_manager import get_recaptcha_secret_key
    secret_key = get_recaptcha_secret_key().strip()
    
    if not secret_key or secret_key == "YOUR_RECAPTCHA_SECRET_KEY_HERE":
        logger.warning("reCAPTCHA secret key not configured - skipping verification")
        return True
    
    if not recaptcha_response or recaptcha_response.strip() == "":
        logger.warning(f"reCAPTCHA response is missing or empty. Response length: {len(recaptcha_response) if recaptcha_response else 0}")
        return False
    
    try:
        data = {
            "secret": secret_key,
            "response": recaptcha_response,
        }
        
        if remote_ip:
            data["remoteip"] = remote_ip
        
        response = requests.post(RECAPTCHA_VERIFY_URL, data=data, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success"):
            logger.debug("reCAPTCHA verification successful")
            return True
        else:
            error_codes = result.get("error-codes", [])
            logger.warning(f"reCAPTCHA verification failed: {error_codes}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"Error verifying reCAPTCHA: {e}", exc_info=True)
        # Fail open in case of network issues (you may want to fail closed)
        return False
    except Exception as e:
        logger.error(f"Unexpected error verifying reCAPTCHA: {e}", exc_info=True)
        return False

