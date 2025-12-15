"""Centralized error handling and structured logging."""
import logging
import traceback
from functools import wraps
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)


def setup_logging():
    """Setup structured logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


class AppError(Exception):
    """Base application error."""
    def __init__(self, message, status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(AppError):
    """Authentication error."""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, status_code=401, error_code="AUTH_ERROR")


class AuthorizationError(AppError):
    """Authorization error."""
    def __init__(self, message="Access denied"):
        super().__init__(message, status_code=403, error_code="AUTHZ_ERROR")


class ValidationError(AppError):
    """Validation error."""
    def __init__(self, message="Validation failed"):
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")


class NotFoundError(AppError):
    """Not found error."""
    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


def handle_error(error):
    """Handle application errors."""
    if isinstance(error, AppError):
        logger.warning(
            f"Application error: {error.message}",
            extra={
                "error_code": error.error_code,
                "status_code": error.status_code,
                "path": request.path,
                "method": request.method,
            }
        )
        return jsonify({
            "error": error.message,
            "error_code": error.error_code
        }), error.status_code
    
    if isinstance(error, IntegrityError):
        logger.error(
            f"Database integrity error: {str(error)}",
            extra={
                "path": request.path,
                "method": request.method,
            },
            exc_info=True
        )
        return jsonify({
            "error": "Database integrity constraint violated",
            "error_code": "DB_INTEGRITY_ERROR"
        }), 400
    
    if isinstance(error, SQLAlchemyError):
        logger.error(
            f"Database error: {str(error)}",
            extra={
                "path": request.path,
                "method": request.method,
            },
            exc_info=True
        )
        return jsonify({
            "error": "Database operation failed",
            "error_code": "DB_ERROR"
        }), 500
    
    # Generic error handler
    logger.error(
        f"Unhandled error: {str(error)}",
        extra={
            "path": request.path,
            "method": request.method,
        },
        exc_info=True
    )
    return jsonify({
        "error": "An unexpected error occurred",
        "error_code": "INTERNAL_ERROR"
    }), 500


def get_client_ip():
    """Get the real client IP address, handling proxies and load balancers."""
    # Check for X-Forwarded-For header (used by proxies/load balancers)
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, the first one is the original client
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return ip
    # Check for X-Real-IP header (used by some proxies)
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP').strip()
    # Fallback to remote_addr
    else:
        return request.remote_addr or 'Unknown'

def log_request(f):
    """Decorator to log requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": client_ip,
            }
        )
        return f(*args, **kwargs)
    return decorated_function


