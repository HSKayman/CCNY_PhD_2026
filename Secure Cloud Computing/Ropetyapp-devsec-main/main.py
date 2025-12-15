"""Main Flask application with security enhancements."""
import os
import tempfile
import logging
import secrets
from flask import (
    Flask,
    redirect,
    url_for,
    request,
    render_template,
    jsonify,
    send_from_directory,
    make_response,
    abort,
    session,
)
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google.cloud import storage
try:
    from google.cloud import logging as cloud_logging
    CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    CLOUD_LOGGING_AVAILABLE = False

# Local imports
from db_session import init_db, close_db
from db_service import (
    get_robots,
    get_robot_by_id,
    get_user_robot_by_user,
    get_user_robots_all,
    select_pet,
    return_pet,
    get_announcements,
    create_announcement,
    update_announcement,
    delete_announcement,
)
from auth_utils import (
    create_jwt,
    decode_jwt_from_cookie,
    hash_password,
    verify_password,
    require_auth,
    require_ownership_or_admin,
    TOKEN_COOKIE_NAME,
    TOKEN_MAX_AGE,
)
from password_policy import check_password_policy
from validation_utils import check_email, check_username, sanitize_input, check_chat_message, sanitize_chat_message
from error_handlers import (
    setup_logging,
    handle_error,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    AppError,
    log_request,
)
from secrets_manager import get_bucket_name, get_flask_secret, get_recaptcha_site_key
from models import UserRole

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Log Cloud Logging availability
if not CLOUD_LOGGING_AVAILABLE:
    logger.warning("Google Cloud Logging not available - GCP logs feature will be disabled")

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = get_flask_secret()

# Initialize database
init_db()

# Configure Content Security Policy to allow reCAPTCHA, Google Fonts, jQuery, Boxicons, and necessary resources
csp_policy = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://www.google.com https://www.gstatic.com https://ajax.googleapis.com https://unpkg.com https://cdn.jsdelivr.net",
    'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com https://cdn.jsdelivr.net",
    'font-src': "'self' https://fonts.gstatic.com https://unpkg.com https://cdn.jsdelivr.net data:",
    'frame-src': "'self' https://www.google.com",
    'img-src': "'self' data: https: blob:",
    'connect-src': "'self' https://www.google.com https://www.gstatic.com https://unpkg.com https://cdn.jsdelivr.net",
}

# Initialize Flask-Talisman for security headers
talisman = Talisman(
    app,
    force_https=True,  # Enforce HTTPS (App Engine provides HTTPS automatically)
    strict_transport_security=True,
    strict_transport_security_max_age=63072000,  # 2 years
    strict_transport_security_include_subdomains=True,
    strict_transport_security_preload=True,
    referrer_policy='strict-origin-when-cross-origin',
    feature_policy={
        'geolocation': "'none'",
        'camera': "'none'",
        'microphone': "'none'",
    },
    frame_options='DENY',
    frame_options_allow_from=None,
    content_security_policy=csp_policy
)

# Add additional security headers manually (Flask-Talisman doesn't support these as parameters)
@app.after_request
def add_security_headers(response):
    """Add additional security headers not supported by Talisman parameters."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Add Permissions-Policy header (replaces Feature-Policy)
    response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'
    # Ensure proper content type for HTML pages
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Use Redis in production
)

# Get bucket name
BUCKET_NAME = get_bucket_name()

# Register error handlers
app.register_error_handler(Exception, handle_error)


# -----------------------
# Helper functions
# -----------------------
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

def set_auth_cookie(response, user_data):
    """Set authentication cookie with JWT."""
    payload = {
        "id": user_data["id"],
        "username": user_data["username"],
        "role": user_data.get("role", "user"),
    }
    token = create_jwt(payload, expires_minutes=15)  # Short-lived token
    
    # Determine if we should use secure cookies (HTTPS)
    use_secure = os.environ.get("FLASK_ENV") != "development"
    
    response.set_cookie(
        TOKEN_COOKIE_NAME,
        token,
        httponly=True,
        secure=use_secure,
        samesite="Strict",
        max_age=TOKEN_MAX_AGE,
        path="/",
    )
    return response


def clear_auth_cookie(response):
    """Clear authentication cookie."""
    use_secure = os.environ.get("FLASK_ENV") != "development"
    response.set_cookie(
        TOKEN_COOKIE_NAME,
        "",
        httponly=True,
        secure=use_secure,
        samesite="Strict",
        expires=0,
        path="/",
    )
    return response


# -----------------------
# Routes (public pages)
# -----------------------
@app.route("/")
def root():
    """Root route redirects to login."""
    return redirect(url_for("login"))


@app.route("/robots.txt")
def robots_txt():
    """Serve robots.txt to allow search engine crawling."""
    robots_content = """User-agent: *
