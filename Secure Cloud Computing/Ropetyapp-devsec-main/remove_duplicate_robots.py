"""Script to remove duplicate robots from the database.

This script finds robots with duplicate names (or name+photo_url combinations),
keeps the one with the lowest ID, updates all user_robots references to point
to the kept robot, and deletes the duplicates.
"""

import logging
from collections import defaultdict
from db_session import init_db, get_db, close_db
from models import Robot, UserRobot
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_duplicate_robots():
    """Find duplicate robots grouped by name."""
    db = get_db()
    try:
        # Get all robots
        all_robots = db.query(Robot).order_by(Robot.id).all()
        
        # Group by name (case-insensitive)
        robots_by_name = defaultdict(list)
        for robot in all_robots:
            robots_by_name[robot.name.lower()].append(robot)
        
        # Find duplicates (groups with more than 1 robot)
        duplicates = {}
        for name, robots in robots_by_name.items():
            if len(robots) > 1:
                duplicates[name] = robots
                logger.info(f"Found {len(robots)} duplicates for robot name '{robots[0].name}'")
        
        return duplicates
    finally:
        db.close()


def remove_duplicates(dry_run=True):
    """Remove duplicate robots, keeping the one with the lowest ID."""
    init_db()
    db = get_db()
    
    try:
        duplicates = find_duplicate_robots()
        
        if not duplicates:
            logger.info("No duplicate robots found!")
            return
        
        total_duplicates = sum(len(robots) - 1 for robots in duplicates.values())
        logger.info(f"\nFound {len(duplicates)} duplicate groups with {total_duplicates} duplicate robots to remove")
        
        if dry_run:
            logger.info("\n=== DRY RUN MODE - No changes will be made ===\n")
        
        removed_count = 0
        updated_references = 0
        
        for name, robots in duplicates.items():
            # Sort by ID to keep the oldest (lowest ID)
            robots.sort(key=lambda r: r.id)
            keep_robot = robots[0]
            duplicate_robots = robots[1:]
            
            logger.info(f"\nProcessing '{keep_robot.name}' (ID: {keep_robot.id})")
            logger.info(f"  Keeping: ID {keep_robot.id} (name: {keep_robot.name}, photo: {keep_robot.photo_url})")
            
            for dup_robot in duplicate_robots:
                logger.info(f"  Duplicate: ID {dup_robot.id} (name: {dup_robot.name}, photo: {dup_robot.photo_url})")
                
                # Count references in user_robots table
                ref_count = db.query(UserRobot).filter(UserRobot.robot_id == dup_robot.id).count()
                logger.info(f"    Has {ref_count} user_robot references")
                
                if not dry_run:
                    # Update all user_robots references to point to the kept robot
                    if ref_count > 0:
                        updated = db.query(UserRobot).filter(
                            UserRobot.robot_id == dup_robot.id
                        ).update({UserRobot.robot_id: keep_robot.id})
                        updated_references += updated
                        logger.info(f"    Updated {updated} user_robot references to point to robot ID {keep_robot.id}")
                    
                    # Delete the duplicate robot
                    db.delete(dup_robot)
                    removed_count += 1
                    logger.info(f"    Deleted duplicate robot ID {dup_robot.id}")
        
        if not dry_run:
            db.commit()
            logger.info(f"\n=== COMPLETED ===")
            logger.info(f"Removed {removed_count} duplicate robots")
            logger.info(f"Updated {updated_references} user_robot references")
        else:
            logger.info(f"\n=== DRY RUN COMPLETE ===")
            logger.info(f"Would remove {total_duplicates} duplicate robots")
            logger.info("Run with dry_run=False to actually remove duplicates")
        
    except Exception as e:
        if not dry_run:
            db.rollback()
        logger.error(f"Error removing duplicates: {e}", exc_info=True)
        raise
    finally:
        db.close()
        close_db()


if __name__ == "__main__":
    import sys
    
    # Check if user wants to actually remove (not just dry run)
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        dry_run = False
        logger.warning("EXECUTE MODE: This will permanently delete duplicate robots!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Cancelled by user")
            sys.exit(0)
    else:
        logger.info("Running in DRY RUN mode. Use --execute to actually remove duplicates.")
    
    remove_duplicates(dry_run=dry_run)

