-- Migration: Create locations table for properties
-- Date: 2025-11-03
-- Description: Creates the locations table if it doesn't exist

CREATE TABLE IF NOT EXISTS locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    sqft INT NULL,
    area_manager VARCHAR(100) NULL,
    plow TINYINT(1) DEFAULT 0,
    salt TINYINT(1) DEFAULT 0,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
