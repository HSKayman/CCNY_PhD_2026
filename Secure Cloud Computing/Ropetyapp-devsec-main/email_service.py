"""Email service for sending notifications."""
import os
import logging
import smtplib
from smtplib import SMTPConnectError, SMTPAuthenticationError, SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from secrets_manager import get_secret

logger = logging.getLogger(__name__)


def get_smtp_config():
    """Get SMTP configuration from secrets or environment variables."""
    # Priority: Secret Manager > Environment Variables > Defaults
    smtp_host = get_secret("SMTP_HOST") or os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port_str = get_secret("SMTP_PORT") or os.environ.get("SMTP_PORT", "587")
    
    # Validate and convert port
    try:
        smtp_port = int(smtp_port_str.strip()) if smtp_port_str else 587
        # Validate port range (common SMTP ports)
        if smtp_port not in [25, 465, 587, 2525]:
            logger.warning(f"Unusual SMTP port {smtp_port} - using default 587")
            smtp_port = 587
    except (ValueError, AttributeError):
        logger.warning(f"Invalid SMTP_PORT value '{smtp_port_str}', using default 587")
        smtp_port = 587
    
    # For SMTP credentials, ALWAYS prioritize environment variables (from app.yaml) over Secret Manager
    # This prevents issues where Secret Manager might have placeholder/comment values
    # Environment variables are set in app.yaml and are the source of truth
    
    # Get values from both sources
    smtp_user_env = os.environ.get("SMTP_USER", "").strip()
    smtp_password_env = os.environ.get("SMTP_PASSWORD", "").strip()
    
    # Only check Secret Manager if environment variables are not set
    if not smtp_user_env or not smtp_password_env:
        smtp_user_secret = get_secret("SMTP_USER", default="").strip()
        smtp_password_secret = get_secret("SMTP_PASSWORD", default="").strip()
        
        # Validate Secret Manager values - reject if they look like comments/placeholders
        if smtp_user_secret and (smtp_user_secret.startswith("#") or "Stored in Google Secret Manager" in smtp_user_secret or "@" not in smtp_user_secret):
            logger.warning(f"SMTP_USER from Secret Manager is invalid (comment/placeholder), ignoring: '{smtp_user_secret[:50]}...'")
            smtp_user_secret = ""
        
        if smtp_password_secret and (smtp_password_secret.startswith("#") or "Stored in Google Secret Manager" in smtp_password_secret or len(smtp_password_secret) < 8):
            logger.warning(f"SMTP_PASSWORD from Secret Manager is invalid (comment/placeholder), ignoring")
            smtp_password_secret = ""
    else:
        smtp_user_secret = ""
        smtp_password_secret = ""
    
    # Use environment variable first, then validated Secret Manager value
    smtp_user = smtp_user_env or smtp_user_secret
    smtp_password = smtp_password_env or smtp_password_secret
    
    # Log which source we're using and validate final values
    if smtp_user_env:
        logger.info(f"✓ Using SMTP_USER from environment variable: {smtp_user}")
    elif smtp_user_secret:
        logger.info(f"✓ Using SMTP_USER from Secret Manager: {smtp_user}")
    else:
        logger.error("✗ SMTP_USER not found in environment variables or Secret Manager")
    
    if smtp_password_env:
        logger.info(f"✓ Using SMTP_PASSWORD from environment variable (length: {len(smtp_password)})")
    elif smtp_password_secret:
        logger.info(f"✓ Using SMTP_PASSWORD from Secret Manager (length: {len(smtp_password)})")
    else:
        logger.error("✗ SMTP_PASSWORD not found in environment variables or Secret Manager")
    
    # Final validation - reject if it looks like a placeholder
    if smtp_user and ("Stored in Google Secret Manager" in smtp_user or smtp_user.startswith("#")):
        logger.error(f"✗ SMTP_USER appears to be a placeholder: '{smtp_user}' - rejecting")
        smtp_user = ""
    
    if smtp_password and ("Stored in Google Secret Manager" in smtp_password or smtp_password.startswith("#")):
        logger.error(f"✗ SMTP_PASSWORD appears to be a placeholder - rejecting")
        smtp_password = ""
    
    # Remove spaces from App Password (Gmail App Passwords are displayed with spaces but should be used without)
    if smtp_password:
        smtp_password = smtp_password.replace(" ", "").strip()
    
    # Get EMAIL_FROM with same priority logic - environment variable first
    email_from_env = os.environ.get("EMAIL_FROM", "").strip()
    if email_from_env:
        email_from = email_from_env
    else:
        # Only check Secret Manager if env var is missing
        email_from_secret = get_secret("EMAIL_FROM", default="").strip()
        if email_from_secret and not email_from_secret.startswith("#") and "@" in email_from_secret and "Stored in Google Secret Manager" not in email_from_secret:
            email_from = email_from_secret
        else:
            email_from = smtp_user  # Fallback to smtp_user
    
    # Final validation - reject placeholder values even if they passed earlier checks
    if smtp_user and ("Stored in Google Secret Manager" in smtp_user or smtp_user.strip().startswith("#")):
        logger.error(f"✗ REJECTING SMTP_USER - appears to be placeholder: '{smtp_user[:50]}...'")
        smtp_user = ""
    
    if smtp_password and ("Stored in Google Secret Manager" in smtp_password or smtp_password.strip().startswith("#")):
        logger.error(f"✗ REJECTING SMTP_PASSWORD - appears to be placeholder")
        smtp_password = ""
    
    # Log configuration status (without sensitive data)
    if smtp_user and smtp_password:
        logger.info(f"✓ SMTP configured: host={smtp_host}, port={smtp_port}, user={smtp_user}")
        logger.debug(f"SMTP password length: {len(smtp_password)} characters")
        # Validate email format
        if "@" not in smtp_user:
            logger.error(f"✗ SMTP_USER does not appear to be a valid email address: {smtp_user}")
            smtp_user = ""  # Invalidate if not an email
    else:
        logger.warning("✗ SMTP credentials not found or invalid - email notifications will be disabled")
        if not smtp_user:
            logger.warning("✗ SMTP_USER is not set or is invalid")
        if not smtp_password:
            logger.warning("✗ SMTP_PASSWORD is not set or is invalid")
    
    return {
        "host": smtp_host,
        "port": smtp_port,
        "user": smtp_user,
        "password": smtp_password,
        "from": email_from,
    }


