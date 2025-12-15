-- Data migration script to fix role values for existing users
-- This converts the ENUM column to VARCHAR to avoid SQLAlchemy enum mapping issues
-- Run this AFTER migration_add_role_safe.sql or migration_add_role.sql

USE ROBOPETY;

-- Convert ENUM to VARCHAR to avoid SQLAlchemy enum name/value mapping issues
-- This allows SQLAlchemy to properly handle the enum values
ALTER TABLE users 
MODIFY COLUMN role VARCHAR(10) NOT NULL DEFAULT 'user';

-- Add a CHECK constraint to ensure only valid values
ALTER TABLE users 
ADD CONSTRAINT chk_role CHECK (role IN ('user', 'admin'));

-- Update any NULL or invalid role values to 'user' (default)
UPDATE users 
SET role = 'user' 
WHERE role IS NULL OR role NOT IN ('user', 'admin');

-- Verify: Show current role distribution
SELECT role, COUNT(*) as count FROM users GROUP BY role;

