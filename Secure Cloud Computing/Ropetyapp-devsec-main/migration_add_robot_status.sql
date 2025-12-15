-- Migration: Add robot status and management
-- Adds status, description, and metadata to robots table

ALTER TABLE robots
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'available',
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS category VARCHAR(100),
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Update existing robots to have status 'available' and is_active TRUE
UPDATE robots SET status = 'available', is_active = TRUE WHERE status IS NULL;

-- Add index for status filtering
CREATE INDEX IF NOT EXISTS idx_robot_status ON robots(status);
CREATE INDEX IF NOT EXISTS idx_robot_active ON robots(is_active);

