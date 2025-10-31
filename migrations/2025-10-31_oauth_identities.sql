-- OAuth Identities Migration
-- Run this to add identity support to your existing database

-- Update users table to support OAuth
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(512),
ADD COLUMN IF NOT EXISTS last_login_at DATETIME,
ADD COLUMN IF NOT EXISTS created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS status ENUM('pending', 'active', 'suspended') DEFAULT 'pending' COMMENT 'pending = awaiting admin approval';

-- Create identities table for OAuth providers
CREATE TABLE IF NOT EXISTS identities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    provider VARCHAR(50) NOT NULL COMMENT 'google, microsoft, etc',
    subject VARCHAR(255) NOT NULL COMMENT 'OAuth provider user ID',
    email VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_provider_subject (provider, subject),
    KEY idx_user_id (user_id),
    KEY idx_email (email),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_status ON users(status);

-- Update existing users to be 'active' if they don't have a status
UPDATE users SET status = 'active' WHERE status IS NULL OR status = '';
