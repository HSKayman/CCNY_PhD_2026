-- Migration to add 2FA (Two-Factor Authentication) fields to users table
-- Run this migration to enable 2FA functionality

USE ROBOPETY;

-- Add 2FA fields to users table
-- Note: If you get "Duplicate column name" error, the columns already exist and migration was already run

-- Add two_factor_enabled column
ALTER TABLE users 
ADD COLUMN two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE;

-- Add two_factor_secret column  
ALTER TABLE users
ADD COLUMN two_factor_secret VARCHAR(255) NULL;

-- Add two_factor_backup_codes column
ALTER TABLE users
ADD COLUMN two_factor_backup_codes TEXT NULL;

-- Create index for faster lookups (MySQL 5.7.4+ supports IF NOT EXISTS for CREATE INDEX)
CREATE INDEX IF NOT EXISTS idx_users_two_factor_enabled ON users(two_factor_enabled);

