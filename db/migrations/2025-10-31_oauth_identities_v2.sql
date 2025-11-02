-- Migration: Add OAuth support and user status management
-- Date: 2025-10-31
-- Description: Adds name, status, display_name columns to users table and creates identities table for OAuth

-- Add new columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS name VARCHAR(255) DEFAULT NULL AFTER id,
ADD COLUMN IF NOT EXISTS status ENUM('pending', 'active', 'suspended') DEFAULT 'active' AFTER password,
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255) DEFAULT NULL AFTER status;

-- Create identities table for OAuth providers
CREATE TABLE IF NOT EXISTS identities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_provider_user (provider, provider_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Update existing users to have 'active' status if NULL
UPDATE users SET status = 'active' WHERE status IS NULL;

-- Populate name column from existing data if it's NULL (use email username part)
UPDATE users SET name = SUBSTRING_INDEX(email, '@', 1) WHERE name IS NULL OR name = '';
