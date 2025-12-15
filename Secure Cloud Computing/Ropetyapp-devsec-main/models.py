"""SQLAlchemy models for the RoboPety application."""
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    BLUE_TEAM = "blue_team"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive matching and legacy values."""
        if isinstance(value, str):
            value_lower = value.lower()
            # Map common variations
            if value_lower in ('user', 'users'):
                return cls.USER
            elif value_lower in ('admin', 'admins', 'administrator'):
                return cls.ADMIN
            elif value_lower in ('blue_team', 'blueteam', 'blue-team'):
                return cls.BLUE_TEAM
        return None


class UserRoleType(TypeDecorator):
    """Custom type to handle UserRole enum with case-insensitive matching."""
    impl = String
    cache_ok = True
    
    def __init__(self, length=20):
        super().__init__(length=length)
    
    def process_bind_param(self, value, dialect):
        """Convert enum to string for database storage."""
        if value is None:
            return None
        if isinstance(value, UserRole):
            return value.value
        if isinstance(value, str):
            return value.lower()
        return str(value).lower()
    
    def process_result_value(self, value, dialect):
        """Convert database string to enum."""
        if value is None:
            return None
        if isinstance(value, UserRole):
            return value
        # Try to match the value (case-insensitive)
        value_lower = str(value).lower()
        for role in UserRole:
            if role.value.lower() == value_lower:
                return role
        # Fallback: try to create from string
        try:
            return UserRole(value_lower)
        except ValueError:
            # If all else fails, return USER as default
            return UserRole.USER


class UserRobotAction(str, Enum):
    """User robot action enumeration."""
    PICK = "pick"
    RETURN = "return"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(UserRoleType(length=20), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, nullable=False, default=0)
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    two_factor_backup_codes = Column(Text, nullable=True)
    
    # Relationships
    user_robots = relationship("UserRobot", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def _role(self):
        """Get role as string value."""
        return self.role.value if isinstance(self.role, UserRole) else str(self.role)
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self._role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count or 0,
        }


class RobotStatus(str, Enum):
    """Robot status enumeration."""
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class Robot(Base):
    """Robot model."""
    __tablename__ = "robots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    photo_url = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="available")
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_robots = relationship("UserRobot", back_populates="robot", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert robot to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "photo_url": self.photo_url,
            "status": self.status,
            "description": self.description,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserRobot(Base):
    """User robot relationship model."""
    __tablename__ = "user_robots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    robot_id = Column(Integer, ForeignKey("robots.id"), nullable=False)
    action = Column(SQLEnum(UserRobotAction, native_enum=False, length=10), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_robots")
    robot = relationship("Robot", back_populates="user_robots")
    
    def to_dict(self):
        """Convert user robot to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "robot_id": self.robot_id,
            "action": self.action.value if isinstance(self.action, UserRobotAction) else str(self.action),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "robot_name": self.robot.name if self.robot else None,
        }


class Alert(Base):
    """Alert model for admin messages to users."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(500), nullable=False)
    read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "read": self.read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatMessage(Base):
    """Chat message model for user-admin communication."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(1000), nullable=False)
    is_from_admin = Column(Boolean, nullable=False, default=False)
    read_by_user = Column(Boolean, nullable=False, default=False)
    read_by_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    
    def to_dict(self):
        """Convert chat message to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "is_from_admin": self.is_from_admin,
            "read_by_user": self.read_by_user,
            "read_by_admin": self.read_by_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "username": self.user.username if self.user else None,
        }


class Announcement(Base):
    """Announcement model for admin broadcasts to all users."""
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert announcement to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserActivityLog(Base):
    """User activity log model for tracking user actions."""
    __tablename__ = "user_activity_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    def to_dict(self):
        """Convert activity log to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_type": self.activity_type,
            "description": self.description,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "username": self.user.username if self.user else None,
        }


class SecurityEvent(Base):
    """Security event model for tracking security incidents and attacks."""
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)  # e.g., "failed_login", "suspicious_activity", "attack_detected"
    severity = Column(String(20), nullable=False, default="low")  # low, medium, high, critical
    description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_agent = Column(String(500), nullable=True)
    event_metadata = Column(Text, nullable=True)  # JSON string for additional data
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_response = Column(Text, nullable=True)  # Admin's response/notes about the threat
    admin_responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    def to_dict(self):
        """Convert security event to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "ip_address": self.ip_address,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "user_agent": self.user_agent,
            "event_metadata": self.event_metadata,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "admin_response": self.admin_response,
            "admin_responded_at": self.admin_responded_at.isoformat() if self.admin_responded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
