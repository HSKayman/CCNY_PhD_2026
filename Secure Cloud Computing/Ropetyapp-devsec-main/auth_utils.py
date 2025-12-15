"""Authentication and authorization utilities."""
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from secrets_manager import get_jwt_secret
from error_handlers import AuthenticationError, AuthorizationError
from models import UserRole
import logging

logger = logging.getLogger(__name__)

# Cookie settings
TOKEN_COOKIE_NAME = "token"
TOKEN_MAX_AGE = 60 * 15  # 15 minutes (short-lived)


def create_jwt(payload, expires_minutes=15):
    """
    Create a JWT token.
    
    Args:
        payload: Dictionary to encode in JWT
        expires_minutes: Token expiration time in minutes (default 15)
        
    Returns:
        Encoded JWT token string
    """
    payload = dict(payload)
    exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload["exp"] = exp
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
    # PyJWT may return bytes in some versions — ensure string
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_jwt(token):
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        decoded = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def decode_jwt_from_cookie():
    """
    Decode JWT from cookie.
    
    Returns:
        Tuple of (decoded_payload, error_message)
    """
    token = request.cookies.get(TOKEN_COOKIE_NAME)
    if not token:
        return None, "no token"
    try:
        decoded = decode_jwt(token)
        return decoded, None
    except AuthenticationError as e:
        return None, str(e)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    return hashed


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        decoded, err = decode_jwt_from_cookie()
        if not decoded:
            raise AuthenticationError("Authentication required")
        # Attach user info to request context
        request.current_user_id = decoded.get("id")
        request.current_username = decoded.get("username")
        request.current_user_role = decoded.get("role", "user")
        return f(*args, **kwargs)
    return decorated_function


def require_role(required_role: UserRole):
    """Decorator to require specific role."""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_role = request.current_user_role
            if isinstance(user_role, str):
                try:
                    user_role = UserRole(user_role)
                except ValueError:
                    raise AuthorizationError("Invalid user role")
            
            # Admins can access everything
            if user_role == UserRole.ADMIN:
                return f(*args, **kwargs)
            
            # Check if user has required role
            if user_role != required_role:
                raise AuthorizationError("Insufficient permissions")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_ownership_or_admin(owner_id_getter):
    """
    Decorator to require ownership or admin role.
    
    Args:
        owner_id_getter: Function that takes (request, *args, **kwargs) and returns owner_id
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_id = request.current_user_id
            user_role = request.current_user_role
            
            # Admins can access everything
            if isinstance(user_role, str):
                user_role = UserRole(user_role)
            if user_role == UserRole.ADMIN:
                return f(*args, **kwargs)
            
            # Check ownership
            owner_id = owner_id_getter(request, *args, **kwargs)
            if owner_id != user_id:
                raise AuthorizationError("Access denied: resource does not belong to you")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