Allow: /
Disallow: /user/
Disallow: /userlogin
Disallow: /usersignup
Disallow: /logout
"""
    response = make_response(robots_content)
    response.headers["Content-Type"] = "text/plain"
    return response


@app.route("/favicon.ico")
def favicon():
    """Serve favicon to prevent 404 errors."""
    # Return a simple 204 No Content to prevent 404 errors
    return "", 204


@app.route("/login", methods=["GET"])
@log_request
def login():
    """Login page."""
    # If already logged in, redirect to their username
    decoded, err = decode_jwt_from_cookie()
    if decoded and "username" in decoded:
        return redirect(url_for("user", username=decoded["username"]))
    
    # Get reCAPTCHA site key using secrets manager (handles env vars and Secret Manager)
    recaptcha_site_key = get_recaptcha_site_key().strip()
    
    # Clean and validate
    if not recaptcha_site_key or recaptcha_site_key == "YOUR_RECAPTCHA_SITE_KEY_HERE":
        logger.debug("reCAPTCHA site key not configured - widget will not be displayed")
        recaptcha_site_key = ""
    else:
        logger.debug(f"reCAPTCHA site key configured: {recaptcha_site_key[:10]}...")
    
    return render_template("login.html", recaptcha_site_key=recaptcha_site_key)


@app.route("/signup", methods=["GET"])
@log_request
def signup():
    """Signup page."""
    decoded, err = decode_jwt_from_cookie()
    if decoded and "username" in decoded:
        return redirect(url_for("user", username=decoded["username"]))
    return render_template("signup.html")


# -----------------------
# Protected user page
# -----------------------
@app.route("/user/<username>", methods=["GET"])
@log_request
@require_auth
def user(username):
    """User dashboard page."""
    # Require valid token and matching username
    if request.current_username != username:
        # Forbidden if token username doesn't match the URL
        raise AuthorizationError("Access denied")
    
    # Check if user is admin - redirect to admin page
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            pass
    
    if user_role == UserRole.ADMIN:
        return redirect(url_for("admin"))
    
    if user_role == UserRole.BLUE_TEAM:
        return redirect(url_for("blue_team"))
    
    # We render the page; client JS will call API endpoints to populate lists
    return render_template("user.html", username=username)


# -----------------------
# Auth API endpoints (POST)
# -----------------------
@app.route("/userlogin", methods=["POST"])
@log_request
@limiter.limit("5 per minute")  # Rate limit login attempts
def userlogin():
    """User login endpoint."""
    email = request.form.get("email")
    password = request.form.get("password")
    recaptcha_response = request.form.get("g-recaptcha-response")
    
    # Validate and sanitize inputs
    if not email or not password:
        raise ValidationError("Email and password are required")
    
    # Sanitize email
    email = sanitize_input(email, max_length=255)
    
    # Validate email format
    check_email(email)
    
    # Validate password is not empty
    password = password.strip() if password else ""
    if not password:
        raise ValidationError("Password is required")
    if len(password) > 128:  # Reasonable max length
        raise ValidationError("Password is too long")
    
    # Verify reCAPTCHA
    from secrets_manager import get_recaptcha_secret_key
    recaptcha_secret = get_recaptcha_secret_key().strip()
    
    if recaptcha_secret and recaptcha_secret != "YOUR_RECAPTCHA_SECRET_KEY_HERE":
        from recaptcha_verify import verify_recaptcha
        # Log for debugging
        logger.debug(f"reCAPTCHA response received: {len(recaptcha_response) if recaptcha_response else 0} chars")
        client_ip = get_client_ip()
        if not verify_recaptcha(recaptcha_response or "", client_ip):
            logger.warning(f"reCAPTCHA verification failed for email: {email}")
            raise ValidationError("reCAPTCHA verification failed. Please complete the reCAPTCHA verification.")
    
    from db_service import validate_user, get_user_by_email
    
    try:
        response = validate_user(email)
        if response["status"] != "success":
            raise AuthenticationError("Invalid credentials")

        data = response["data"]
        stored_hash = data["password"]
        
        if not verify_password(password, stored_hash):
            raise AuthenticationError("Invalid credentials")
        
        # Check if 2FA is enabled
        two_factor_enabled = data.get("two_factor_enabled", False)
        
        if two_factor_enabled:
            # Store temporary login state in session for 2FA verification
            session["pending_login"] = {
                "user_id": data["id"],
                "username": data["username"],
                "email": data["email"],
                "role": data.get("role", "user"),
            }
            session.permanent = False  # Session expires when browser closes
            return jsonify({
                "status": "2fa_required",
                "message": "Please enter your 2FA code"
            })
        
        # No 2FA - proceed with normal login
        user_data = {
            "id": data["id"],
            "username": data["username"],
            "role": data.get("role", "user"),
        }
        
        # Track login activity
        try:
            from db_service import update_user_login
            client_ip = get_client_ip()
            update_user_login(user_data["id"], client_ip, request.headers.get("User-Agent", ""))
        except Exception as e:
            logger.warning(f"Failed to track login: {e}")
        
        resp = make_response(jsonify({"username": user_data["username"]}))
        set_auth_cookie(resp, user_data)
        return resp
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise AuthenticationError("Login failed")


@app.route("/verify-2fa", methods=["POST"])
@log_request
@limiter.limit("10 per minute")
def verify_2fa():
    """Verify 2FA code during login."""
    code = request.form.get("code", "").strip()
    # Remove any spaces or dashes from the code
    code = code.replace(' ', '').replace('-', '')
    
    if not code:
        raise ValidationError("2FA code is required")
    
    # Validate code format (6 digits for TOTP, 8 digits for backup)
    if len(code) not in [6, 8] or not code.isdigit():
        raise ValidationError("Invalid code format. Please enter a 6-digit TOTP code or 8-digit backup code.")
    
    # Get pending login from session
    pending_login = session.get("pending_login")
    if not pending_login:
        raise AuthenticationError("No pending login found. Please login again.")
    
    user_id = pending_login.get("user_id")
    if not user_id:
        raise AuthenticationError("Invalid session")
    
    # Verify 2FA code
    from db_service import verify_2fa_code
    if not verify_2fa_code(user_id, code):
        raise AuthenticationError("Invalid 2FA code. Please try again.")
    
    # 2FA verified - complete login
    user_data = {
        "id": pending_login["user_id"],
        "username": pending_login["username"],
        "role": pending_login.get("role", "user"),
    }
    
    # Track login activity
    try:
        from db_service import update_user_login
        client_ip = get_client_ip()
        update_user_login(user_data["id"], client_ip, request.headers.get("User-Agent", ""))
    except Exception as e:
        logger.warning(f"Failed to track login: {e}")
    
    # Clear pending login from session
    session.pop("pending_login", None)
    
    resp = make_response(jsonify({"username": user_data["username"]}))
    set_auth_cookie(resp, user_data)
    return resp


@app.route("/usersignup", methods=["POST"])
@log_request
@limiter.limit("3 per minute")  # Rate limit signup attempts
def usersignup():
    """User signup endpoint."""
    email = request.form.get("email", "")
    username = request.form.get("username", "")
    password_1 = request.form.get("password_1")
    password_2 = request.form.get("password_2")
    
    # Check all fields are provided
    if not email or not username or not password_1 or not password_2:
        raise ValidationError("Please fill in all the fields")
    
    # Sanitize inputs
    email = sanitize_input(email, max_length=255)
    username = sanitize_input(username, max_length=30)
    
    # Validate email format (strict validation)
    check_email(email)
    
    # Validate username format
    check_username(username)
    
    # Validate passwords match
    if password_1 != password_2:
        raise ValidationError("Passwords do not match")
    
    # Validate password policy
    check_password_policy(password_1)

    # Hash password
    hashed = hash_password(password_1)
    
    from db_service import add_user

    try:
        response = add_user(email, username, hashed, role=UserRole.USER)
        if response["status"] == "success":
            user = response["data"]
            resp = make_response(jsonify({"username": user["username"]}))
            set_auth_cookie(resp, user)
            return resp
        else:
            raise ValidationError(response.get("error", "Signup failed"))
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        raise ValidationError("Signup failed")


@app.route("/logout", methods=["GET", "POST"])
@log_request
@require_auth
def logout():
    """Logout endpoint."""
    # Log logout activity before clearing auth
    try:
        user_id = request.current_user_id
        from db_service import log_user_activity
        client_ip = get_client_ip()
        log_user_activity(
            user_id,
            "Logout",
            "User logged out",
            client_ip,
            request.headers.get("User-Agent", "")
        )
    except Exception as e:
        logger.warning(f"Failed to log logout activity: {e}")
    
    resp = make_response(redirect(url_for("login")))
    clear_auth_cookie(resp)
    return resp


# -----------------------
# Blue Team routes
# -----------------------
@app.route("/blue-team", methods=["GET"])
@log_request
@require_auth
def blue_team():
    """Blue Team dashboard page."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    # Only blue team and admin can access
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    username = request.current_username
    return render_template("blue_team.html", username=username)


