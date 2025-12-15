#!/usr/bin/env python3
"""Script to delete all users and create admin user."""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables if not set
os.environ.setdefault('CLOUD_SQL_USERNAME', 'root')
os.environ.setdefault('CLOUD_SQL_PASSWORD', '-6uB+6(7_bHPGmGu')
os.environ.setdefault('CLOUD_SQL_DATABASE_NAME', 'ROBOPETY')
os.environ.setdefault('CLOUD_SQL_CONNECTION_NAME', 'melodic-voice-475605-d2:us-central1:robo')
os.environ.setdefault('JWT_SECRET', 's3yPp7rV1iQe9kJw4ZxTnA2uB8LmF0cGhYdR5qKsO3vWbEtU')
os.environ.setdefault('BUCKET_NAME', 'robo-images-melodic-voice-475605-d2')

from db_session import init_db, get_db
from models import User, UserRole
from auth_utils import hash_password
from sqlalchemy import delete

def setup_admin():
    """Delete all users and create admin user."""
    print("Initializing database connection...")
    init_db()
    db = get_db()
    
    try:
        # Delete all existing users
        print("Deleting all existing users...")
        deleted_count = db.query(User).count()
        db.execute(delete(User))
        db.commit()
        print(f"✓ Deleted {deleted_count} user(s)")
        
        # Create admin user
        print("Creating admin user...")
        admin_password = hash_password("theoneandonly")
        
        admin_user = User(
            email="theoneandonly@gmail.com",
            username="Admin",
            password=admin_password,
            role=UserRole.ADMIN
        )
        db.add(admin_user)
        db.commit()
        
        print("✓ Admin user created successfully!")
        print("\nAdmin Credentials:")
        print("  Username: Admin")
        print("  Email: theoneandonly@gmail.com")
        print("  Password: theoneandonly")
        print("\nYou can now login at: /login")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_admin()

