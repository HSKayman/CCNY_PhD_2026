"""SQLAlchemy database session management."""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from secrets_manager import (
    get_db_user,
    get_db_password,
    get_db_name,
    get_db_connection_name,
)

logger = logging.getLogger(__name__)

# Global session factory
SessionLocal = None
engine = None


def init_db():
    """Initialize database connection."""
    global SessionLocal, engine
    
    db_user = get_db_user()
    db_password = get_db_password()
    db_name = get_db_name()
    db_connection_name = get_db_connection_name()
    
    if not all([db_user, db_password, db_name, db_connection_name]):
        raise RuntimeError(
            "Database configuration missing required environment variables or secrets"
        )
    
    # Use Unix socket for Cloud SQL (secure, encrypted by default)
    unix_socket = f"/cloudsql/{db_connection_name}"
    
    # SQLAlchemy connection string for Cloud SQL with SSL/TLS enforcement
    # Note: Unix sockets are already encrypted by Cloud SQL, but we add SSL parameters
    # for additional security and to satisfy Cloud SQL security requirements
    database_url = (
        f"mysql+pymysql://{db_user}:{db_password}@/{db_name}"
        f"?unix_socket={unix_socket}"
        f"&ssl_disabled=false"  # Enable SSL (Unix sockets are already encrypted, but this ensures SSL is used)
        f"&ssl_verify_cert=false"  # Don't verify cert for Unix socket connections (Cloud SQL handles this)
    )
    
    try:
        engine = create_engine(
            database_url,
            poolclass=NullPool,  # Cloud SQL proxy handles connection pooling
            echo=False,  # Set to True for SQL debugging
        )
        SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )
        
        # Create tables if they don't exist (including alerts table)
        try:
            from models import Base
            Base.metadata.create_all(bind=engine, checkfirst=True)
            logger.info("Database tables verified/created successfully")
        except Exception as e:
            logger.warning(f"Could not create tables automatically: {e}")
            logger.warning("Tables should be created via migration scripts")
        
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_db():
    """Get database session (dependency injection)."""
    if SessionLocal is None:
        init_db()
    return SessionLocal()


def close_db():
    """Close database session."""
    if SessionLocal:
        SessionLocal.remove()

