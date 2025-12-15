#!/usr/bin/env python3
"""Simple script to remove duplicate robots using pymysql directly."""
import pymysql
import sys

# Database connection settings
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3310,
    'user': 'root',
    'password': '-6uB+6(7_bHPGmGupolivoliv67',
    'database': 'ROBOPETY',
    'charset': 'utf8mb4'
}

def find_duplicate_robots(cursor):
    """Find duplicate robots grouped by name."""
    # Get all robots ordered by ID
    cursor.execute("""
        SELECT id, name, photo_url, status, created_at
        FROM robots
        ORDER BY id
    """)
    all_robots = cursor.fetchall()
    
    # Group by name (case-insensitive)
    robots_by_name = {}
    for robot in all_robots:
        robot_id, name, photo_url, status, created_at = robot
        name_lower = name.lower()
        if name_lower not in robots_by_name:
            robots_by_name[name_lower] = []
        robots_by_name[name_lower].append(robot)
    
    # Find duplicates (groups with more than 1 robot)
    duplicates = {}
    for name_lower, robots in robots_by_name.items():
        if len(robots) > 1:
            duplicates[name_lower] = robots
    
    return duplicates

def remove_duplicates(dry_run=True):
    """Remove duplicate robots, keeping the one with the lowest ID."""
    try:
        print("Connecting to database...")
        connection = pymysql.connect(**DB_CONFIG)
        
        try:
            with connection.cursor() as cursor:
                duplicates = find_duplicate_robots(cursor)
                
                if not duplicates:
                    print("\n✓ No duplicate robots found!")
                    return
                
                total_duplicates = sum(len(robots) - 1 for robots in duplicates.values())
                print(f"\nFound {len(duplicates)} duplicate group(s) with {total_duplicates} duplicate robot(s) to remove")
                
                if dry_run:
                    print("\n=== DRY RUN MODE - No changes will be made ===\n")
                
                removed_count = 0
                updated_references = 0
                
                for name_lower, robots in duplicates.items():
                    # Sort by ID to keep the oldest (lowest ID)
                    robots.sort(key=lambda r: r[0])  # Sort by ID (first element)
                    keep_robot = robots[0]
                    duplicate_robots = robots[1:]
                    
                    keep_id, keep_name, keep_photo, keep_status, keep_created = keep_robot
                    print(f"\nProcessing '{keep_name}' (ID: {keep_id})")
                    print(f"  Keeping: ID {keep_id} (name: {keep_name}, photo: {keep_photo})")
                    
                    for dup_robot in duplicate_robots:
                        dup_id, dup_name, dup_photo, dup_status, dup_created = dup_robot
                        print(f"  Duplicate: ID {dup_id} (name: {dup_name}, photo: {dup_photo})")
                        
                        # Count references in user_robots table
                        cursor.execute("SELECT COUNT(*) FROM user_robots WHERE robot_id = %s", (dup_id,))
                        ref_count = cursor.fetchone()[0]
                        print(f"    Has {ref_count} user_robot reference(s)")
                        
                        if not dry_run:
                            # Update all user_robots references to point to the kept robot
                            if ref_count > 0:
                                cursor.execute("""
                                    UPDATE user_robots
                                    SET robot_id = %s
                                    WHERE robot_id = %s
                                """, (keep_id, dup_id))
                                updated = cursor.rowcount
                                updated_references += updated
                                print(f"    Updated {updated} user_robot reference(s) to point to robot ID {keep_id}")
                            
                            # Delete the duplicate robot
                            cursor.execute("DELETE FROM robots WHERE id = %s", (dup_id,))
                            removed_count += 1
                            print(f"    Deleted duplicate robot ID {dup_id}")
                
                if not dry_run:
                    connection.commit()
                    print(f"\n=== COMPLETED ===")
                    print(f"Removed {removed_count} duplicate robot(s)")
                    print(f"Updated {updated_references} user_robot reference(s)")
                else:
                    print(f"\n=== DRY RUN COMPLETE ===")
                    print(f"Would remove {total_duplicates} duplicate robot(s)")
                    print("Run with --execute to actually remove duplicates")
                
        finally:
            connection.close()
            
    except pymysql.Error as e:
        print(f"\n✗ Database error: {e}")
        print("\nMake sure:")
        print("  1. Cloud SQL Proxy is running on port 3310")
        print("  2. Database credentials are correct")
        raise
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise

if __name__ == "__main__":
    # Check if user wants to actually remove (not just dry run)
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        dry_run = False
        print("\n⚠️  EXECUTE MODE: This will permanently delete duplicate robots!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled by user")
            sys.exit(0)
    else:
        print("Running in DRY RUN mode. Use --execute to actually remove duplicates.")
    
    remove_duplicates(dry_run=dry_run)

