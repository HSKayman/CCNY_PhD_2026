-- Migration: Fix role enum case consistency
-- This ensures all role values in the database are lowercase to match Python enum values

USE ROBOPETY;

-- Update any uppercase role values to lowercase
-- Note: MySQL ENUM values are case-sensitive, but we want them lowercase
UPDATE users SET role = 'user' WHERE UPPER(role) = 'USER';
UPDATE users SET role = 'admin' WHERE UPPER(role) = 'ADMIN';

-- Verify all roles are lowercase
-- SELECT DISTINCT role FROM users;

