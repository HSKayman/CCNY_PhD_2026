"""Database service layer with SQLAlchemy and transactional operations."""
import logging
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from db_session import get_db
from models import User, Robot, UserRobot, UserRole, UserRobotAction, Alert, ChatMessage, UserActivityLog, RobotStatus, SecurityEvent
from error_handlers import NotFoundError, ValidationError, AppError

logger = logging.getLogger(__name__)


@contextmanager
def db_transaction():
    """Context manager for database transactions."""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rolled back: {e}", exc_info=True)
        raise
    finally:
        db.close()


def get_robots():
    """Get all robots."""
    with db_transaction() as db:
        robots = db.query(Robot).all()
        return {"status": "success", "data": [r.to_dict() for r in robots]}


def get_robot_count():
    """Get total count of robots."""
    with db_transaction() as db:
        count = db.query(Robot).count()
        return {"status": "success", "count": count}


def get_robot_by_id(robot_id: int):
    """Get robot by ID."""
    with db_transaction() as db:
        robot = db.query(Robot).filter(Robot.id == robot_id).first()
        if not robot:
            raise NotFoundError("Robot not found")
        return {"status": "success", "data": robot.to_dict()}


def change_user_password(user_id: int, old_password: str, new_password: str):
    """Change user password (requires old password verification)."""
    with db_transaction() as db:
        from sqlalchemy import text
        from auth_utils import verify_password, hash_password
        from password_policy import check_password_policy
        
        # Get user with password
        try:
            result = db.execute(
                text("SELECT id, password FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
        except Exception as e:
            logger.error(f"Error fetching user for password change: {e}")
            raise ValidationError("Failed to verify current password")
        
        if not result:
            raise NotFoundError("User not found")
        
        # Verify old password
        if not verify_password(old_password, result.password):
            raise ValidationError("Current password is incorrect")
        
        # Validate new password
        check_password_policy(new_password)
        
        # Hash new password
        new_password_hash = hash_password(new_password)
        
        # Update password
        try:
            db.execute(
                text("UPDATE users SET password = :new_password WHERE id = :user_id"),
                {"new_password": new_password_hash, "user_id": user_id}
            )
            logger.info(f"Password changed for user_id={user_id}")
            return {"status": "success", "message": "Password changed successfully"}
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            raise ValidationError("Failed to update password")


def get_user_by_id(user_id: int):
    """Get user by ID."""
    from sqlalchemy import text
    with db_transaction() as db:
        # Try ORM query first
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotFoundError("User not found")
            return {"status": "success", "data": user.to_dict()}
        except (LookupError, ValueError) as enum_err:
            # Fallback to raw SQL if enum conversion fails
            logger.warning(f"Enum error in get_user_by_id, using raw SQL: {enum_err}")
            result = db.execute(
                text("SELECT id, username, email, password, role, created_at, last_login, login_count FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if not result:
                raise NotFoundError("User not found")
            
            # Convert to dict format
            role_str = result.role.lower() if result.role else "user"
            return {
                "status": "success",
                "data": {
                    "id": result.id,
                    "username": result.username,
                    "email": result.email,
                    "role": role_str,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "last_login": result.last_login.isoformat() if result.last_login else None,
                    "login_count": result.login_count or 0,
                }
            }


def get_user_by_username(username: str):
    """Get user by username."""
    from sqlalchemy import text
    with db_transaction() as db:
        # Try ORM query first
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise NotFoundError("User not found")
            return {"status": "success", "data": user.to_dict()}
        except (LookupError, ValueError) as enum_err:
            # Fallback to raw SQL if enum conversion fails
            logger.warning(f"Enum error in get_user_by_username, using raw SQL: {enum_err}")
            result = db.execute(
                text("SELECT id, username, email, password, role, created_at, last_login, login_count FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()
            
            if not result:
                raise NotFoundError("User not found")
            
            # Convert to dict format
            role_str = result.role.lower() if result.role else "user"
            return {
                "status": "success",
                "data": {
                    "id": result.id,
                    "username": result.username,
                    "email": result.email,
                    "role": role_str,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "last_login": result.last_login.isoformat() if result.last_login else None,
                    "login_count": result.login_count or 0,
                }
            }


def get_user_by_email(email: str):
    """Get user by email."""
    from sqlalchemy import text
    with db_transaction() as db:
        # Try ORM query first
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise NotFoundError("User not found")
            return {"status": "success", "data": user.to_dict()}
        except (LookupError, ValueError) as enum_err:
            # Fallback to raw SQL if enum conversion fails
            logger.warning(f"Enum error in get_user_by_email, using raw SQL: {enum_err}")
            result = db.execute(
                text("SELECT id, username, email, password, role, created_at, last_login, login_count FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if not result:
                raise NotFoundError("User not found")
            
            # Convert to dict format
            role_str = result.role.lower() if result.role else "user"
            return {
                "status": "success",
                "data": {
                    "id": result.id,
                    "username": result.username,
                    "email": result.email,
                    "role": role_str,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "last_login": result.last_login.isoformat() if result.last_login else None,
                    "login_count": result.login_count or 0,
                }
            }


def validate_user(email: str):
    """Validate user by email (for login). Returns user data including password hash."""
    from sqlalchemy import text
    with db_transaction() as db:
        # Query using raw SQL to avoid enum conversion issues with MySQL ENUM
        # SQLAlchemy has issues with MySQL ENUM types when values don't match exactly
        try:
            result = db.execute(
                text("SELECT id, username, email, password, role, two_factor_enabled, two_factor_secret FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"status": "fail", "error": "Credentials are not correct."}
        
        if not result:
            return {"status": "fail", "error": "Credentials are not correct."}
        
        # Get role as string - ensure lowercase for consistency
        role_str = result.role.lower() if result.role else "user"
        
        # Return user data including password for login verification
        user_data = {
            "id": result.id,
            "username": result.username,
            "email": result.email,
            "password": result.password,  # Include password hash for verification
            "role": role_str,  # Return as string
            "two_factor_enabled": bool(result.two_factor_enabled) if hasattr(result, 'two_factor_enabled') else False,
            "two_factor_secret": result.two_factor_secret if hasattr(result, 'two_factor_secret') else None,
        }
        return {"status": "success", "data": user_data}


def add_user(email: str, username: str, password_hash: str, role: UserRole = UserRole.USER):
    """Add a new user with transactional safety."""
    with db_transaction() as db:
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValidationError("This email is already registered. Please use a different email or try logging in.")
        
        # Check if username already exists
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            raise ValidationError("This username is already taken. Please choose a different username.")
        
        # Create new user
        new_user = User(
            email=email,
            username=username,
            password=password_hash,
            role=role
        )
        db.add(new_user)
        db.flush()  # Get the ID without committing
        
        # Return user data
        user_dict = new_user.to_dict()
        return {"status": "success", "data": user_dict}


def get_user_robot_by_user(user_id: int):
    """Get latest user_robot record for a user."""
    with db_transaction() as db:
        user_robot = (
            db.query(UserRobot)
            .filter(UserRobot.user_id == user_id)
            .order_by(UserRobot.id.desc())
            .first()
        )
        if not user_robot:
            return {"status": "fail", "error": "User does not have a robot"}
        return {"status": "success", "data": user_robot.to_dict()}


def get_user_robots_all(user_id: int):
    """Get all robots currently picked by a user (latest action must be PICK, not RETURN)."""
    with db_transaction() as db:
        # Get all unique robot IDs that the user has interacted with
        all_robot_ids = (
            db.query(UserRobot.robot_id)
            .filter(UserRobot.user_id == user_id)
            .distinct()
            .all()
        )
        
        if not all_robot_ids:
            return {"status": "success", "data": []}
        
        # For each robot, check the latest action
        active_robot_ids = []
        for (robot_id,) in all_robot_ids:
            # Get the latest user_robot record for this user and robot
            latest_action = (
                db.query(UserRobot)
                .filter(
                    UserRobot.user_id == user_id,
                    UserRobot.robot_id == robot_id
                )
                .order_by(UserRobot.id.desc())
                .first()
            )
            
            # Only include if latest action is PICK (not RETURN)
            if latest_action and latest_action.action == UserRobotAction.PICK:
                active_robot_ids.append(robot_id)
        
        if not active_robot_ids:
            return {"status": "success", "data": []}
        
        # Get robot details for active robots
        robots_list = []
        for robot_id in active_robot_ids:
            robot = db.query(Robot).filter(Robot.id == robot_id).first()
            if robot:
                robots_list.append({
                    "robot_id": robot.id,
                    "robot_name": robot.name,
                })
        
        return {"status": "success", "data": robots_list}


def get_user_robot_by_robot(robot_id: int):
    """Get latest user_robot record for a robot."""
    with db_transaction() as db:
        user_robot = (
            db.query(UserRobot)
            .filter(UserRobot.robot_id == robot_id)
            .order_by(UserRobot.id.desc())
            .first()
        )
        if not user_robot:
            return {"status": "fail", "error": "No one picked this robot"}
        return {"status": "success", "data": user_robot.to_dict()}


def select_pet(user_id: int, robot_id: int):
    """
    Select a pet with strict ownership checks and transactional safety.
    Uses SELECT FOR UPDATE to prevent race conditions.
    """
    with db_transaction() as db:
        # Use SELECT FOR UPDATE to lock rows and prevent race conditions
        # Check if robot exists
        robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()
        if not robot:
            raise NotFoundError("Robot not found")
        
        # Check if user exists and is not an admin - use raw SQL to avoid enum conversion issues
        from sqlalchemy import text
        try:
            user_result = db.execute(
                text("SELECT id, role FROM users WHERE id = :user_id FOR UPDATE"),
                {"user_id": user_id}
            ).fetchone()
            if not user_result:
                raise NotFoundError("User not found")
            # Check if user is admin - prevent admins from booking robots
            user_role = user_result.role.lower() if user_result.role else "user"
            if user_role == "admin":
                raise ValidationError("Admin users cannot book robots")
        except ValidationError:
            raise
        except Exception as e:
            # Fallback to ORM query if raw SQL fails
            try:
                user = db.query(User).filter(User.id == user_id).with_for_update().first()
                if not user:
                    raise NotFoundError("User not found")
                # Check if user is admin
                if user.role == UserRole.ADMIN:
                    raise ValidationError("Admin users cannot book robots")
            except ValidationError:
                raise
            except (LookupError, ValueError) as enum_err:
                # If enum error, just verify user exists via raw SQL and check role
                logger.warning(f"Enum error in select_pet, using raw SQL: {enum_err}")
                user_result = db.execute(
                    text("SELECT id, role FROM users WHERE id = :user_id FOR UPDATE"),
                    {"user_id": user_id}
                ).fetchone()
                if not user_result:
                    raise NotFoundError("User not found")
                user_role = user_result.role.lower() if user_result.role else "user"
                if user_role == "admin":
                    raise ValidationError("Admin users cannot book robots")
                user_result = db.execute(
                    text("SELECT id FROM users WHERE id = :user_id FOR UPDATE"),
                    {"user_id": user_id}
                ).fetchone()
                if not user_result:
                    raise NotFoundError("User not found")
        
        # Check current state - get latest user_robot for this user
        user_robot_user = (
            db.query(UserRobot)
            .filter(UserRobot.user_id == user_id)
            .order_by(UserRobot.id.desc())
            .with_for_update()
            .first()
        )
        
        # Check if user already has THIS specific robot picked
        # Must check the LATEST action - if latest is RETURN, user doesn't have it
        latest_user_robot_action = (
            db.query(UserRobot)
            .filter(
                UserRobot.user_id == user_id,
                UserRobot.robot_id == robot_id
            )
            .order_by(UserRobot.id.desc())
            .with_for_update()
            .first()
        )
        
        # Only raise error if latest action is PICK (user still has it)
        if latest_user_robot_action and latest_user_robot_action.action == UserRobotAction.PICK:
            raise ValidationError("You already have this robot selected")
        
        # Check current state - get latest user_robot for this robot
        # Only check if robot is currently picked by someone else (not this user)
        user_robot_robot = (
            db.query(UserRobot)
            .filter(UserRobot.robot_id == robot_id)
            .order_by(UserRobot.id.desc())
            .with_for_update()
            .first()
        )
        
        # Check if robot is already picked by someone else (not this user)
        if user_robot_robot and user_robot_robot.action == UserRobotAction.PICK:
            # Only block if it's picked by a different user
            if user_robot_robot.user_id != user_id:
                raise ValidationError("Robot is not available - already selected by another user")
        
        # Create new pick record
        new_user_robot = UserRobot(
            user_id=user_id,
            robot_id=robot_id,
            action=UserRobotAction.PICK
        )
        db.add(new_user_robot)
        db.flush()
        
        # Send booking confirmation email
        try:
            from email_service import send_booking_confirmation_email
            from secrets_manager import get_bucket_name
            robot = db.query(Robot).filter(Robot.id == robot_id).first()
            user = db.query(User).filter(User.id == user_id).first()
            if robot and user and user.email:
                # Construct full image URL if photo_url is just a filename
                image_url = robot.photo_url
                if image_url:
                    # Convert old format to new format if needed
                    if 'storage.cloud.google.com' in image_url:
                        image_url = image_url.replace('storage.cloud.google.com', 'storage.googleapis.com')
                    elif not image_url.startswith('http'):
                        # If it's just a filename, construct full URL
                        bucket_name = get_bucket_name()
                        if bucket_name:
                            # Remove leading slash if present
                            filename = image_url.lstrip('/')
                            image_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
                        else:
                            image_url = None
                    # Ensure URL is properly formatted
                    if image_url and not image_url.startswith('https://'):
                        image_url = None
                else:
                    image_url = None
                
                email_sent = send_booking_confirmation_email(
                    user.email,
                    user.username,
                    robot.name,
                    image_url
                )
                if not email_sent:
                    logger.warning(f"Email notification failed for booking: user_id={user_id}, robot_id={robot_id}")
            elif not user or not user.email:
                logger.warning(f"Cannot send booking email: user {user_id} has no email address")
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email: {e}", exc_info=True)
        
        return {"status": "success", "data": new_user_robot.to_dict()}


def return_pet(user_id: int, robot_id: int):
    """
    Return a pet with strict ownership checks and transactional safety.
    Uses SELECT FOR UPDATE to prevent race conditions.
    """
    with db_transaction() as db:
        # Use SELECT FOR UPDATE to lock rows
        # Check if robot exists
        robot = db.query(Robot).filter(Robot.id == robot_id).with_for_update().first()
        if not robot:
            raise NotFoundError("Robot not found")
        
        # Check if user exists - use raw SQL to avoid enum conversion issues
        from sqlalchemy import text
        try:
            user_result = db.execute(
                text("SELECT id FROM users WHERE id = :user_id FOR UPDATE"),
                {"user_id": user_id}
            ).fetchone()
            if not user_result:
                raise NotFoundError("User not found")
        except Exception as e:
            # Fallback to ORM query if raw SQL fails
            try:
                user = db.query(User).filter(User.id == user_id).with_for_update().first()
                if not user:
                    raise NotFoundError("User not found")
            except (LookupError, ValueError) as enum_err:
                # If enum error, just verify user exists via raw SQL
                logger.warning(f"Enum error in return_pet, using raw SQL: {enum_err}")
                user_result = db.execute(
                    text("SELECT id FROM users WHERE id = :user_id FOR UPDATE"),
                    {"user_id": user_id}
                ).fetchone()
                if not user_result:
                    raise NotFoundError("User not found")
        
        # Check if user owns this specific robot
        user_robot_record = (
            db.query(UserRobot)
            .filter(
                UserRobot.user_id == user_id,
                UserRobot.robot_id == robot_id,
                UserRobot.action == UserRobotAction.PICK
            )
            .order_by(UserRobot.id.desc())
            .with_for_update()
            .first()
        )
        
        # Strict ownership check: user must own this specific robot
        if not user_robot_record:
            raise ValidationError("You don't own this robot")
        
        # Create return record
        new_user_robot = UserRobot(
            user_id=user_id,
            robot_id=robot_id,
            action=UserRobotAction.RETURN
        )
        db.add(new_user_robot)
        db.flush()
        
        # Send return confirmation email
        try:
            from email_service import send_return_confirmation_email
            robot = db.query(Robot).filter(Robot.id == robot_id).first()
            user = db.query(User).filter(User.id == user_id).first()
            if robot and user and user.email:
                email_sent = send_return_confirmation_email(
                    user.email,
                    user.username,
                    robot.name
                )
                if not email_sent:
                    logger.warning(f"Email notification failed for return: user_id={user_id}, robot_id={robot_id}")
            elif not user or not user.email:
                logger.warning(f"Cannot send return email: user {user_id} has no email address")
        except Exception as e:
            logger.error(f"Failed to send return confirmation email: {e}", exc_info=True)
        
        return {"status": "success", "data": new_user_robot.to_dict()}


def get_all_bookings():
    """Get all current robot bookings with user and robot details (admin only)."""
    with db_transaction() as db:
        # Get all unique robot IDs that have been interacted with
        all_robot_ids = (
            db.query(UserRobot.robot_id)
            .distinct()
            .all()
        )
        
        if not all_robot_ids:
            return {"status": "success", "data": []}
        
        # For each robot, check the latest action - only include if latest is PICK
        active_bookings = []
        for (robot_id,) in all_robot_ids:
            # Get the latest user_robot record for this robot
            latest_action = (
                db.query(UserRobot)
                .filter(UserRobot.robot_id == robot_id)
                .order_by(UserRobot.id.desc())
                .first()
            )
            
            # Only include if latest action is PICK (not RETURN)
            if latest_action and latest_action.action == UserRobotAction.PICK:
                # Use raw SQL to avoid enum issues when querying User
                from sqlalchemy import text
                try:
                    user_result = db.execute(
                        text("SELECT id, username, email FROM users WHERE id = :user_id"),
                        {"user_id": latest_action.user_id}
                    ).fetchone()
                except Exception:
                    user_result = None
                
                robot = db.query(Robot).filter(Robot.id == robot_id).first()
                
                if user_result and robot:
                    active_bookings.append({
                        "booking_id": latest_action.id,
                        "user_id": user_result.id,
                        "username": user_result.username,
                        "email": user_result.email,
                        "robot_id": robot.id,
                        "robot_name": robot.name,
                        "robot_image": robot.photo_url,
                        "booked_at": latest_action.created_at.isoformat() if latest_action.created_at else None,
                    })
        
        # Sort by booked_at descending
        active_bookings.sort(key=lambda x: x["booked_at"] or "", reverse=True)
        
        return {"status": "success", "data": active_bookings}


def get_all_users():
    """Get all regular users and Blue Team members (not admins) with their active booking count (admin only)."""
    from sqlalchemy import text
    from sqlalchemy import or_
    with db_transaction() as db:
        # Query users using raw SQL to avoid enum issues, then filter by role
        # Include both regular users and Blue Team members (exclude admins)
        try:
            # Try SQLAlchemy query first with enum - include USER and BLUE_TEAM roles
            users = db.query(User).filter(
                or_(User.role == UserRole.USER, User.role == UserRole.BLUE_TEAM)
            ).all()
        except Exception as e:
            # Fallback to raw SQL if enum query fails
            logger.warning(f"Enum query failed, using raw SQL: {e}")
            # Check if last_login column exists
            try:
                results = db.execute(
                    text("SELECT id, username, email, password, role, created_at, last_login FROM users WHERE LOWER(role) IN ('user', 'blue_team')")
                ).fetchall()
            except Exception:
                # If last_login column doesn't exist, query without it
                results = db.execute(
                    text("SELECT id, username, email, password, role, created_at FROM users WHERE LOWER(role) IN ('user', 'blue_team')")
                ).fetchall()
            users = []
            for result in results:
                # Create a minimal user-like object
                class UserObj:
                    def __init__(self, id, username, email, password, role, created_at, last_login=None):
                        self.id = id
                        self.username = username
                        self.email = email
                        self.password = password
                        self.role = role
                        self.created_at = created_at
                        self.last_login = last_login if hasattr(result, 'last_login') else None
                    @property
                    def _role(self):
                        return self.role.lower() if self.role else "user"
                last_login_val = getattr(result, 'last_login', None) if hasattr(result, 'last_login') else None
                users.append(UserObj(result.id, result.username, result.email, result.password, result.role, result.created_at, last_login_val))
        
        users_list = []
        
        for user in users:
            # Get all unique robot IDs this user has interacted with
            all_robot_ids = (
                db.query(UserRobot.robot_id)
                .filter(UserRobot.user_id == user.id)
                .distinct()
                .all()
            )
            
            # Count only robots where:
            # 1. User's latest action for this robot is PICK, AND
            # 2. Robot's global latest action (across all users) is also PICK by this user
            # This ensures consistency with get_all_bookings()
            active_booking_count = 0
            for (robot_id,) in all_robot_ids:
                # Check user's latest action for this robot
                user_latest_action = (
                    db.query(UserRobot)
                    .filter(
                        UserRobot.user_id == user.id,
                        UserRobot.robot_id == robot_id
                    )
                    .order_by(UserRobot.id.desc())
                    .first()
                )
                
                # Only count if user's latest action is PICK
                if user_latest_action and user_latest_action.action == UserRobotAction.PICK:
                    # Also verify that this robot's global latest action is PICK by this user
                    # This ensures consistency with get_all_bookings()
                    robot_global_latest = (
                        db.query(UserRobot)
                        .filter(UserRobot.robot_id == robot_id)
                        .order_by(UserRobot.id.desc())
                        .first()
                    )
                    
                    # Count only if robot's global latest action is PICK by this user
                    if (robot_global_latest and 
                        robot_global_latest.action == UserRobotAction.PICK and 
                        robot_global_latest.user_id == user.id):
                        active_booking_count += 1
            
            # Get role as string safely
            try:
                role_str = user._role if hasattr(user, '_role') else (user.role.value if hasattr(user.role, 'value') else str(user.role).lower())
            except (AttributeError, ValueError):
                role_str = "user"
            
            # Get last_login if available
            last_login = None
            if hasattr(user, 'last_login') and user.last_login:
                last_login = user.last_login.isoformat() if hasattr(user.last_login, 'isoformat') else str(user.last_login)
            
            users_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role_str,
                "booking_count": active_booking_count,
                "created_at": user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') and user.created_at else (str(user.created_at) if user.created_at else None),
                "last_login": last_login,
            })
        
        return {"status": "success", "data": users_list}


def send_alert_to_user(user_id: int, message: str):
    """Store an alert message for a user (admin only). Never sends to admin."""
    from sqlalchemy import text
    with db_transaction() as db:
        # Use raw SQL to avoid enum conversion issues
        user_result = None
        try:
            user_result = db.execute(
                text("SELECT id, username, role FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            if not user_result:
                raise NotFoundError("User not found")
            # Check role from raw result
            role_str = user_result.role.lower() if user_result.role else "user"
            if role_str == "admin":
                raise ValidationError("Cannot send alerts to admin users")
            username = user_result.username
        except ValidationError:
            raise
        except Exception as e:
            # Fallback to ORM query
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise NotFoundError("User not found")
                # Never send alerts to admin users (keep email private)
                if user.role == UserRole.ADMIN:
                    raise ValidationError("Cannot send alerts to admin users")
                username = user.username
            except (LookupError, ValueError) as enum_err:
                logger.warning(f"Enum error in send_alert_to_user, using raw SQL: {enum_err}")
                user_result = db.execute(
                    text("SELECT id, username, role FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                if not user_result:
                    raise NotFoundError("User not found")
                role_str = user_result.role.lower() if user_result.role else "user"
                if role_str == "admin":
                    raise ValidationError("Cannot send alerts to admin users")
                username = user_result.username
        
        # Check if an identical alert (same message) was already sent to this user recently
        # This prevents duplicate alerts from being sent
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)  # Check last 24 hours
        
        existing_alert = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.message == message,
            Alert.created_at >= recent_cutoff
        ).first()
        
        if existing_alert:
            logger.warning(f"Duplicate alert prevented for user_id={user_id}: {message[:50]}...")
            raise ValidationError(f"An identical alert was already sent to {username} recently. Please wait before sending the same alert again.")
        
        # Create alert record
        alert = Alert(
            user_id=user_id,
            message=message,
            read=False
        )
        db.add(alert)
        db.flush()  # Flush immediately to ensure alert is available in database
        # Commit will happen automatically when exiting context manager
        logger.info(f"Alert created for user_id={user_id}: {message[:50]}...")
        
        return {"status": "success", "message": f"Alert sent to {username}", "alert_id": alert.id}


def get_user_alerts(user_id: int):
    """Get all alerts for a user."""
    with db_transaction() as db:
        alerts = (
            db.query(Alert)
            .filter(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())
            .all()
        )
        
        alerts_list = [alert.to_dict() for alert in alerts]
        unread_count = sum(1 for a in alerts_list if not a["read"])
        
        logger.info(f"Retrieved {len(alerts_list)} alerts for user_id={user_id}, unread={unread_count}")
        
        return {
            "status": "success",
            "data": alerts_list,
            "unread_count": unread_count
        }


def mark_alert_read(alert_id: int, user_id: int):
    """Mark an alert as read (only by the owner)."""
    with db_transaction() as db:
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user_id
        ).first()
        
        if not alert:
            raise NotFoundError("Alert not found")
        
        alert.read = True
        db.flush()
        
        return {"status": "success"}


def send_chat_message(user_id: int, message: str, is_from_admin: bool = False):
    """Send a chat message (user or admin)."""
    from validation_utils import sanitize_chat_message
    
    with db_transaction() as db:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        # Additional sanitization before storing (defense in depth)
        sanitized_message = sanitize_chat_message(message)
        if not sanitized_message or not sanitized_message.strip():
            raise ValidationError("Message cannot be empty after sanitization")
        
        # Create chat message
        chat_message = ChatMessage(
            user_id=user_id,
            message=sanitized_message,
            is_from_admin=is_from_admin,
            read_by_user=is_from_admin,  # If from admin, mark as unread by user
            read_by_admin=not is_from_admin,  # If from user, mark as unread by admin
        )
        db.add(chat_message)
        db.flush()
        
        logger.info(f"Chat message sent: user_id={user_id}, is_admin={is_from_admin}, message_length={len(sanitized_message)}")
        
        return {"status": "success", "data": chat_message.to_dict()}


def get_user_chat_messages(user_id: int):
    """Get all chat messages for a user."""
    with db_transaction() as db:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        
        messages_list = [msg.to_dict() for msg in messages]
        
        # Mark messages as read
        unread_count = 0
        for msg in messages:
            if not msg.is_from_admin and not msg.read_by_user:
                msg.read_by_user = True
                unread_count += 1
            elif msg.is_from_admin and not msg.read_by_user:
                msg.read_by_user = True
                unread_count += 1
        
        db.flush()
        
        return {
            "status": "success",
            "data": messages_list,
            "unread_count": unread_count
        }


def get_all_chat_conversations():
    """Get all chat conversations for admin (grouped by user)."""
    from sqlalchemy import text
    with db_transaction() as db:
        # Get all unique user IDs that have chat messages
        user_ids = (
            db.query(ChatMessage.user_id)
            .distinct()
            .all()
        )
        
        conversations = []
        for (user_id,) in user_ids:
            # Get user info - handle enum conversion issues
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue
                # Check role using string comparison to avoid enum issues
                try:
                    user_role_str = str(user.role.value if hasattr(user.role, 'value') else user.role).lower()
                except:
                    # If role is already a string, use it directly
                    user_role_str = str(user.role).lower() if user.role else 'user'
                if user_role_str == 'admin':
                    continue  # Skip admin users
            except Exception as e:
                logger.warning(f"Error loading user {user_id} for chat conversations: {e}")
                # Fallback to raw SQL
                try:
                    result = db.execute(
                        text("SELECT id, username, email, role FROM users WHERE id = :user_id"),
                        {"user_id": user_id}
                    ).fetchone()
                    if not result or (result.role and result.role.lower() == 'admin'):
                        continue
                    # Create minimal user object
                    class MinimalUser:
                        def __init__(self, id, username, email, role):
                            self.id = id
                            self.username = username
                            self.email = email
                            self.role = role
                    user = MinimalUser(result.id, result.username, result.email, result.role)
                except Exception as e2:
                    logger.error(f"Failed to load user {user_id} even with raw SQL: {e2}")
                    continue
            
            # Get latest message
            latest_message = (
                db.query(ChatMessage)
                .filter(ChatMessage.user_id == user_id)
                .order_by(ChatMessage.created_at.desc())
                .first()
            )
            
            # Count unread messages from users
            unread_count = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.user_id == user_id,
                    ChatMessage.is_from_admin == False,
                    ChatMessage.read_by_admin == False
                )
                .count()
            )
            
            conversations.append({
                "user_id": user_id,
                "username": user.username,
                "email": user.email,
                "latest_message": latest_message.message if latest_message else "",
                "latest_message_time": latest_message.created_at.isoformat() if latest_message else None,
                "unread_count": unread_count,
            })
        
        # Sort by latest message time (most recent first)
        conversations.sort(key=lambda x: x["latest_message_time"] or "", reverse=True)
        
        return {"status": "success", "data": conversations}


def get_chat_messages_for_admin(user_id: int):
    """Get all chat messages for a specific user (admin view)."""
    with db_transaction() as db:
        # Verify user exists and is not admin
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        if user.role == UserRole.ADMIN:
            raise ValidationError("Cannot view chat for admin users")
        
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        
        # Mark user messages as read by admin
        for msg in messages:
            if not msg.is_from_admin and not msg.read_by_admin:
                msg.read_by_admin = True
        
        db.flush()
        
        messages_list = [msg.to_dict() for msg in messages]
        
        return {
            "status": "success",
            "data": messages_list,
            "username": user.username
        }


def mark_chat_messages_read(user_id: int, is_admin: bool = False):
    """Mark chat messages as read."""
    with db_transaction() as db:
        if is_admin:
            # Mark all user messages as read by admin
            messages = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.user_id == user_id,
                    ChatMessage.is_from_admin == False,
                    ChatMessage.read_by_admin == False
                )
                .all()
            )
            for msg in messages:
                msg.read_by_admin = True
        else:
            # Mark all admin messages as read by user
            messages = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.user_id == user_id,
                    ChatMessage.is_from_admin == True,
                    ChatMessage.read_by_user == False
                )
                .all()
            )
            for msg in messages:
                msg.read_by_user = True
        
        db.flush()
        
        return {"status": "success"}


def check_user_robot_availability(user_id: int, robot_id: int) -> bool:
    """
    Check if a robot is available for a user.
    This is a read-only check, not used for transactional operations.
    Note: This is a best-effort check. The actual transactional operations
    in select_pet() and return_pet() provide the real race-condition protection.
    """
    try:
        user_response = get_user_robot_by_user(user_id)
        robot_response = get_user_robot_by_robot(robot_id)
        
        # If no records exist, available
        if user_response["status"] == "fail" and robot_response["status"] == "fail":
            return True
        
        # Check user's latest action
        if user_response["status"] == "success":
            user_action = user_response["data"].get("action")
            # to_dict() returns enum.value as string
            if user_action == "pick":
                # User already has a robot
                return False
        
        # Check robot's latest action
        if robot_response["status"] == "success":
            robot_action = robot_response["data"].get("action")
            # to_dict() returns enum.value as string
            if robot_action == "pick":
                # Robot is currently picked
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return False


def delete_user_and_bookings(user_id: int):
    """
    Delete a user and all their associated data (bookings, alerts).
    This will:
    1. Return all robots currently booked by the user (create RETURN records)
    2. Delete all alerts for the user
    3. Delete all user_robot records
    4. Delete the user account
    
    Note: This should only be called by admins.
    
    Args:
        user_id: ID of the user to delete
        
    Returns:
        Dictionary with status and message
    """
    from sqlalchemy import text
    with db_transaction() as db:
        # Check if user exists and is not an admin
        try:
            user_result = db.execute(
                text("SELECT id, username, role FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            if not user_result:
                raise NotFoundError("User not found")
            
            # Get role but allow deletion (with safety check below)
            role_str = user_result.role.lower() if user_result.role else "user"
            
            username = user_result.username
        except ValidationError:
            raise
        except Exception as e:
            # Fallback to ORM query
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise NotFoundError("User not found")
                # Allow admin deletion (with safety check below)
                role_str = user.role.value.lower() if hasattr(user.role, 'value') else str(user.role).lower()
                username = user.username
            except (LookupError, ValueError) as enum_err:
                logger.warning(f"Enum error in delete_user_and_bookings, using raw SQL: {enum_err}")
                user_result = db.execute(
                    text("SELECT id, username, role FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                if not user_result:
                    raise NotFoundError("User not found")
                # Allow admin deletion (with safety check below)
                role_str = user_result.role.lower() if user_result.role else "user"
                username = user_result.username
        
        # If this is an admin user, check that there's at least one other admin remaining
        if role_str == "admin":
            # Count remaining admins (excluding the one being deleted)
            remaining_admin_count = db.execute(
                text("SELECT COUNT(*) FROM users WHERE role = 'admin' AND id != :user_id"),
                {"user_id": user_id}
            ).scalar()
            
            if remaining_admin_count == 0:
                raise ValidationError("Cannot delete the last admin user. At least one admin must remain.")
        
        # Get all robots currently booked by this user (latest action is PICK)
        active_robot_ids = []
        all_user_robots = (
            db.query(UserRobot)
            .filter(UserRobot.user_id == user_id)
            .all()
        )
        
        # Group by robot_id and find latest action for each
        robot_latest_action = {}
        for ur in all_user_robots:
            if ur.robot_id not in robot_latest_action:
                robot_latest_action[ur.robot_id] = ur
            elif ur.id > robot_latest_action[ur.robot_id].id:
                robot_latest_action[ur.robot_id] = ur
        
        # Find robots that are currently picked (latest action is PICK)
        for robot_id, latest_ur in robot_latest_action.items():
            if latest_ur.action == UserRobotAction.PICK:
                active_robot_ids.append(robot_id)
                # Create RETURN record to free up the robot
                return_record = UserRobot(
                    user_id=user_id,
                    robot_id=robot_id,
                    action=UserRobotAction.RETURN
                )
                db.add(return_record)
        
        # Delete all alerts for this user (cascade should handle this, but explicit for clarity)
        db.query(Alert).filter(Alert.user_id == user_id).delete()
        
        # Delete all user_robot records (cascade should handle this, but explicit for clarity)
        db.query(UserRobot).filter(UserRobot.user_id == user_id).delete()
        
        # Delete the user (this will cascade delete related records)
        db.query(User).filter(User.id == user_id).delete()
        
        logger.info(f"User {username} (ID: {user_id}) deleted. Freed {len(active_robot_ids)} robot(s).")
        
        return {
            "status": "success",
            "message": f"User {username} and all associated data deleted successfully. {len(active_robot_ids)} robot(s) were freed.",
            "freed_robots": len(active_robot_ids)
        }


def get_announcements(active_only: bool = True):
    """Get all announcements (active only by default)."""
    with db_transaction() as db:
        from models import Announcement
        query = db.query(Announcement)
        if active_only:
            query = query.filter(Announcement.is_active == True)
        announcements = query.order_by(Announcement.created_at.desc()).all()
        return {"status": "success", "data": [ann.to_dict() for ann in announcements]}


def create_announcement(title: str, message: str):
    """Create a new announcement."""
    from validation_utils import check_chat_message, sanitize_chat_message, sanitize_input
    from models import Announcement
    
    # Validate and sanitize title and message
    if not title or not title.strip():
        raise ValidationError("Title cannot be empty")
    if len(title.strip()) > 255:
        raise ValidationError("Title is too long (max 255 characters)")
    
    check_chat_message(message)
    sanitized_message = sanitize_chat_message(message)
    sanitized_title = sanitize_input(title.strip(), max_length=255)
    
    with db_transaction() as db:
        announcement = Announcement(
            title=sanitized_title,
            message=sanitized_message,
            is_active=True
        )
        db.add(announcement)
        db.flush()
        
        logger.info(f"Announcement created: id={announcement.id}, title={sanitized_title}")
        return {"status": "success", "data": announcement.to_dict()}


def update_announcement(announcement_id: int, title: str = None, message: str = None, is_active: bool = None):
    """Update an existing announcement."""
    from validation_utils import check_chat_message, sanitize_chat_message, sanitize_input
    from models import Announcement
    
    with db_transaction() as db:
        announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if not announcement:
            raise NotFoundError("Announcement not found")
        
        if title is not None:
            if not title.strip():
                raise ValidationError("Title cannot be empty")
            if len(title.strip()) > 255:
                raise ValidationError("Title is too long (max 255 characters)")
            announcement.title = sanitize_input(title.strip(), max_length=255)
        
        if message is not None:
            check_chat_message(message)
            announcement.message = sanitize_chat_message(message)
        
        if is_active is not None:
            announcement.is_active = is_active
        
        db.flush()
        
        logger.info(f"Announcement updated: id={announcement_id}")
        return {"status": "success", "data": announcement.to_dict()}


def delete_announcement(announcement_id: int):
    """Delete an announcement."""
    from models import Announcement
    
    with db_transaction() as db:
        announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if not announcement:
            raise NotFoundError("Announcement not found")
        
        db.delete(announcement)
        logger.info(f"Announcement deleted: id={announcement_id}")
        return {"status": "success", "message": "Announcement deleted successfully"}


# ==================== NEW FEATURES ====================

def get_user_booking_history(user_id: int, limit: int = 50):
    """Get booking history for a user (completed bookings with duration)."""
    with db_transaction() as db:
        # Get all user_robot records for this user
        user_robots = (
            db.query(UserRobot)
            .filter(UserRobot.user_id == user_id)
            .order_by(UserRobot.id.desc())
            .limit(limit * 2)  # Get more to match PICK/RETURN pairs
            .all()
        )
        
        # Match PICK with corresponding RETURN to calculate duration
        booking_history = []
        pick_records = {}
        
        for record in user_robots:
            if record.action == UserRobotAction.PICK:
                pick_records[record.robot_id] = record
            elif record.action == UserRobotAction.RETURN and record.robot_id in pick_records:
                pick_record = pick_records[record.robot_id]
                robot = db.query(Robot).filter(Robot.id == record.robot_id).first()
                
                duration = None
                if pick_record.created_at and record.created_at:
                    duration_seconds = (record.created_at - pick_record.created_at).total_seconds()
                    duration = int(duration_seconds / 3600)  # Hours
                
                booking_history.append({
                    "robot_id": robot.id if robot else None,
                    "robot_name": robot.name if robot else "Unknown",
                    "robot_image": robot.photo_url if robot else None,
                    "picked_at": pick_record.created_at.isoformat() if pick_record.created_at else None,
                    "returned_at": record.created_at.isoformat() if record.created_at else None,
                    "duration_hours": duration,
                    "status": "completed",
                })
                del pick_records[record.robot_id]
        
        # Add ongoing bookings (PICK without RETURN)
        for robot_id, pick_record in pick_records.items():
            robot = db.query(Robot).filter(Robot.id == robot_id).first()
            booking_history.append({
                "robot_id": robot.id if robot else None,
                "robot_name": robot.name if robot else "Unknown",
                "robot_image": robot.photo_url if robot else None,
                "picked_at": pick_record.created_at.isoformat() if pick_record.created_at else None,
                "returned_at": None,
                "duration_hours": None,
                "status": "active",
            })
        
        # Sort by picked_at descending (most recent first)
        booking_history.sort(key=lambda x: x["picked_at"] or "", reverse=True)
        
        # Status is already correctly set:
        # - "active" for ongoing bookings (PICK without RETURN)
        # - "completed" for returned bookings (PICK with RETURN)
        # No need to override - keep the actual status based on whether robot was returned
        
        return {"status": "success", "data": booking_history[:limit]}


def log_user_activity(user_id: int, activity_type: str, description: str = None, ip_address: str = None, user_agent: str = None):
    """Log user activity."""
    with db_transaction() as db:
        activity = UserActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(activity)
        return {"status": "success"}


def update_user_login(user_id: int, ip_address: str = None, user_agent: str = None):
    """Update user login timestamp and count."""
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        from datetime import datetime
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        
        # Log activity
        log_user_activity(user_id, "login", "User logged in", ip_address, user_agent)
        
        return {"status": "success"}


def get_user_activity_log(user_id: int, limit: int = 100):
    """Get activity log for a user."""
    with db_transaction() as db:
        activities = (
            db.query(UserActivityLog)
            .filter(UserActivityLog.user_id == user_id)
            .order_by(UserActivityLog.id.desc())
            .limit(limit)
            .all()
        )
        return {"status": "success", "data": [a.to_dict() for a in activities]}


def get_user_statistics(user_id: int):
    """Get comprehensive statistics for a user."""
    from sqlalchemy import func
    from datetime import datetime
    
    with db_transaction() as db:
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        # Get current robots count (only robots where latest action is PICK, not RETURN)
        # Get all unique robot IDs that the user has interacted with
        all_robot_ids = (
            db.query(UserRobot.robot_id)
            .filter(UserRobot.user_id == user_id)
            .distinct()
            .all()
        )
        
        current_robots = 0
        for (robot_id,) in all_robot_ids:
            # Get the latest user_robot record for this user and robot
            latest_action = (
                db.query(UserRobot)
                .filter(
                    UserRobot.user_id == user_id,
                    UserRobot.robot_id == robot_id
                )
                .order_by(UserRobot.id.desc())
                .first()
            )
            
            # Only count if latest action is PICK (not RETURN)
            if latest_action and latest_action.action == UserRobotAction.PICK:
                current_robots += 1
        
        # Get total robots ever selected (count distinct robot_ids from PICK actions)
        total_robots_selected = db.query(func.count(func.distinct(UserRobot.robot_id))).filter(
            UserRobot.user_id == user_id,
            UserRobot.action == UserRobotAction.PICK
        ).scalar() or 0
        
        # Get total bookings count
        total_bookings = db.query(UserRobot).filter(
            UserRobot.user_id == user_id,
            UserRobot.action == UserRobotAction.PICK
        ).count()
        
        # Get account age in days
        account_age_days = 0
        if user.created_at:
            account_age_days = (datetime.utcnow() - user.created_at).days
    
    # Get booking history outside transaction to avoid nested transaction issues
    booking_history = get_user_booking_history(user_id, limit=1000)
    total_hours = 0
    favorite_robot_id = None
    favorite_robot_count = 0
    robot_counts = {}
    
    if booking_history.get("status") == "success":
        for booking in booking_history.get("data", []):
            if booking.get("duration_hours"):
                total_hours += booking.get("duration_hours", 0)
            # Track favorite robot
            robot_id = booking.get("robot_id")
            if robot_id:
                robot_counts[robot_id] = robot_counts.get(robot_id, 0) + 1
                if robot_counts[robot_id] > favorite_robot_count:
                    favorite_robot_count = robot_counts[robot_id]
                    favorite_robot_id = robot_id
    
    # Get favorite robot name
    favorite_robot_name = None
    if favorite_robot_id:
        with db_transaction() as db:
            robot = db.query(Robot).filter(Robot.id == favorite_robot_id).first()
            if robot:
                favorite_robot_name = robot.name
    
    return {
        "status": "success",
        "data": {
            "current_robots": current_robots,
            "total_robots_selected": total_robots_selected,
            "total_booking_hours": total_hours,
            "favorite_robot": favorite_robot_name,
            "favorite_robot_id": favorite_robot_id,
            "account_age_days": account_age_days,
            "total_bookings": total_bookings,
            "login_count": user.login_count or 0,
            "member_since": user.created_at.isoformat() if user.created_at else None,
        }
    }


def get_all_activity_logs(limit: int = 500, activity_type: str = None):
    """Get all activity logs (admin only)."""
    with db_transaction() as db:
        query = db.query(UserActivityLog).options(joinedload(UserActivityLog.user))
        if activity_type:
            query = query.filter(UserActivityLog.activity_type == activity_type)
        activities = query.order_by(UserActivityLog.id.desc()).limit(limit).all()
        return {"status": "success", "data": [a.to_dict() for a in activities]}


def create_robot(name: str, photo_url: str, description: str = None, category: str = None, status: str = "available"):
    """Create a new robot. Prevents duplicates by name (case-insensitive)."""
    with db_transaction() as db:
        if not name or not photo_url:
            raise ValidationError("Name and photo_url are required")
        
        # Check for duplicate robot by name (case-insensitive)
        from sqlalchemy import func
        existing_robot = db.query(Robot).filter(
            func.lower(Robot.name) == func.lower(name)
        ).first()
        
        if existing_robot:
            raise ValidationError(f"Robot with name '{name}' already exists (ID: {existing_robot.id})")
        
        # Also check for duplicate photo_url (optional - in case same image is used)
        existing_by_url = db.query(Robot).filter(Robot.photo_url == photo_url).first()
        if existing_by_url:
            raise ValidationError(f"Robot with photo URL '{photo_url}' already exists (ID: {existing_by_url.id}, name: {existing_by_url.name})")
        
        robot = Robot(
            name=name,
            photo_url=photo_url,
            description=description,
            category=category,
            status=status,
            is_active=True
        )
        db.add(robot)
        db.flush()
        
        logger.info(f"Robot created: id={robot.id}, name={robot.name}")
        return {"status": "success", "data": robot.to_dict()}


def update_robot(robot_id: int, name: str = None, photo_url: str = None, description: str = None, 
                 category: str = None, status: str = None, is_active: bool = None):
    """Update robot information. Prevents duplicates when updating name or photo_url."""
    with db_transaction() as db:
        robot = db.query(Robot).filter(Robot.id == robot_id).first()
        if not robot:
            raise NotFoundError("Robot not found")
        
        # Check for duplicate name if updating name
        if name is not None:
            from sqlalchemy import func
            existing_robot = db.query(Robot).filter(
                func.lower(Robot.name) == func.lower(name),
                Robot.id != robot_id  # Exclude current robot
            ).first()
            
            if existing_robot:
                raise ValidationError(f"Robot with name '{name}' already exists (ID: {existing_robot.id})")
            
            robot.name = name
        
        # Check for duplicate photo_url if updating photo_url
        if photo_url is not None:
            existing_by_url = db.query(Robot).filter(
                Robot.photo_url == photo_url,
                Robot.id != robot_id  # Exclude current robot
            ).first()
            
            if existing_by_url:
                raise ValidationError(f"Robot with photo URL '{photo_url}' already exists (ID: {existing_by_url.id}, name: {existing_by_url.name})")
            
            robot.photo_url = photo_url
        
        if description is not None:
            robot.description = description
        if category is not None:
            robot.category = category
        if status is not None:
            robot.status = status
        if is_active is not None:
            robot.is_active = is_active
        
        from datetime import datetime
        robot.updated_at = datetime.utcnow()
        
        db.flush()
        logger.info(f"Robot updated: id={robot_id}")
        return {"status": "success", "data": robot.to_dict()}


def delete_robot(robot_id: int):
    """Delete a robot."""
    with db_transaction() as db:
        robot = db.query(Robot).filter(Robot.id == robot_id).first()
        if not robot:
            raise NotFoundError("Robot not found")
        
        # Check if robot has active bookings
        active_bookings = (
            db.query(UserRobot)
            .filter(UserRobot.robot_id == robot_id)
            .order_by(UserRobot.id.desc())
            .first()
        )
        
        if active_bookings and active_bookings.action == UserRobotAction.PICK:
            raise ValidationError("Cannot delete robot with active bookings")
        
        db.delete(robot)
        logger.info(f"Robot deleted: id={robot_id}")
        return {"status": "success", "message": "Robot deleted successfully"}


def search_robots(query: str, category: str = None, status: str = None, is_active: bool = True):
    """Search robots by name, description, or category."""
    from sqlalchemy import or_, func
    with db_transaction() as db:
        search_query = db.query(Robot)
        
        if query:
            # Use case-insensitive search
            filters = [func.lower(Robot.name).contains(func.lower(query))]
            # Add description filter if description column exists
            try:
                filters.append(func.lower(Robot.description).contains(func.lower(query)))
            except:
                pass
            search_query = search_query.filter(or_(*filters))
        
        if category:
            search_query = search_query.filter(Robot.category == category)
        
        if status:
            search_query = search_query.filter(Robot.status == status)
        
        if is_active is not None:
            search_query = search_query.filter(Robot.is_active == is_active)
        
        robots = search_query.all()
        return {"status": "success", "data": [r.to_dict() for r in robots]}


def search_users(query: str, role: str = None):
    """Search users by username or email."""
    from sqlalchemy import or_, func
    with db_transaction() as db:
        search_query = db.query(User)
        
        if query:
            # Use case-insensitive search
            search_query = search_query.filter(
                or_(
                    func.lower(User.username).contains(func.lower(query)),
                    func.lower(User.email).contains(func.lower(query))
                )
            )
        
        if role:
            search_query = search_query.filter(User.role == role)
        
        users = search_query.all()
        return {"status": "success", "data": [u.to_dict() for u in users]}


def get_booking_analytics(start_date: str = None, end_date: str = None):
    """Get booking analytics for admin dashboard."""
    from datetime import datetime, timedelta
    with db_transaction() as db:
        # Total bookings
        query = db.query(UserRobot).filter(UserRobot.action == UserRobotAction.PICK)
        
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(UserRobot.created_at >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(UserRobot.created_at <= end)
        
        total_bookings = query.count()
        
        # Bookings by day (last 30 days)
        bookings_by_day = []
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = db.query(UserRobot).filter(
                UserRobot.action == UserRobotAction.PICK,
                UserRobot.created_at >= day_start,
                UserRobot.created_at < day_end
            ).count()
            bookings_by_day.append({
                "date": day_start.isoformat(),
                "count": count
            })
        bookings_by_day.reverse()
        
        # Most popular robots
        from sqlalchemy import func
        popular_robots = (
            db.query(
                Robot.id,
                Robot.name,
                func.count(UserRobot.id).label('booking_count')
            )
            .join(UserRobot, Robot.id == UserRobot.robot_id)
            .filter(UserRobot.action == UserRobotAction.PICK)
            .group_by(Robot.id, Robot.name)
            .order_by(func.count(UserRobot.id).desc())
            .limit(10)
            .all()
        )
        
        popular_robots_list = [{"robot_id": r.id, "robot_name": r.name, "booking_count": r.booking_count} for r in popular_robots]
        
        return {
            "status": "success",
            "data": {
                "total_bookings": total_bookings,
                "bookings_by_day": bookings_by_day,
                "popular_robots": popular_robots_list,
            }
        }


def get_robot_booking_days(robot_id: int, start_date: str = None, end_date: str = None):
    """Get booking days for a specific robot (which days it was booked)."""
    from datetime import datetime, timedelta
    with db_transaction() as db:
        # Get all PICK actions for this robot
        query = db.query(UserRobot).filter(
            UserRobot.robot_id == robot_id,
            UserRobot.action == UserRobotAction.PICK
        )
        
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(UserRobot.created_at >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(UserRobot.created_at <= end)
        
        picks = query.order_by(UserRobot.created_at).all()
        
        # Get corresponding RETURN actions to calculate booking duration
        booking_days = {}  # {date: count}
        
        for pick in picks:
            pick_date = pick.created_at.date()
            
            # Find corresponding return (if any)
            return_action = (
                db.query(UserRobot)
                .filter(
                    UserRobot.robot_id == robot_id,
                    UserRobot.user_id == pick.user_id,
                    UserRobot.action == UserRobotAction.RETURN,
                    UserRobot.id > pick.id
                )
                .order_by(UserRobot.id)
                .first()
            )
            
            # Count days this robot was booked
            if return_action:
                return_date = return_action.created_at.date()
                current_date = pick_date
                while current_date <= return_date:
                    booking_days[current_date.isoformat()] = booking_days.get(current_date.isoformat(), 0) + 1
                    current_date += timedelta(days=1)
            else:
                # Still booked (no return yet) - count from pick date to today
                end_date_obj = datetime.utcnow().date()
                current_date = pick_date
                while current_date <= end_date_obj:
                    booking_days[current_date.isoformat()] = booking_days.get(current_date.isoformat(), 0) + 1
                    current_date += timedelta(days=1)
        
        # Convert to list of {date, count} for chart
        booking_days_list = [
            {"date": date, "count": count}
            for date, count in sorted(booking_days.items())
        ]
        
        return {
            "status": "success",
            "data": {
                "robot_id": robot_id,
                "booking_days": booking_days_list
            }
        }


def bulk_delete_users(user_ids: list):
    """Bulk delete users."""
    with db_transaction() as db:
        deleted_count = 0
        for user_id in user_ids:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.role != UserRole.ADMIN:
                    db.delete(user)
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete user {user_id}: {e}")
        
        logger.info(f"Bulk deleted {deleted_count} users")
        return {"status": "success", "message": f"Deleted {deleted_count} users", "deleted_count": deleted_count}


def get_all_alerts(limit: int = 100, offset: int = 0):
    """Get all alerts (admin only)."""
    with db_transaction() as db:
        alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).offset(offset).all()
        total = db.query(Alert).count()
        
        result = []
        for alert in alerts:
            user = db.query(User).filter(User.id == alert.user_id).first()
            result.append({
                "id": alert.id,
                "user_id": alert.user_id,
                "username": user.username if user else "Unknown",
                "email": user.email if user else "Unknown",
                "message": alert.message,
                "read": alert.read,
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            })
        
        return {"status": "success", "data": result, "total": total}


def delete_alert(alert_id: int):
    """Delete an alert (admin only)."""
    with db_transaction() as db:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise NotFoundError("Alert not found")
        
        db.delete(alert)
        logger.info(f"Alert {alert_id} deleted by admin")
        return {"status": "success", "message": "Alert deleted successfully"}


def delete_old_alerts(days_old: int = 30):
    """Delete alerts older than specified days (admin only)."""
    from datetime import datetime, timedelta
    with db_transaction() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        old_alerts = db.query(Alert).filter(Alert.created_at < cutoff_date).all()
        count = len(old_alerts)
        
        for alert in old_alerts:
            db.delete(alert)
        
        logger.info(f"Deleted {count} alerts older than {days_old} days")
        return {"status": "success", "message": f"Deleted {count} old alerts", "deleted_count": count}


def export_bookings_csv(start_date: str = None, end_date: str = None):
    """Export bookings data as CSV format."""
    from datetime import datetime
    import re
    
    try:
        with db_transaction() as db:
            query = db.query(UserRobot).filter(UserRobot.action == UserRobotAction.PICK)
            
            if start_date:
                try:
                    # Handle different date formats (YYYY-MM-DD or ISO format)
                    start_date_clean = start_date.strip()
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', start_date_clean):
                        start = datetime.strptime(start_date_clean, '%Y-%m-%d')
                    else:
                        # Try ISO format
                        start_date_clean = start_date_clean.replace('Z', '+00:00')
                        start = datetime.fromisoformat(start_date_clean)
                    query = query.filter(UserRobot.created_at >= start)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid start_date format: {start_date}, error: {e}")
                    # Continue without date filter if invalid
            
            if end_date:
                try:
                    # Handle different date formats (YYYY-MM-DD or ISO format)
                    end_date_clean = end_date.strip()
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', end_date_clean):
                        # Add time to end of day
                        end = datetime.strptime(end_date_clean, '%Y-%m-%d')
                        end = end.replace(hour=23, minute=59, second=59)
                    else:
                        # Try ISO format
                        end_date_clean = end_date_clean.replace('Z', '+00:00')
                        end = datetime.fromisoformat(end_date_clean)
                    query = query.filter(UserRobot.created_at <= end)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Invalid end_date format: {end_date}, error: {e}")
                    # Continue without date filter if invalid
            
            bookings = query.order_by(UserRobot.created_at.desc()).all()
            
            csv_lines = ["User ID,Username,Email,Robot ID,Robot Name,Booked At\n"]
            for booking in bookings:
                try:
                    user = db.query(User).filter(User.id == booking.user_id).first()
                    robot = db.query(Robot).filter(Robot.id == booking.robot_id).first()
                    if user and robot:
                        booked_at = booking.created_at.isoformat() if booking.created_at else ""
                        # Escape commas and quotes in CSV
                        username = (user.username or "").replace('"', '""')
                        email = (user.email or "").replace('"', '""')
                        robot_name = (robot.name or "").replace('"', '""')
                        csv_lines.append(f'{user.id},"{username}","{email}",{robot.id},"{robot_name}",{booked_at}\n')
                except Exception as e:
                    logger.warning(f"Error processing booking {booking.id}: {e}")
                    continue  # Skip this booking if there's an error
            
            csv_data = "".join(csv_lines)
            return {"status": "success", "data": csv_data}
    except Exception as e:
        logger.error(f"Error exporting bookings CSV: {e}", exc_info=True)
        raise AppError(f"Failed to export bookings: {str(e)}")


def update_chat_message_with_attachment(message_id: int, attachment_url: str = None):
    """Update chat message with attachment (placeholder for future file upload feature)."""
    with db_transaction() as db:
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise NotFoundError("Chat message not found")
        
        # For now, just add attachment info to message text
        # In future, add attachment_url column to ChatMessage model
        if attachment_url:
            message.message = f"{message.message} [Attachment: {attachment_url}]"
        
        return {"status": "success", "data": message.to_dict()}


# ==================== 2FA Management Functions ====================

def get_user_2fa_status(user_id: int):
    """Get user's 2FA status."""
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        backup_codes_count = 0
        if user.two_factor_backup_codes:
            from two_factor_auth import backup_codes_from_json
            codes = backup_codes_from_json(user.two_factor_backup_codes)
            backup_codes_count = len(codes)
        
        return {
            "status": "success",
            "data": {
                "two_factor_enabled": user.two_factor_enabled or False,
                "backup_codes_count": backup_codes_count,
            }
        }


def get_user_backup_codes(user_id: int):
    """Get user's backup codes (for download)."""
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        if not user.two_factor_enabled:
            raise ValidationError("2FA is not enabled")
        
        if not user.two_factor_backup_codes:
            return {
                "status": "success",
                "data": {
                    "backup_codes": [],
                    "message": "No backup codes available"
                }
            }
        
        from two_factor_auth import backup_codes_from_json
        codes = backup_codes_from_json(user.two_factor_backup_codes)
        
        return {
            "status": "success",
            "data": {
                "backup_codes": codes,
                "count": len(codes)
            }
        }


def generate_2fa_secret(user_id: int):
    """Generate a new 2FA secret for a user (before enabling)."""
    from two_factor_auth import generate_secret, generate_qr_code
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        # Generate new secret
        secret = generate_secret()
        
        # Generate QR code
        qr_code = generate_qr_code(secret, user.email)
        
        return {
            "status": "success",
            "data": {
                "secret": secret,
                "qr_code": qr_code,
                "email": user.email,
            }
        }


def enable_2fa(user_id: int, secret: str, verification_code: str):
    """Enable 2FA for a user after verifying the code."""
    from two_factor_auth import verify_totp, generate_backup_codes, backup_codes_to_json
    
    # Clean the secret - remove any whitespace
    secret = str(secret).strip()
    verification_code = str(verification_code).strip().replace(' ', '').replace('-', '')
    
    if not secret:
        raise ValidationError("Invalid secret")
    
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        # Verify the code
        if not verify_totp(secret, verification_code):
            logger.warning(f"2FA enable verification failed for user_id={user_id}")
            raise ValidationError("Invalid verification code. Please try again.")
        
        # Enable 2FA and store secret (ensure it's stored as-is, no encoding issues)
        user.two_factor_enabled = True
        user.two_factor_secret = secret  # Store the cleaned secret
        
        # Generate backup codes
        backup_codes = generate_backup_codes(10)
        user.two_factor_backup_codes = backup_codes_to_json(backup_codes)
        
        # Flush to ensure it's saved
        db.flush()
        
        # Verify the secret was stored correctly by reading it back
        db.refresh(user)
        stored_secret = user.two_factor_secret
        if stored_secret != secret:
            logger.error(f"Secret mismatch after storage! Original: {secret[:10]}..., Stored: {stored_secret[:10] if stored_secret else 'None'}...")
            raise AppError("Failed to store 2FA secret correctly")
        
        logger.info(f"2FA enabled successfully for user_id={user_id}, secret length={len(secret)}")
        
        return {
            "status": "success",
            "data": {
                "backup_codes": backup_codes,
                "message": "2FA enabled successfully. Please save your backup codes."
            }
        }


def disable_2fa(user_id: int, password: str):
    """Disable 2FA for a user (requires password verification)."""
    from auth_utils import verify_password
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        # Verify password
        if not verify_password(password, user.password):
            raise ValidationError("Invalid password")
        
        # Disable 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = None
        
        return {"status": "success", "message": "2FA disabled successfully"}


def verify_2fa_code(user_id: int, code: str) -> bool:
    """Verify a 2FA code for a user (used during login)."""
    from two_factor_auth import verify_totp, verify_backup_code
    
    # Clean the code - remove spaces and ensure it's a string
    code = str(code).strip().replace(' ', '').replace('-', '')
    
    if not code:
        logger.warning(f"Empty 2FA code provided for user_id={user_id}")
        return False
    
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return False
        
        if not user.two_factor_enabled:
            logger.warning(f"2FA not enabled for user_id={user_id}")
            return False
        
        if not user.two_factor_secret:
            logger.error(f"2FA secret missing for user_id={user_id} (2FA is enabled but secret is None)")
            return False
        
        # Clean the stored secret (in case there's any whitespace)
        secret = str(user.two_factor_secret).strip()
        if not secret:
            logger.error(f"2FA secret is empty for user_id={user_id}")
            return False
        
        logger.debug(f"Verifying 2FA for user_id={user_id}, secret length={len(secret)}, code length={len(code)}")
        
        # Try TOTP code first (with larger window to account for clock skew)
        if verify_totp(secret, code, window=2):
            logger.info(f"TOTP code verified successfully for user_id={user_id}")
            return True
        
        # Try backup code (8-digit codes)
        if user.two_factor_backup_codes and len(code) == 8:
            is_valid, updated_codes = verify_backup_code(user.two_factor_backup_codes, code)
            if is_valid:
                # Update backup codes (remove used one)
                user.two_factor_backup_codes = updated_codes
                logger.info(f"Backup code verified successfully for user_id={user_id}")
                return True
        
        logger.warning(f"2FA verification failed for user_id={user_id}, code length={len(code)}, secret exists={bool(secret)}")
        return False


def get_users_with_2fa():
    """Get all users who have 2FA enabled (admin only)."""
    from sqlalchemy import text
    with db_transaction() as db:
        try:
            users = db.query(User).filter(
                User.two_factor_enabled == True,
                User.two_factor_secret.isnot(None)
            ).all()
        except Exception as e:
            logger.warning(f"Enum query failed in get_users_with_2fa, using raw SQL: {e}")
            # Fallback to raw SQL to avoid enum issues
            results = db.execute(
                text("""
                    SELECT id, username, email, two_factor_enabled, two_factor_secret, 
                           two_factor_backup_codes, created_at, last_login
                    FROM users 
                    WHERE two_factor_enabled = 1 AND two_factor_secret IS NOT NULL
                """)
            ).fetchall()
            users = []
            for result in results:
                # Create a minimal user-like object
                class MinimalUser:
                    def __init__(self, row):
                        self.id = row.id
                        self.username = row.username
                        self.email = row.email
                        self.two_factor_enabled = bool(row.two_factor_enabled)
                        self.two_factor_secret = row.two_factor_secret
                        self.two_factor_backup_codes = row.two_factor_backup_codes
                        self.created_at = row.created_at
                        self.last_login = row.last_login
                users.append(MinimalUser(result))
        
        result = []
        for user in users:
            # Count backup codes
            backup_codes_count = 0
            if user.two_factor_backup_codes:
                from two_factor_auth import backup_codes_from_json
                backup_codes = backup_codes_from_json(user.two_factor_backup_codes)
                backup_codes_count = len(backup_codes)
            
            result.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "two_factor_enabled": user.two_factor_enabled,
                "backup_codes_count": backup_codes_count,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        
        return {"status": "success", "data": result}


def admin_disable_user_2fa(user_id: int):
    """Disable 2FA for a user (admin only)."""
    with db_transaction() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        if not user.two_factor_enabled:
            return {"status": "success", "message": "2FA is already disabled for this user"}
        
        # Disable 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_backup_codes = None
        
        logger.info(f"Admin disabled 2FA for user_id={user_id}, username={user.username}")
        
        return {
            "status": "success",
            "message": f"2FA has been disabled for user {user.username}",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        }


# ==================== BLUE TEAM FUNCTIONS ====================

def create_security_event(event_type: str, severity: str, description: str, ip_address: str = None, user_id: int = None, user_agent: str = None, event_metadata: str = None):
    """Create a security event."""
    with db_transaction() as db:
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_id=user_id,
            user_agent=user_agent,
            event_metadata=event_metadata
        )
        db.add(event)
        logger.info(f"Security event created: {event_type} - {severity} - {description}")
        return {"status": "success", "data": event.to_dict()}


def get_security_events(limit: int = 100, severity: str = None, resolved: bool = None, event_type: str = None):
    """Get security events for blue team."""
    with db_transaction() as db:
        query = db.query(SecurityEvent).options(joinedload(SecurityEvent.user), joinedload(SecurityEvent.resolver))
        
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
        if resolved is not None:
            query = query.filter(SecurityEvent.resolved == resolved)
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        
        events = query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()
        return {"status": "success", "data": [e.to_dict() for e in events]}


def resolve_security_event(event_id: int, resolved_by: int):
    """Mark a security event as resolved."""
    with db_transaction() as db:
        from datetime import datetime
        event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
        if not event:
            raise NotFoundError("Security event not found")
        
        event.resolved = True
        event.resolved_at = datetime.utcnow()
        event.resolved_by = resolved_by
        
        logger.info(f"Security event {event_id} resolved by user {resolved_by}")
        return {"status": "success", "data": event.to_dict()}


def get_admin_security_threats(severity: str = None, resolved: bool = None):
    """Get high and critical security threats for admin review (marked by Blue Team)."""
    with db_transaction() as db:
        from sqlalchemy import or_
        query = db.query(SecurityEvent).options(joinedload(SecurityEvent.user), joinedload(SecurityEvent.resolver))
        
        # Only show high and critical threats
        query = query.filter(or_(SecurityEvent.severity == "high", SecurityEvent.severity == "critical"))
        
        # Filter by severity if specified
        if severity and severity in ["high", "critical"]:
            query = query.filter(SecurityEvent.severity == severity)
        
        # Filter by resolved status if specified
        if resolved is not None:
            query = query.filter(SecurityEvent.resolved == resolved)
        
        events = query.order_by(SecurityEvent.created_at.desc()).all()
        return {"status": "success", "data": [e.to_dict() for e in events]}


def respond_to_security_threat(event_id: int, admin_response: str, admin_id: int, mark_resolved: bool = False):
    """Admin responds to a security threat."""
    with db_transaction() as db:
        from datetime import datetime
        event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
        if not event:
            raise NotFoundError("Security event not found")
        
        if not admin_response or not admin_response.strip():
            raise ValidationError("Admin response is required")
        
        event.admin_response = admin_response.strip()
        event.admin_responded_at = datetime.utcnow()
        
        # Optionally mark as resolved
        if mark_resolved:
            event.resolved = True
            event.resolved_at = datetime.utcnow()
            event.resolved_by = admin_id
        
        logger.info(f"Admin {admin_id} responded to security event {event_id}")
        return {"status": "success", "data": event.to_dict()}


def get_all_activity_logs(limit: int = 500, activity_type: str = None, user_id: int = None):
    """Get all activity logs for blue team analytics."""
    with db_transaction() as db:
        query = db.query(UserActivityLog).options(joinedload(UserActivityLog.user))
        
        if activity_type:
            query = query.filter(UserActivityLog.activity_type == activity_type)
        if user_id:
            query = query.filter(UserActivityLog.user_id == user_id)
        
        logs = query.order_by(UserActivityLog.created_at.desc()).limit(limit).all()
        return {"status": "success", "data": [log.to_dict() for log in logs]}


def get_blue_team_analytics():
    """Get comprehensive analytics for blue team dashboard."""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    with db_transaction() as db:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Security events statistics
        total_events = db.query(func.count(SecurityEvent.id)).scalar() or 0
        critical_events = db.query(func.count(SecurityEvent.id)).filter(SecurityEvent.severity == "critical", SecurityEvent.resolved == False).scalar() or 0
        high_events = db.query(func.count(SecurityEvent.id)).filter(SecurityEvent.severity == "high", SecurityEvent.resolved == False).scalar() or 0
        events_24h = db.query(func.count(SecurityEvent.id)).filter(SecurityEvent.created_at >= last_24h).scalar() or 0
        events_7d = db.query(func.count(SecurityEvent.id)).filter(SecurityEvent.created_at >= last_7d).scalar() or 0
        unresolved_events = db.query(func.count(SecurityEvent.id)).filter(SecurityEvent.resolved == False).scalar() or 0
        
        # Activity logs statistics
        total_activities = db.query(func.count(UserActivityLog.id)).scalar() or 0
        activities_24h = db.query(func.count(UserActivityLog.id)).filter(UserActivityLog.created_at >= last_24h).scalar() or 0
        activities_7d = db.query(func.count(UserActivityLog.id)).filter(UserActivityLog.created_at >= last_7d).scalar() or 0
        
        # User statistics
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users_24h = db.query(func.count(func.distinct(UserActivityLog.user_id))).filter(UserActivityLog.created_at >= last_24h).scalar() or 0
        active_users_7d = db.query(func.count(func.distinct(UserActivityLog.user_id))).filter(UserActivityLog.created_at >= last_7d).scalar() or 0
        
        # Failed login attempts (from activity logs)
        failed_logins_24h = db.query(func.count(UserActivityLog.id)).filter(
            UserActivityLog.activity_type == "failed_login",
            UserActivityLog.created_at >= last_24h
        ).scalar() or 0
        
        # Event types breakdown
        event_types = db.query(
            SecurityEvent.event_type,
            func.count(SecurityEvent.id).label('count')
        ).group_by(SecurityEvent.event_type).all()
        event_types_dict = {et[0]: et[1] for et in event_types}
        
        # Severity breakdown
        severity_breakdown = db.query(
            SecurityEvent.severity,
            func.count(SecurityEvent.id).label('count')
        ).group_by(SecurityEvent.severity).all()
        severity_dict = {s[0]: s[1] for s in severity_breakdown}
        
        # Activity types breakdown
        activity_types = db.query(
            UserActivityLog.activity_type,
            func.count(UserActivityLog.id).label('count')
        ).group_by(UserActivityLog.activity_type).limit(20).all()
        activity_types_dict = {at[0]: at[1] for at in activity_types}
        
        return {
            "status": "success",
            "data": {
                "security_events": {
                    "total": total_events,
                    "critical": critical_events,
                    "high": high_events,
                    "unresolved": unresolved_events,
                    "last_24h": events_24h,
                    "last_7d": events_7d,
                    "by_type": event_types_dict,
                    "by_severity": severity_dict
                },
                "activity_logs": {
                    "total": total_activities,
                    "last_24h": activities_24h,
                    "last_7d": activities_7d,
                    "by_type": activity_types_dict
                },
                "users": {
                    "total": total_users,
                    "active_24h": active_users_24h,
                    "active_7d": active_users_7d
                },
                "failed_logins": {
                    "last_24h": failed_logins_24h
                }
            }
        }


def update_user_role(user_id: int, new_role: UserRole):
    """Update user role (admin only)."""
    from sqlalchemy import text
    with db_transaction() as db:
        # Get user first to check if exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        
        old_role_str = str(user.role.value if hasattr(user.role, 'value') else user.role)
        new_role_str = new_role.value
        
        # Use raw SQL to update role to avoid check constraint issues
        try:
            # First, try to drop the constraint if it exists and is blocking
            try:
                # Check if constraint exists and drop it
                db.execute(text("""
                    SET @constraint_exists = (
                        SELECT COUNT(*) 
                        FROM information_schema.TABLE_CONSTRAINTS 
                        WHERE CONSTRAINT_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'users' 
                        AND CONSTRAINT_NAME = 'chk_role'
                    );
                """))
                result = db.execute(text("SELECT @constraint_exists as exists")).fetchone()
                if result and result.exists:
                    db.execute(text("ALTER TABLE users DROP CHECK chk_role"))
                    logger.info("Dropped chk_role constraint to allow blue_team role")
            except Exception as constraint_err:
                logger.debug(f"Could not drop constraint (may not exist): {constraint_err}")
            
            # Now update the role
            db.execute(
                text("UPDATE users SET role = :new_role WHERE id = :user_id"),
                {"new_role": new_role_str, "user_id": user_id}
            )
            db.commit()
            
            # Refresh user object
            db.refresh(user)
            
            logger.info(f"User {user.username} role changed from {old_role_str} to {new_role_str}")
            return {"status": "success", "data": user.to_dict()}
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            raise ValidationError(f"Failed to update user role. Please run the migration script to update the database constraint: {str(e)}")


def get_blue_team_users():
    """Get all users with blue team role."""
    with db_transaction() as db:
        users = db.query(User).filter(User.role == UserRole.BLUE_TEAM).all()
        return {"status": "success", "data": [u.to_dict() for u in users]}


def get_robopets_analytics():
    """Get RoboPets analytics for blue team."""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    with db_transaction() as db:
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Robot statistics - calculate based on latest UserRobot action
        total_robots = db.query(func.count(Robot.id)).scalar() or 0
        
        # Get all robots and check their latest action
        all_robots = db.query(Robot.id).all()
        booked_count = 0
        available_count = 0
        maintenance_count = 0
        
        for (robot_id,) in all_robots:
            # Get latest action for this robot
            latest_action = (
                db.query(UserRobot)
                .filter(UserRobot.robot_id == robot_id)
                .order_by(UserRobot.id.desc())
                .first()
            )
            
            if latest_action:
                if latest_action.action == UserRobotAction.PICK:
                    booked_count += 1
                elif latest_action.action == UserRobotAction.RETURN:
                    available_count += 1
            else:
                # Robot has never been picked, so it's available
                available_count += 1
        
        # Check maintenance status from Robot.status field if it exists
        try:
            maintenance_robots = db.query(func.count(Robot.id)).filter(Robot.status == "maintenance").scalar() or 0
        except:
            maintenance_robots = 0
        
        booked_robots = booked_count
        available_robots = available_count
        
        # Status breakdown
        status_dict = {
            "available": available_robots,
            "booked": booked_robots,
            "maintenance": maintenance_robots
        }
        
        # Booking statistics
        total_bookings = db.query(func.count(UserRobot.id)).scalar() or 0
        bookings_24h = db.query(func.count(UserRobot.id)).filter(UserRobot.created_at >= last_24h).scalar() or 0
        bookings_7d = db.query(func.count(UserRobot.id)).filter(UserRobot.created_at >= last_7d).scalar() or 0
        
        # Active users with robots
        active_users_with_robots = db.query(func.count(func.distinct(UserRobot.user_id))).filter(
            UserRobot.action == UserRobotAction.PICK,
            UserRobot.created_at >= last_7d
        ).scalar() or 0
        
        # Booking timeline (last 7 days)
        booking_timeline = []
        for i in range(7):
            day_start = now - timedelta(days=6-i)
            day_end = day_start + timedelta(days=1)
            count = db.query(func.count(UserRobot.id)).filter(
                UserRobot.created_at >= day_start,
                UserRobot.created_at < day_end
            ).scalar() or 0
            booking_timeline.append({
                "date": day_start.strftime("%m/%d"),
                "count": count
            })
        
        # Popular robots (most booked)
        popular_robots_query = db.query(
            Robot.id,
            Robot.name,
            func.count(UserRobot.id).label('booking_count')
        ).join(
            UserRobot, Robot.id == UserRobot.robot_id
        ).group_by(
            Robot.id, Robot.name
        ).order_by(
            func.count(UserRobot.id).desc()
        ).limit(10).all()
        
        popular_robots = [
            {
                "id": r[0],
                "name": r[1],
                "booking_count": r[2]
            }
            for r in popular_robots_query
        ]
        
        return {
            "status": "success",
            "data": {
                "total_robots": total_robots,
                "available_robots": available_robots,
                "booked_robots": booked_robots,
                "maintenance_robots": maintenance_robots,
                "status_breakdown": status_dict,
                "total_bookings": total_bookings,
                "bookings_24h": bookings_24h,
                "bookings_7d": bookings_7d,
                "active_users_with_robots": active_users_with_robots,
                "booking_timeline": booking_timeline,
                "popular_robots": popular_robots
            }
        }


def get_gcp_logs(limit: int = 50, severity: str = None, service: str = None):
    """Get GCP logs for blue team (real-time)."""
    try:
        from google.cloud import logging as cloud_logging
        import os
        from datetime import datetime, timedelta
        
        # Get project ID
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            # Try to extract from connection name
            connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME", "")
            if connection_name and ":" in connection_name:
                project_id = connection_name.split(":")[0]
        
        if not project_id:
            raise ValueError("Could not determine GCP project ID")
        
        # Initialize Cloud Logging client
        client = cloud_logging.Client(project=project_id)
        
        # Build filter
        filter_str = f'resource.type="gae_app"'
        
        if service:
            filter_str += f' AND resource.labels.module_id="{service}"'
        else:
            filter_str += ' AND resource.labels.module_id="default"'
        
        if severity:
            filter_str += f' AND severity>="{severity}"'
        
        # Get logs from last 24 hours
        entries = client.list_entries(
            filter_=filter_str,
            max_results=limit,
            order_by=cloud_logging.DESCENDING
        )
        
        logs = []
        for entry in entries:
            log_data = {
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else datetime.utcnow().isoformat(),
                "severity": entry.severity or "INFO",
                "message": entry.payload if isinstance(entry.payload, str) else str(entry.payload),
                "service": entry.resource.labels.get("module_id", "default"),
                "details": {}
            }
            
            # Add additional metadata
            if hasattr(entry, 'labels') and entry.labels:
                log_data["details"]["labels"] = dict(entry.labels)
            
            # Handle http_request (can be dict or object)
            if hasattr(entry, 'http_request') and entry.http_request:
                http_req = entry.http_request
                if isinstance(http_req, dict):
                    log_data["details"]["http_request"] = {
                        "method": http_req.get("requestMethod", ""),
                        "url": http_req.get("requestUrl", ""),
                        "status": http_req.get("status", "")
                    }
                else:
                    # It's an object
                    log_data["details"]["http_request"] = {
                        "method": getattr(http_req, 'request_method', getattr(http_req, 'requestMethod', '')),
                        "url": getattr(http_req, 'request_url', getattr(http_req, 'requestUrl', '')),
                        "status": getattr(http_req, 'status', '')
                    }
            
            # Handle source_location
            if hasattr(entry, 'source_location') and entry.source_location:
                source = entry.source_location
                if isinstance(source, dict):
                    log_data["details"]["source"] = {
                        "file": source.get("file", ""),
                        "line": source.get("line", ""),
                        "function": source.get("function", "")
                    }
                else:
                    log_data["details"]["source"] = {
                        "file": getattr(source, 'file', ''),
                        "line": getattr(source, 'line', ''),
                        "function": getattr(source, 'function', '')
                    }
            
            logs.append(log_data)
        
        return {"status": "success", "data": logs}
    
    except ImportError:
        logger.error("Google Cloud Logging not available")
        return {
            "status": "error",
            "error": "Google Cloud Logging library not installed"
        }
    except Exception as e:
        logger.error(f"Error fetching GCP logs: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Failed to fetch GCP logs: {str(e)}"
        }

