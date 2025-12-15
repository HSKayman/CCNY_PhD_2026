-- Migration script to add role column to users table
-- Run this before deploying the new code
-- Note: MySQL doesn't support IF NOT EXISTS in ALTER TABLE, so this script
-- should be run with error handling or after checking if columns exist

USE ROBOPETY;

-- Add role column with default value 'user'
-- Note: This will fail if column already exists - that's okay, just means migration was already run
ALTER TABLE users 
ADD COLUMN role ENUM('user', 'admin') NOT NULL DEFAULT 'user';

-- Add created_at timestamp column to users
ALTER TABLE users 
ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Add created_at timestamp column to user_robots
ALTER TABLE user_robots 
ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Optionally, set a default admin user (change password after first login!)
-- UPDATE users SET role = 'admin' WHERE username = 'admin' LIMIT 1;
