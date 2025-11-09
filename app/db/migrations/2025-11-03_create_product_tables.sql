-- Migration: Create product tables
-- Date: 2025-11-03
-- Description: Creates winter_products and landscape_products tables for tracking materials/supplies

-- Winter products table (salt, calcium chloride, etc.)
CREATE TABLE IF NOT EXISTS winter_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) NOT NULL COMMENT 'Unit of measurement (tons, bags, lbs, etc.)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Landscape/Green services products table (fertilizer, mulch, etc.)
CREATE TABLE IF NOT EXISTS landscape_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) NOT NULL COMMENT 'Unit of measurement (gallons, bags, yards, etc.)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert some default winter products
INSERT INTO winter_products (name, unit) VALUES
    ('Bulk Salt', 'tons'),
    ('Bagged Salt', 'bags'),
    ('Calcium Chloride', 'lbs')
ON DUPLICATE KEY UPDATE name=name;

-- Insert some default landscape products
INSERT INTO landscape_products (name, unit) VALUES
    ('Fertilizer', 'bags'),
    ('Mulch', 'yards'),
    ('Herbicide', 'gallons'),
    ('Seed', 'lbs')
ON DUPLICATE KEY UPDATE name=name;
