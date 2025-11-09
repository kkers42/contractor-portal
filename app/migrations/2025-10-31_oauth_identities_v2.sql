-- OAuth Identities Migration (MySQL 9.2 Compatible)
-- Run this to add identity support to your existing database

-- Update users table to support OAuth (check if columns exist first)
SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND column_name = 'display_name'
    ) > 0,
    'SELECT 1',
    'ALTER TABLE users ADD COLUMN display_name VARCHAR(255)'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND column_name = 'avatar_url'
    ) > 0,
    'SELECT 1',
    'ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND column_name = 'last_login_at'
    ) > 0,
    'SELECT 1',
    'ALTER TABLE users ADD COLUMN last_login_at DATETIME'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND column_name = 'created_at'
    ) > 0,
    'SELECT 1',
    'ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND column_name = 'updated_at'
    ) > 0,
    'SELECT 1',
    'ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND column_name = 'status'
    ) > 0,
    'SELECT 1',
    'ALTER TABLE users ADD COLUMN status ENUM(''pending'', ''active'', ''suspended'') DEFAULT ''pending'' COMMENT ''pending = awaiting admin approval'''
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

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

-- Add indexes for faster lookups (skip if already exists)
SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND index_name = 'idx_user_email'
    ) > 0,
    'SELECT 1',
    'CREATE INDEX idx_user_email ON users(email)'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE table_name = 'users'
        AND table_schema = DATABASE()
        AND index_name = 'idx_user_status'
    ) > 0,
    'SELECT 1',
    'CREATE INDEX idx_user_status ON users(status)'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Update existing users to be 'active' if they don't have a status
-- This will only work if the status column was just added
UPDATE users SET status = 'active' WHERE status = 'pending' OR status IS NULL;

SELECT 'OAuth migration completed successfully!' AS status;
