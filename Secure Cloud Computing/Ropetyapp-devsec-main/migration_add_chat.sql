-- Migration script to add chat_messages table
-- Run this before deploying the new code

USE ROBOPETY;

-- Create chat_messages table for user-admin communication
CREATE TABLE IF NOT EXISTS chat_messages (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    message VARCHAR(1000) NOT NULL,
    is_from_admin BOOLEAN NOT NULL DEFAULT FALSE,
    read_by_user BOOLEAN NOT NULL DEFAULT FALSE,
    read_by_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_read_by_admin (read_by_admin),
    INDEX idx_read_by_user (read_by_user)
);