@app.route("/blue-team/analytics", methods=["GET"])
@log_request
@require_auth
def blue_team_analytics():
    """Get analytics for blue team dashboard."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    from db_service import get_blue_team_analytics
    response = get_blue_team_analytics()
    return jsonify(response)


@app.route("/blue-team/security-events", methods=["GET"])
@log_request
@require_auth
def blue_team_security_events():
    """Get security events for blue team."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    severity = request.args.get("severity", "").strip() or None
    resolved_str = request.args.get("resolved", "").strip()
    resolved = None if resolved_str == "" else resolved_str.lower() == "true"
    event_type = request.args.get("event_type", "").strip() or None
    limit = int(request.args.get("limit", 100))
    
    from db_service import get_security_events
    response = get_security_events(limit=limit, severity=severity, resolved=resolved, event_type=event_type)
    return jsonify(response)


@app.route("/blue-team/security-events/<int:event_id>/resolve", methods=["POST"])
@log_request
@require_auth
def blue_team_resolve_event(event_id):
    """Resolve a security event."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    user_id = request.current_user_id
    from db_service import resolve_security_event
    response = resolve_security_event(event_id, user_id)
    return jsonify(response)


@app.route("/blue-team/activity-logs", methods=["GET"])
@log_request
@require_auth
def blue_team_activity_logs():
    """Get activity logs for blue team."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    activity_type = request.args.get("activity_type", "").strip() or None
    user_id = request.args.get("user_id", "").strip()
    user_id = int(user_id) if user_id.isdigit() else None
    limit = int(request.args.get("limit", 500))
    
    from db_service import get_all_activity_logs
    response = get_all_activity_logs(limit=limit, activity_type=activity_type, user_id=user_id)
    return jsonify(response)


@app.route("/blue-team/chat/messages", methods=["GET"])
@log_request
@require_auth
def blue_team_chat_messages():
    """Get chat messages for blue team (with admin)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    user_id = request.current_user_id
    from db_service import get_user_chat_messages
    response = get_user_chat_messages(user_id)
    # Limit to last 100 messages
    if response.get("status") == "success" and response.get("data"):
        response["data"] = response["data"][-100:]
    return jsonify(response)


@app.route("/blue-team/chat/send", methods=["POST"])
@log_request
@require_auth
@limiter.limit("20 per minute")
def blue_team_send_chat():
    """Send chat message from blue team to admin."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    user_id = request.current_user_id
    message = request.form.get("message", "").strip()
    
    if not message:
        raise ValidationError("Message is required")
    
    message = sanitize_chat_message(message)
    check_chat_message(message)
    
    from db_service import send_chat_message
    response = send_chat_message(user_id, message, is_from_admin=False)
    return jsonify(response)


@app.route("/blue-team/robopets-analytics", methods=["GET"])
@log_request
@require_auth
def blue_team_robopets_analytics():
    """Get RoboPets analytics for blue team."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    from db_service import get_robopets_analytics
    response = get_robopets_analytics()
    return jsonify(response)


@app.route("/blue-team/gcp-logs", methods=["GET"])
@log_request
@require_auth
def blue_team_gcp_logs():
    """Get GCP logs for blue team (real-time)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    if not CLOUD_LOGGING_AVAILABLE:
        return jsonify({
            "status": "error",
            "error": "Google Cloud Logging not available. Please install google-cloud-logging package."
        }), 503
    
    level = request.args.get("level", "").strip().upper() or None
    service = request.args.get("service", "").strip() or None
    limit = int(request.args.get("limit", 50))
    
    try:
        from db_service import get_gcp_logs
        response = get_gcp_logs(limit=limit, severity=level, service=service)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching GCP logs: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Failed to fetch GCP logs: {str(e)}"
        }), 500


@app.route("/blue-team/gcp-logs/mark-threat", methods=["POST"])
@log_request
@require_auth
def blue_team_mark_log_as_threat():
    """Mark a GCP log entry as a security threat."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.BLUE_TEAM and user_role != UserRole.ADMIN:
        raise AuthorizationError("Blue Team access required")
    
    data = request.json
    message = data.get("message", "").strip()
    level = data.get("level", "INFO").strip()
    service = data.get("service", "default").strip()
    severity = data.get("severity", "medium").strip().lower()
    
    if not message:
        raise ValidationError("Message is required")
    
    # Validate severity
    if severity not in ['low', 'medium', 'high', 'critical']:
        severity = 'medium'
    
    # Get client IP (function is defined in this file)
    ip_address = get_client_ip()
    user_agent = request.headers.get("User-Agent", "")
    user_id = request.current_user_id
    
    # Create security event
    from db_service import create_security_event
    import json
    
    event_description = f"GCP Log Threat: {message[:200]}"
    if len(message) > 200:
        event_description += "..."
    
    metadata = json.dumps({
        "source": "gcp_logs",
        "log_level": level,
        "service": service,
        "full_message": message
    })
    
    try:
        response = create_security_event(
            event_type="threat_detected",
            severity=severity,
            description=event_description,
            ip_address=ip_address,
            user_id=user_id,
            user_agent=user_agent,
            event_metadata=metadata
        )
        
        logger.info(f"Blue Team user {user_id} marked GCP log as threat: {severity} - {event_description[:50]}")
        return jsonify({
            "status": "success",
            "message": "Log entry marked as security threat",
            "data": response.get("data")
        })
    except Exception as e:
        logger.error(f"Error creating security event from GCP log: {e}", exc_info=True)
        raise AppError(f"Failed to mark log as threat: {str(e)}")


# -----------------------
# Admin routes
# -----------------------
@app.route("/admin", methods=["GET"])
@log_request
@require_auth
def admin():
    """Admin dashboard page."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    return render_template("admin.html", username=request.current_username)


