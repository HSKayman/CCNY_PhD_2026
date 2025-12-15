#!/usr/bin/env python3
"""Update admin password hash - run after deployment when packages are available."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_session import init_db, get_db
from models import User
from auth_utils import hash_password

def update_admin_hash():
    """Update admin user password hash."""
    init_db()
    db = get_db()
    
    try:
        admin = db.query(User).filter(User.email == 'theoneandonly@gmail.com').first()
        if not admin:
            print("Admin user not found!")
            return
        
        print("Updating admin password hash...")
        admin.password = hash_password("theoneandonly")
        db.commit()
        
        print("✓ Admin password hash updated successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_hash()