def send_email(to_email: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
    """
    Send email notification.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML email body
        body_text: Plain text email body (optional)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        config = get_smtp_config()
        
        # Skip sending if SMTP not configured
        if not config.get("user") or not config.get("password"):
            logger.warning(f"SMTP not configured - email notifications disabled")
            logger.warning(f"Would send email to {to_email}: {subject}")
            logger.warning("To enable emails, configure SMTP_USER and SMTP_PASSWORD in app.yaml or Secret Manager")
            return False
        
        # Validate email address
        if not to_email or '@' not in to_email:
            logger.error(f"Invalid email address: {to_email}")
            return False
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config["from"]
        msg["To"] = to_email
        
        # Add text and HTML parts
        if body_text:
            text_part = MIMEText(body_text, "plain", "utf-8")
            msg.attach(text_part)
        
        html_part = MIMEText(body_html, "html", "utf-8")
        msg.attach(html_part)
        
        # Send email with better error handling
        try:
            port = config["port"]
            host = config["host"]
            
            # Log connection attempt (without sensitive data)
            logger.info(f"Connecting to SMTP server: {host}:{port}")
            
            # Use appropriate SMTP class based on port
            # Port 465 requires SSL, port 587 uses STARTTLS
            if port == 465:
                # Port 465 uses SSL/TLS from the start
                server = smtplib.SMTP_SSL(host, port, timeout=10)
                logger.info("Using SMTP_SSL for port 465")
            else:
                # Port 587 (and others) use STARTTLS
                server = smtplib.SMTP(host, port, timeout=10)
                server.set_debuglevel(0)  # Set to 1 for debugging (change to 1 to see SMTP conversation)
                logger.info("Starting TLS handshake...")
                server.starttls()
                logger.info("TLS handshake successful")
            
            # Authenticate
            logger.info(f"Authenticating as {config['user']}...")
            server.login(config["user"], config["password"])
            logger.info("Authentication successful")
            
            # Send message
            logger.info(f"Sending email to {to_email}...")
            server.send_message(msg)
            server.quit()
            logger.info("SMTP connection closed")
            
            logger.info(f"✅ Email sent successfully to {to_email}: {subject}")
            return True
        except smtplib.SMTPAuthenticationError as auth_error:
            logger.error(f"SMTP authentication failed: {auth_error}")
            logger.error(f"SMTP_HOST: {config['host']}, SMTP_PORT: {config['port']}, SMTP_USER: {config['user']}")
            logger.error("Check your SMTP_USER and SMTP_PASSWORD credentials")
            logger.error("For Gmail, ensure you're using an App Password (not your regular password)")
            return False
        except smtplib.SMTPConnectError as conn_error:
            logger.error(f"SMTP connection error: {conn_error}")
            logger.error(f"Could not connect to {config['host']}:{config['port']}")
            logger.error("Check your SMTP_HOST and SMTP_PORT settings")
            return False
        except smtplib.SMTPException as smtp_error:
            logger.error(f"SMTP error sending email to {to_email}: {smtp_error}")
            logger.error(f"SMTP server: {config['host']}:{config['port']}")
            return False
        except Exception as smtp_err:
            logger.error(f"Error connecting to SMTP server: {smtp_err}")
            logger.error(f"SMTP configuration: host={config['host']}, port={config['port']}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        return False


def send_booking_confirmation_email(user_email: str, username: str, robot_name: str, robot_image_url: str = None):
    """Send booking confirmation email."""
    subject = f"Booking Confirmed: {robot_name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #6C5CE7 0%, #0984E3 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
            .robot-info {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center; }}
            .button {{ display: inline-block; background: #6C5CE7; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 RoboPety Booking Confirmed!</h1>
            </div>
            <div class="content">
                <p>Hi {username},</p>
                <p>Great news! Your booking for <strong>{robot_name}</strong> has been confirmed.</p>
                
                <div class="robot-info">
                    <h2>{robot_name}</h2>
                    {f'<img src="{robot_image_url}" alt="{robot_name}" style="max-width: 200px; border-radius: 8px; margin: 10px 0; display: block; margin-left: auto; margin-right: auto;" />' if robot_image_url and robot_image_url.startswith('http') else ''}
                    <p>Your robot is ready to use!</p>
                </div>
                
                <p>You can manage your bookings and return the robot anytime from your account.</p>
                
                <div class="footer">
                    <p>Thank you for using RoboPety!</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
Hi {username},

Great news! Your booking for {robot_name} has been confirmed.

You can manage your bookings and return the robot anytime from your account.

Thank you for using RoboPety!
    """
    
    return send_email(user_email, subject, html_body, text_body)


def send_booking_reminder_email(user_email: str, username: str, robot_name: str, days_booked: int):
    """Send booking reminder email."""
    subject = f"Reminder: You've had {robot_name} for {days_booked} day(s)"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0984E3 0%, #6C5CE7 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #0984E3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📅 Booking Reminder</h1>
            </div>
            <div class="content">
                <p>Hi {username},</p>
                <p>Just a friendly reminder that you've had <strong>{robot_name}</strong> booked for <strong>{days_booked} day(s)</strong>.</p>
                <p>Remember to return the robot when you're done so others can enjoy it too!</p>
                <p style="margin-top: 15px;">
                    <a href="https://csci0220-472715.appspot.com/user/{username}" class="button" style="text-decoration: none;">Manage Bookings</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_body)


def send_return_confirmation_email(user_email: str, username: str, robot_name: str):
    """Send return confirmation email."""
    subject = f"Return Confirmed: {robot_name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #00B894 0%, #0984E3 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Return Confirmed</h1>
            </div>
            <div class="content">
                <p>Hi {username},</p>
                <p>Thank you for returning <strong>{robot_name}</strong>.</p>
                <p>We hope you enjoyed your time with your robot! Feel free to book another robot anytime.</p>
                <p>Thank you for using RoboPety!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, html_body)

