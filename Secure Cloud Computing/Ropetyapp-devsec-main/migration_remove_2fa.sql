-- Migration: Remove 2FA (TOTP) support from users table
-- Run this migration to remove two-factor authentication support

-- Drop index first
DROP INDEX IF EXISTS idx_users_totp_enabled ON users;

-- Remove TOTP columns
ALTER TABLE users 
DROP COLUMN IF EXISTS totp_secret,
DROP COLUMN IF EXISTS totp_enabled;