@app.route("/admin/bookings", methods=["GET"])
@log_request
@require_auth
def admin_bookings():
    """Get all bookings (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import get_all_bookings
    response = get_all_bookings()
    return jsonify(response)


@app.route("/admin/users", methods=["GET"])
@log_request
@require_auth
def admin_users():
    """Get all users (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import get_all_users
    response = get_all_users()
    return jsonify(response)


@app.route("/admin/robot-count", methods=["GET"])
@log_request
@require_auth
def admin_robot_count():
    """Get total robot count (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import get_robot_count
    response = get_robot_count()
    return jsonify(response)


@app.route("/chat/send", methods=["POST"])
@log_request
@require_auth
@limiter.limit("20 per minute")  # Rate limit chat messages
def send_chat_message():
    """Send a chat message (user only)."""
    user_id = request.current_user_id
    message = request.form.get("message", "")
    
    # Validate and sanitize message
    check_chat_message(message)
    message = sanitize_chat_message(message)
    
    if not message or not message.strip():
        raise ValidationError("Message cannot be empty")
    
    from db_service import send_chat_message as db_send_chat
    response = db_send_chat(user_id, message, is_from_admin=False)
    return jsonify(response)


@app.route("/chat/messages", methods=["GET", "POST"])
@log_request
@require_auth
@limiter.limit("200 per minute")  # Higher limit for polling endpoint
def get_chat_messages():
    """Get chat messages for the current user."""
    user_id = request.current_user_id
    from db_service import get_user_chat_messages
    response = get_user_chat_messages(user_id)
    return jsonify(response)


@app.route("/admin/chat/conversations", methods=["GET"])
@log_request
@require_auth
def admin_chat_conversations():
    """Get all chat conversations (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import get_all_chat_conversations
    response = get_all_chat_conversations()
    return jsonify(response)


@app.route("/admin/chat/messages", methods=["GET"])
@log_request
@require_auth
def admin_chat_messages():
    """Get chat messages for a specific user (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    try:
        user_id = int(request.args.get("user_id"))
    except (ValueError, TypeError):
        raise ValidationError("Invalid user ID")
    
    from db_service import get_chat_messages_for_admin
    response = get_chat_messages_for_admin(user_id)
    return jsonify(response)


@app.route("/admin/chat/send", methods=["POST"])
@log_request
@require_auth
@limiter.limit("30 per minute")  # Rate limit admin chat messages
def admin_send_chat_message():
    """Send a chat message to a user (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    try:
        user_id = int(request.form.get("user_id"))
    except (ValueError, TypeError):
        raise ValidationError("Invalid user ID")
    
    message = request.form.get("message", "")
    
    # Validate and sanitize message
    check_chat_message(message)
    message = sanitize_chat_message(message)
    
    if not message or not message.strip():
        raise ValidationError("Message cannot be empty")
    
    from db_service import send_chat_message as db_send_chat
    response = db_send_chat(user_id, message, is_from_admin=True)
    return jsonify(response)


@app.route("/admin/send-alert", methods=["POST"])
@log_request
@require_auth
def admin_send_alert():
    """Send alert to user (admin only). Never sends to admin users."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    user_id = request.form.get("user_id")
    message = request.form.get("message", "Thanks for having the robopet, do give a feedback!")
    
    if not user_id:
        raise ValidationError("User ID is required")
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise ValidationError("Invalid user ID")
    
    from db_service import send_alert_to_user
    try:
        response = send_alert_to_user(user_id, message)
        return jsonify(response)
    except ValidationError as ve:
        # This will catch the "Cannot send alerts to admin users" error
        raise


@app.route("/admin/free-robot", methods=["POST"])
@log_request
@require_auth
def admin_free_robot():
    """Free a robot booking for a user (admin only). Returns the robot without deleting the user."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    user_id = request.form.get("user_id")
    robot_id = request.form.get("robot_id")
    
    if not user_id:
        raise ValidationError("User ID is required")
    if not robot_id:
        raise ValidationError("Robot ID is required")
    
    try:
        user_id = int(user_id)
        robot_id = int(robot_id)
    except (ValueError, TypeError):
        raise ValidationError("Invalid user ID or robot ID")
    
    from db_service import return_pet, get_user_by_id, get_robot_by_id
    try:
        # Verify user exists
        user_response = get_user_by_id(user_id)
        if user_response["status"] != "success":
            raise NotFoundError("User not found")
        
        username = user_response["data"]["username"]
        
        # Verify robot exists
        robot_response = get_robot_by_id(robot_id)
        if robot_response["status"] != "success":
            raise NotFoundError("Robot not found")
        
        robot_name = robot_response["data"]["name"]
        
        # Return the robot (this creates a RETURN record, freeing the robot)
        # Note: return_pet checks ownership, but since we're only showing active bookings,
        # the user should own this robot
        response = return_pet(user_id, robot_id)
        
        return jsonify({
            "status": "success",
            "message": f"Robot '{robot_name}' freed successfully for user {username}",
            "data": response.get("data")
        })
    except ValidationError as ve:
        # Provide more context for validation errors
        error_msg = str(ve)
        if "don't own" in error_msg.lower():
            raise ValidationError("This robot is not currently booked by this user. It may have already been returned.")
        raise
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error freeing robot: {e}", exc_info=True)
        raise ValidationError("Failed to free robot")


@app.route("/admin/delete-user", methods=["POST"])
@log_request
@require_auth
def admin_delete_user():
    """Delete a user and all their bookings (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    user_id = request.form.get("user_id")
    
    if not user_id:
        raise ValidationError("User ID is required")
    
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise ValidationError("Invalid user ID")
    
    # Prevent admin from deleting themselves
    if user_id == request.current_user_id:
        raise ValidationError("You cannot delete your own account")
    
    from db_service import delete_user_and_bookings
    try:
        response = delete_user_and_bookings(user_id)
        return jsonify(response)
    except (ValidationError, NotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}", exc_info=True)
        raise ValidationError("Failed to delete user")


@app.route("/admin/announcements", methods=["GET"])
@log_request
@require_auth
def admin_get_announcements():
    """Get all announcements (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    active_only = request.args.get("active_only", "false").lower() == "true"
    response = get_announcements(active_only=active_only)
    return jsonify(response)


@app.route("/admin/announcements", methods=["POST"])
@log_request
@require_auth
@limiter.limit("10 per minute")
def admin_create_announcement():
    """Create a new announcement (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    
    if not title:
        raise ValidationError("Title is required")
    if not message:
        raise ValidationError("Message is required")
    
    response = create_announcement(title, message)
    return jsonify(response)


@app.route("/admin/announcements/<int:announcement_id>", methods=["POST"])
@log_request
@require_auth
@limiter.limit("10 per minute")
def admin_update_announcement(announcement_id):
    """Update an announcement (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    title = request.form.get("title")
    message = request.form.get("message")
    is_active = request.form.get("is_active")
    
    if title is not None:
        title = title.strip()
    if message is not None:
        message = message.strip()
    
    is_active_bool = None
    if is_active is not None:
        is_active_bool = is_active.lower() in ("true", "1", "yes")
    
    response = update_announcement(announcement_id, title=title, message=message, is_active=is_active_bool)
    return jsonify(response)


@app.route("/admin/announcements/<int:announcement_id>", methods=["DELETE"])
@log_request
@require_auth
@limiter.limit("10 per minute")
def admin_delete_announcement(announcement_id):
    """Delete an announcement (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    response = delete_announcement(announcement_id)
    return jsonify(response)


@app.route("/announcements", methods=["GET"])
@log_request
@require_auth
@limiter.limit("100 per minute")  # Higher limit for polling endpoint
def get_user_announcements():
    """Get active announcements (user only)."""
    response = get_announcements(active_only=True)
    return jsonify(response)


# -----------------------
# New Features Routes
# -----------------------

# Booking History (User)
@app.route("/booking-history", methods=["GET"])
@log_request
@require_auth
def get_booking_history():
    """Get booking history for current user."""
    user_id = request.current_user_id
    limit = int(request.args.get("limit", 50))
    from db_service import get_user_booking_history
    response = get_user_booking_history(user_id, limit)
    return jsonify(response)


# Robot Management (Admin)
@app.route("/admin/robots", methods=["GET"])
@log_request
@require_auth
def admin_get_robots():
    """Get all robots (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import get_robots
    response = get_robots()
    return jsonify(response)


@app.route("/admin/robots", methods=["POST"])
@log_request
@require_auth
def admin_create_robot():
    """Create a new robot (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    name = request.form.get("name", "").strip()
    photo_url = request.form.get("photo_url", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    status = request.form.get("status", "available").strip()
    
    if not name or not photo_url:
        raise ValidationError("Name and photo_url are required")
    
    from db_service import create_robot
    from validation_utils import sanitize_input
    name = sanitize_input(name, max_length=255)
    photo_url = sanitize_input(photo_url, max_length=255)
    if description:
        description = sanitize_input(description, max_length=1000)
    if category:
        category = sanitize_input(category, max_length=100)
    
    response = create_robot(name, photo_url, description if description else None, category if category else None, status)
    return jsonify(response)


@app.route("/admin/robots/<int:robot_id>", methods=["POST"])
@log_request
@require_auth
def admin_update_robot(robot_id):
    """Update robot (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    name = request.form.get("name")
    photo_url = request.form.get("photo_url")
    description = request.form.get("description")
    category = request.form.get("category")
    status = request.form.get("status")
    is_active = request.form.get("is_active")
    
    from db_service import update_robot
    from validation_utils import sanitize_input
    
    if name is not None:
        name = sanitize_input(name.strip(), max_length=255)
    if photo_url is not None:
        photo_url = sanitize_input(photo_url.strip(), max_length=255)
    if description is not None:
        description = sanitize_input(description.strip(), max_length=1000) if description.strip() else None
    if category is not None:
        category = sanitize_input(category.strip(), max_length=100) if category.strip() else None
    
    is_active_bool = None
    if is_active is not None:
        is_active_bool = is_active.lower() in ("true", "1", "yes")
    
    response = update_robot(robot_id, name, photo_url, description, category, status, is_active_bool)
    return jsonify(response)


@app.route("/admin/robots/<int:robot_id>", methods=["DELETE"])
@log_request
@require_auth
def admin_delete_robot(robot_id):
    """Delete robot (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import delete_robot
    response = delete_robot(robot_id)
    return jsonify(response)


# Analytics (Admin)
@app.route("/admin/analytics", methods=["GET"])
@log_request
@require_auth
def admin_analytics():
    """Get booking analytics (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    from db_service import get_booking_analytics
    response = get_booking_analytics(start_date, end_date)
    return jsonify(response)


@app.route("/admin/analytics/robot/<int:robot_id>", methods=["GET"])
@log_request
@require_auth
def admin_robot_analytics(robot_id):
    """Get booking days for a specific robot (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    from db_service import get_robot_booking_days
    response = get_robot_booking_days(robot_id, start_date, end_date)
    return jsonify(response)


# Search & Filter
@app.route("/admin/search/robots", methods=["GET"])
@log_request
@require_auth
def admin_search_robots():
    """Search robots (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    query = request.args.get("q", "").strip()
    category = request.args.get("category")
    status = request.args.get("status")
    is_active = request.args.get("is_active", "true").lower() == "true"
    
    from db_service import search_robots
    response = search_robots(query if query else None, category, status, is_active)
    return jsonify(response)


@app.route("/admin/search/users", methods=["GET"])
@log_request
@require_auth
def admin_search_users():
    """Search users (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    query = request.args.get("q", "").strip()
    role = request.args.get("role")
    
    from db_service import search_users
    response = search_users(query if query else None, role)
    return jsonify(response)


@app.route("/search/robots", methods=["GET"])
@log_request
@require_auth
def search_robots_user():
    """Search robots (user)."""
    query = request.args.get("q", "").strip()
    category = request.args.get("category")
    from db_service import search_robots
    response = search_robots(query if query else None, category, "available", True)
    return jsonify(response)


# Activity Tracking (Admin)
@app.route("/admin/activity", methods=["GET"])
@log_request
@require_auth
def admin_activity_logs():
    """Get activity logs (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    limit = int(request.args.get("limit", 500))
    activity_type = request.args.get("activity_type")
    from db_service import get_all_activity_logs
    response = get_all_activity_logs(limit, activity_type)
    return jsonify(response)


# Bulk Operations (Admin)
@app.route("/admin/users/bulk-delete", methods=["POST"])
@log_request
@require_auth
def admin_bulk_delete_users():
    """Bulk delete users (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    try:
        user_ids = [int(id) for id in request.form.getlist("user_ids")]
    except (ValueError, TypeError):
        raise ValidationError("Invalid user IDs")
    
    # Prevent admin from deleting themselves
    if request.current_user_id in user_ids:
        raise ValidationError("You cannot delete your own account")
    
    from db_service import bulk_delete_users
    response = bulk_delete_users(user_ids)
    return jsonify(response)


@app.route("/admin/users/create-admin", methods=["POST"])
@log_request
@require_auth
def admin_create_admin_user():
    """Create a new admin user (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    email = request.form.get("email", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    # Validate inputs
    if not email or not username or not password:
        raise ValidationError("All fields are required")
    
    # Sanitize inputs
    email = sanitize_input(email, max_length=255)
    username = sanitize_input(username, max_length=30)
    
    # Validate email format
    check_email(email)
    
    # Validate username format
    check_username(username)
    
    # Validate password policy
    check_password_policy(password)
    
    # Hash password
    password_hash = hash_password(password)
    
    # Create admin user
    from db_service import add_user
    try:
        response = add_user(email, username, password_hash, role=UserRole.ADMIN)
        if response["status"] == "success":
            logger.info(f"Admin user created: {username} ({email})")
            return jsonify({
                "status": "success",
                "message": f"Admin user '{username}' created successfully",
                "data": response["data"]
            })
        else:
            raise ValidationError(response.get("error", "Failed to create admin user"))
    except Exception as e:
        logger.error(f"Error creating admin user: {e}", exc_info=True)
        raise AppError("Failed to create admin user")


@app.route("/admin/security-threats", methods=["GET"])
@log_request
@require_auth
def admin_get_security_threats():
    """Get high and critical security threats from Blue Team (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    severity = request.args.get("severity", "").strip().lower() or None
    resolved = request.args.get("resolved", "").strip().lower()
    
    resolved_filter = None
    if resolved == "true":
        resolved_filter = True
    elif resolved == "false":
        resolved_filter = False
    
    from db_service import get_admin_security_threats
    response = get_admin_security_threats(severity=severity, resolved=resolved_filter)
    return jsonify(response)


@app.route("/admin/security-threats/<int:event_id>/respond", methods=["POST"])
@log_request
@require_auth
def admin_respond_to_threat(event_id):
    """Admin responds to a security threat."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    data = request.json
    admin_response = data.get("response", "").strip()
    mark_resolved = data.get("mark_resolved", False)
    admin_id = request.current_user_id
    
    if not admin_response:
        raise ValidationError("Response is required")
    
    from db_service import respond_to_security_threat
    response = respond_to_security_threat(event_id, admin_response, admin_id, mark_resolved=mark_resolved)
    
    logger.info(f"Admin {admin_id} responded to security threat {event_id}")
    return jsonify(response)


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@log_request
@require_auth
def admin_update_user_role(user_id):
    """Update user role (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    new_role_str = request.json.get("role", "").strip().lower()
    
    # Validate role
    try:
        new_role = UserRole(new_role_str)
    except ValueError:
        raise ValidationError(f"Invalid role: {new_role_str}. Must be one of: user, admin, blue_team")
    
    # Don't allow changing admin role
    from db_service import get_user_by_id
    user = get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    
    if user.get("role") == "admin" and new_role != UserRole.ADMIN:
        raise ValidationError("Cannot change admin role")
    
    # Update role
    from db_service import update_user_role
    try:
        response = update_user_role(user_id, new_role)
        if response["status"] == "success":
            role_name = "Blue Team" if new_role == UserRole.BLUE_TEAM else new_role.value.title()
            logger.info(f"User {user_id} role updated to {new_role.value}")
            return jsonify({
                "status": "success",
                "message": f"User role updated to {role_name}",
                "data": response["data"]
            })
        else:
            raise ValidationError(response.get("error", "Failed to update user role"))
    except Exception as e:
        logger.error(f"Error updating user role: {e}", exc_info=True)
        raise AppError("Failed to update user role")


@app.route("/admin/alerts", methods=["GET"])
@log_request
@require_auth
def admin_get_alerts():
    """Get all alerts (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)
    
    from db_service import get_all_alerts
    response = get_all_alerts(limit=limit, offset=offset)
    return jsonify(response)


@app.route("/admin/alerts/<int:alert_id>", methods=["DELETE"])
@log_request
@require_auth
def admin_delete_alert(alert_id):
    """Delete an alert (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import delete_alert
    response = delete_alert(alert_id)
    return jsonify(response)


@app.route("/admin/alerts/delete-old", methods=["POST"])
@log_request
@require_auth
def admin_delete_old_alerts():
    """Delete old alerts (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    days_old = request.form.get("days_old", 30, type=int)
    if days_old < 1:
        raise ValidationError("Days must be at least 1")
    
    from db_service import delete_old_alerts
    response = delete_old_alerts(days_old=days_old)
    return jsonify(response)


# Export (Admin)
@app.route("/admin/export/bookings", methods=["GET"])
@log_request
@require_auth
def admin_export_bookings():
    """Export bookings as CSV (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        from db_service import export_bookings_csv
        response = export_bookings_csv(start_date, end_date)
        
        if response.get("status") != "success":
            raise ValidationError(response.get("error", "Failed to export bookings"))
        
        from flask import make_response
        resp = make_response(response["data"])
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = "attachment; filename=bookings_export.csv"
        return resp
    except Exception as e:
        logger.error(f"Error in admin_export_bookings: {e}", exc_info=True)
        from error_handlers import AppError
        raise AppError(f"Failed to export bookings: {str(e)}")


# Update login tracking
@app.route("/track-login", methods=["POST"])
@log_request
@require_auth
def track_login():
    """Track user login (called after login)."""
    user_id = request.current_user_id
    client_ip = get_client_ip()
    user_agent = request.headers.get("User-Agent", "")
    from db_service import update_user_login
    response = update_user_login(user_id, client_ip, user_agent)
    return jsonify(response)


# -----------------------
# API endpoints that read token from cookie
# -----------------------
@app.route("/getusername", methods=["POST"])
@log_request
@require_auth
def getUsername():
    """Get current username."""
    return jsonify({"username": request.current_username})


@app.route("/getallrobots", methods=["POST"])
@log_request
@require_auth
def getAllRobot():
    """Get all robots available to the user."""
    user_id = request.current_user_id
    
    # Get all user's robots
    user_robots_resp = get_user_robots_all(user_id)
    user_robots = user_robots_resp.get("data", []) if user_robots_resp["status"] == "success" else []
    user_robot_ids = [r["robot_id"] for r in user_robots]

    robots_data = get_robots()
    if robots_data["status"] != "success":
        raise NotFoundError(robots_data.get("error", "No robots available"))
    
    # Get which robots are currently booked by anyone (latest action must be PICK)
    from db_service import get_all_bookings
    bookings_response = get_all_bookings()
    booked_robot_ids = set()
    if bookings_response.get("status") == "success":
        for booking in bookings_response.get("data", []):
            booked_robot_ids.add(booking["robot_id"])
    
    # Filter out all user's robots so front-end shows only available ones
    all_robots = []
    for r in robots_data["data"]:
        if r["id"] not in user_robot_ids:
            robot_info = {
                "robot_id": r["id"],
                "name": r["name"],
                "is_booked": r["id"] in booked_robot_ids  # Add booking status
            }
            all_robots.append(robot_info)
    
    # For backward compatibility, include single user_robot
    user_robot = user_robots[0] if user_robots else {"robot_id": -1, "robot_name": "None"}

    return jsonify({"all_robots": all_robots, "user_robot": user_robot})


@app.route("/getuserrobot", methods=["POST"])
@log_request
@require_auth
def getUserRobot():
    """Get user's current robot (single, for backward compatibility)."""
    user_id = request.current_user_id
    user_robot_resp = get_user_robot_by_user(user_id)
    
    if user_robot_resp["status"] == "success" and user_robot_resp["data"].get("action") == "pick":
        robot_id = user_robot_resp["data"]["robot_id"]
        robot_resp = get_robot_by_id(robot_id)
        robot_name = robot_resp["data"]["name"] if robot_resp["status"] == "success" else "Unknown"
        return jsonify({"robot": {"robot_id": robot_id, "robot_name": robot_name}})
    else:
        return jsonify({"robot": {"robot_id": -1, "robot_name": "None"}})


@app.route("/getuserrobots", methods=["POST"])
@log_request
@require_auth
def getUserRobots():
    """Get all robots currently selected by the user."""
    user_id = request.current_user_id
    user_robots_resp = get_user_robots_all(user_id)
    return jsonify(user_robots_resp)


@app.route("/getalerts", methods=["POST"])
@log_request
@require_auth
@limiter.limit("200 per minute")  # Higher limit for polling endpoint
def get_alerts():
    """Get all alerts for the current user."""
    user_id = request.current_user_id
    from db_service import get_user_alerts
    response = get_user_alerts(user_id)
    return jsonify(response)


@app.route("/markalertread", methods=["POST"])
@log_request
@require_auth
def mark_alert_read():
    """Mark an alert as read."""
    user_id = request.current_user_id
    
    try:
        alert_id = int(request.form.get("alert_id"))
    except (ValueError, TypeError):
        raise ValidationError("Invalid alert id")
    
    from db_service import mark_alert_read
    response = mark_alert_read(alert_id, user_id)
    return jsonify(response)


@app.route("/setuserrobot", methods=["POST"])
@log_request
@require_auth
def setUserRobot():
    """Select a robot for the user."""
    from auth_utils import UserRole
    user_id = request.current_user_id
    user_role = request.current_user_role
    
    # Check if user is admin - prevent admins from booking robots
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            pass
    
    if user_role == UserRole.ADMIN:
        raise ValidationError("Admin users cannot book robots")
    
    try:
        robot_id = int(request.form.get("robot_id"))
    except (ValueError, TypeError):
        raise ValidationError("Invalid robot id")

    # Use transactional select_pet which includes strict ownership checks
    try:
        response = select_pet(user_id, robot_id)
        if response["status"] == "success":
            # Log booking activity with IP and user agent
            try:
                from db_service import log_user_activity, get_robot_by_id
                robot_response = get_robot_by_id(robot_id)
                if robot_response["status"] == "success":
                    robot_name = robot_response["data"]["name"]
                    client_ip = get_client_ip()
                    log_user_activity(
                        user_id,
                        "Booking",
                        f"Booked robot: {robot_name}",
                        client_ip,
                        request.headers.get("User-Agent", "")
                    )
            except Exception as e:
                logger.warning(f"Failed to log booking activity: {e}")
            
            return jsonify({"status": "success"})
        else:
            raise ValidationError(response.get("error", "Failed to select pet"))
    except (ValidationError, NotFoundError):
        raise
    except Exception as e:
        logger.error(f"Error selecting pet: {e}", exc_info=True)
        raise ValidationError("Failed to select pet")


@app.route("/returnuserrobot", methods=["POST"])
@log_request
@require_auth
def returnUserRobots():
    """Return a robot (strict ownership check enforced in return_pet)."""
    user_id = request.current_user_id
    
    try:
        robot_id = int(request.form.get("robot_id"))
    except (ValueError, TypeError):
        raise ValidationError("Invalid robot id")
    
    # Use transactional return_pet which includes strict ownership checks
    try:
        response = return_pet(user_id, robot_id)
        if response["status"] == "success":
            # Log return activity with IP and user agent
            try:
                from db_service import log_user_activity, get_robot_by_id
                robot_response = get_robot_by_id(robot_id)
                if robot_response["status"] == "success":
                    robot_name = robot_response["data"]["name"]
                    client_ip = get_client_ip()
                    log_user_activity(
                        user_id,
                        "Return",
                        f"Returned robot: {robot_name}",
                        client_ip,
                        request.headers.get("User-Agent", "")
                    )
            except Exception as e:
                logger.warning(f"Failed to log return activity: {e}")
            
            return jsonify({"status": "success", "message": "Robot returned successfully"})
        else:
            raise ValidationError(response.get("error", "Failed to return pet"))
    except ValidationError as ve:
        raise  # Re-raise validation errors
    except NotFoundError:
        raise
    except AuthorizationError:
        raise
    except Exception as e:
        logger.error(f"Error returning pet: {e}", exc_info=True)
        raise ValidationError("Failed to return pet")


# -----------------------
# Helper for images
# -----------------------
@app.route("/user/statistics", methods=["GET", "POST"])
@log_request
@require_auth
def get_user_statistics():
    """Get user statistics."""
    user_id = request.current_user_id
    from db_service import get_user_statistics
    response = get_user_statistics(user_id)
    return jsonify(response)


@app.route("/user/activity", methods=["GET", "POST"])
@log_request
@require_auth
def get_user_activity():
    """Get user activity log."""
    user_id = request.current_user_id
    limit = request.args.get("limit", 20, type=int)
    from db_service import get_user_activity_log
    response = get_user_activity_log(user_id, limit=limit)
    return jsonify(response)


@app.route("/getRobotImage/<name>")
@log_request
@limiter.exempt  # Exempt from rate limiting - images are needed for page display
def getRobotImage(name):
    """Get robot image from Google Cloud Storage."""
    if not BUCKET_NAME:
        abort(404)
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # Try exact name first, then lowercase version (case-insensitive lookup)
        blob = bucket.blob(name)
        if not blob.exists():
            # Try lowercase version
            blob = bucket.blob(name.lower())
            if not blob.exists():
                # Try with .png extension if not present
                if not name.lower().endswith('.png'):
                    blob = bucket.blob(f"{name.lower()}.png")
                    if not blob.exists():
                        abort(404)
                else:
                    abort(404)
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            filename = blob.name.split('/')[-1]  # Get just the filename
            fullpath = f"{tmpdirname}/{filename}"
            blob.download_to_filename(fullpath)
            return send_from_directory(tmpdirname, filename)
    except Exception as e:
        logger.error(f"Error fetching image {name}: {e}", exc_info=True)
        abort(404)


# -----------------------
# 2FA Management Endpoints
# -----------------------
@app.route("/api/2fa/status", methods=["GET"])
@log_request
@require_auth
def get_2fa_status():
    """Get user's 2FA status."""
    user_id = request.current_user_id
    from db_service import get_user_2fa_status
    response = get_user_2fa_status(user_id)
    return jsonify(response)


@app.route("/api/2fa/generate", methods=["POST"])
@log_request
@require_auth
def generate_2fa_secret():
    """Generate a new 2FA secret and QR code."""
    user_id = request.current_user_id
    from db_service import generate_2fa_secret
    response = generate_2fa_secret(user_id)
    return jsonify(response)


@app.route("/api/2fa/enable", methods=["POST"])
@log_request
@require_auth
def enable_2fa():
    """Enable 2FA for a user."""
    user_id = request.current_user_id
    secret = request.form.get("secret", "").strip()
    verification_code = request.form.get("verification_code", "").strip()
    
    if not secret or not verification_code:
        raise ValidationError("Secret and verification code are required")
    
    from db_service import enable_2fa
    response = enable_2fa(user_id, secret, verification_code)
    return jsonify(response)


@app.route("/api/2fa/disable", methods=["POST"])
@log_request
@require_auth
def disable_2fa():
    """Disable 2FA for a user."""
    user_id = request.current_user_id
    password = request.form.get("password", "").strip()
    
    if not password:
        raise ValidationError("Password is required to disable 2FA")
    
    from db_service import disable_2fa
    response = disable_2fa(user_id, password)
    return jsonify(response)


@app.route("/api/2fa/backup-codes", methods=["GET"])
@log_request
@require_auth
def get_backup_codes():
    """Get user's backup codes (admin only or for download)."""
    user_id = request.current_user_id
    from db_service import get_user_2fa_status, get_user_backup_codes
    
    # Check if 2FA is enabled
    status = get_user_2fa_status(user_id)
    if not status.get("data", {}).get("two_factor_enabled"):
        raise ValidationError("2FA is not enabled")
    
    # Get backup codes
    response = get_user_backup_codes(user_id)
    return jsonify(response)


@app.route("/api/change-password", methods=["POST"])
@log_request
@require_auth
def change_password():
    """Change user password (for both users and admins)."""
    user_id = request.current_user_id
    old_password = request.form.get("old_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    
    if not old_password or not new_password:
        raise ValidationError("Both old and new passwords are required")
    
    from db_service import change_user_password
    response = change_user_password(user_id, old_password, new_password)
    return jsonify(response)


# -----------------------
# Admin 2FA Management Endpoints
# -----------------------
@app.route("/admin/2fa/users", methods=["GET"])
@log_request
@require_auth
def admin_get_2fa_users():
    """Get all users with 2FA enabled (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import get_users_with_2fa
    response = get_users_with_2fa()
    return jsonify(response)


@app.route("/admin/2fa/disable/<int:user_id>", methods=["POST"])
@log_request
@require_auth
def admin_disable_user_2fa(user_id):
    """Disable 2FA for a user (admin only)."""
    from auth_utils import UserRole
    user_role = request.current_user_role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            raise AuthorizationError("Invalid user role")
    
    if user_role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    
    from db_service import admin_disable_user_2fa
    response = admin_disable_user_2fa(user_id)
    return jsonify(response)


# -----------------------
# Cleanup on app shutdown
# -----------------------
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close database session on app shutdown."""
    close_db()


# -----------------------
# Run locally only
# -----------------------
if __name__ == "__main__":
    # For local dev you may want debug=True and secure cookie disabled
    app.run(host="127.0.0.1", port=8080, debug=False)
