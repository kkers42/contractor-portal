-- Create users and identities tables for OAuth support
-- Run this on production database

-- Create users table with OAuth support
CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) DEFAULT NULL,
  phone VARCHAR(20) DEFAULT NULL,
  username VARCHAR(100) DEFAULT NULL,
  email VARCHAR(255) NOT NULL,
  role ENUM('Admin','Manager','Contractor','Subcontractor','User') DEFAULT 'User',
  contractor_id INT DEFAULT NULL,
  password VARCHAR(255) DEFAULT NULL,
  password_hash VARCHAR(255) DEFAULT NULL,
  display_name VARCHAR(255) DEFAULT NULL,
  avatar_url VARCHAR(512) DEFAULT NULL,
  status ENUM('pending', 'active', 'suspended') DEFAULT 'pending' COMMENT 'pending = awaiting admin approval',
  last_login_at DATETIME DEFAULT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY unique_email (email),
  KEY idx_user_email (email),
  KEY idx_user_status (status),
  KEY idx_role (role),
  FOREIGN KEY (contractor_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Users and identities tables created successfully!' AS status;
