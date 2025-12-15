-- Migration script to add blue_team role to users table
-- Run this before deploying the new code

USE ROBOPETY;

-- Drop existing check constraint if it exists (MySQL 8.0.19+)
-- For older MySQL versions, manually drop: ALTER TABLE users DROP CHECK chk_role;
SET @constraint_exists = (
    SELECT COUNT(*) 
    FROM information_schema.TABLE_CONSTRAINTS 
    WHERE CONSTRAINT_SCHEMA = 'ROBOPETY' 
    AND TABLE_NAME = 'users' 
    AND CONSTRAINT_NAME = 'chk_role'
);

SET @sql = IF(@constraint_exists > 0, 
    'ALTER TABLE users DROP CHECK chk_role', 
    'SELECT "Constraint does not exist"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Modify role column to include 'blue_team' option
-- Note: This will fail if column doesn't exist - run migration_add_role.sql first
ALTER TABLE users 
MODIFY COLUMN role ENUM('user', 'admin', 'blue_team') NOT NULL DEFAULT 'user';

-- Recreate check constraint to allow all three roles (optional, ENUM already enforces this)
-- ALTER TABLE users 
-- ADD CONSTRAINT chk_role CHECK (role IN ('user', 'admin', 'blue_team'));

-- Create security_events table for tracking security incidents
CREATE TABLE IF NOT EXISTS security_events (
    id INT NOT NULL AUTO_INCREMENT,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'low',
    description TEXT NOT NULL,
    ip_address VARCHAR(45) NULL,
    user_id INT NULL,
    user_agent VARCHAR(500) NULL,
    event_metadata TEXT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at DATETIME NULL,
    resolved_by INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_event_type (event_type),
    INDEX idx_severity (severity),
    INDEX idx_resolved (resolved),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

