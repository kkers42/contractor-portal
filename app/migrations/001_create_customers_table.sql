-- Migration: Create customers table for multi-tenant architecture
-- Version: 0.6.0
-- Date: 2026-02-01

CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(9) UNIQUE NOT NULL COMMENT '9-character alphanumeric tenant identifier',
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address TEXT,
    status ENUM('active', 'suspended', 'cancelled') DEFAULT 'active',
    subscription_tier ENUM('free', 'basic', 'professional', 'enterprise') DEFAULT 'basic',
    max_users INT DEFAULT 10 COMMENT 'Maximum users allowed for this customer',
    max_properties INT DEFAULT 100 COMMENT 'Maximum properties allowed for this customer',
    features JSON COMMENT 'Feature flags: {"jobber": true, "quickbooks": true, "sms": false}',
    billing_email VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_company_name (company_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Multi-tenant customers table';

-- Create first customer from existing data
INSERT INTO customers (
    customer_id,
    company_name,
    contact_name,
    contact_email,
    status,
    subscription_tier,
    max_users,
    max_properties,
    features
) VALUES (
    'LEGACY001',
    'Initial Customer (Migrated)',
    'System Admin',
    'admin@contractor.local',
    'active',
    'enterprise',
    999,
    9999,
    '{"jobber": true, "quickbooks": true, "sms": true, "weather": true, "ai": true}'
);
