#!/usr/bin/env python3
"""Quick script to create admin user using pymysql."""
import pymysql
import bcrypt
import os
import re

# Read database configuration from app.yaml
def get_config_from_app_yaml():
    """Extract database config from app.yaml."""
    config = {
        'host': '127.0.0.1',
        'port': 3310,
        'user': 'root',
        'password': '',
        'database': 'ROBOPETY',
        'charset': 'utf8mb4'
    }
    
    if os.path.exists('app.yaml'):
        with open('app.yaml', 'r') as f:
            content = f.read()
            
            # Extract CLOUD_SQL_PASSWORD
            password_match = re.search(r'CLOUD_SQL_PASSWORD:\s*["\']?([^"\']+)["\']?', content)
            if password_match:
                config['password'] = password_match.group(1).strip()
            
            # Extract CLOUD_SQL_DATABASE_NAME
            db_match = re.search(r'CLOUD_SQL_DATABASE_NAME:\s*["\']?([^"\']+)["\']?', content)
            if db_match:
                config['database'] = db_match.group(1).strip()
    
    # Fallback to environment variables
    config['password'] = config['password'] or os.environ.get('CLOUD_SQL_PASSWORD', '')
    config['database'] = config['database'] or os.environ.get('CLOUD_SQL_DATABASE_NAME', 'ROBOPETY')
    
    return config

DB_CONFIG = get_config_from_app_yaml()

def create_admin():
    """Create admin user."""
    try:
        print(f"Connecting to database...")
        print(f"  Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print(f"  User: {DB_CONFIG['user']}")
        print(f"  Password: {'*' * len(DB_CONFIG['password'])} ({len(DB_CONFIG['password'])} chars)")
        
        if not DB_CONFIG['password']:
            print("✗ ERROR: Database password is empty! Check app.yaml or CLOUD_SQL_PASSWORD environment variable.")
            return
        
        connection = pymysql.connect(**DB_CONFIG)
        
        try:
            with connection.cursor() as cursor:
                # Check if admin already exists
                cursor.execute("SELECT id FROM users WHERE email = 'theoneandonly@gmail.com'")
                if cursor.fetchone():
                    print("Admin user already exists!")
                    return
                
                # Generate password hash
                password = "theoneandonly"
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                print("Creating admin user...")
                cursor.execute("""
                    INSERT INTO users (username, email, password, role, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, ('Admin', 'theoneandonly@gmail.com', password_hash, 'admin'))
                
                connection.commit()
                
                print("✓ Admin user created successfully!")
                print("\nAdmin Credentials:")
                print("  Username: Admin")
                print("  Email: theoneandonly@gmail.com")
                print("  Password: theoneandonly")
                
        finally:
            connection.close()
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    create_admin()


