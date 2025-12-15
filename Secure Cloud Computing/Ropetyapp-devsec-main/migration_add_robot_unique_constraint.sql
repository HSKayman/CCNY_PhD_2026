-- Migration to add unique constraint on robot name to prevent duplicates
-- Run this migration to enforce uniqueness at the database level

USE ROBOPETY;

-- Add unique constraint on robot name (case-sensitive)
-- Note: Application code also checks for case-insensitive duplicates
ALTER TABLE robots 
ADD UNIQUE INDEX idx_robots_name_unique (name);

