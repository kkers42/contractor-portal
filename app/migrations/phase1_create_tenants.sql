-- Phase 1 SAAS Multi-Tenancy Migration
-- Create tenants table for small-scale contractor companies
-- Constraints: 5 accounts max, 100 properties max, Manager level max

CREATE TABLE IF NOT EXISTS tenants (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Company Information
    company_name VARCHAR(255) NOT NULL UNIQUE,
    subdomain VARCHAR(100) NOT NULL UNIQUE,

    -- Contact Information
    admin_email VARCHAR(255) NOT NULL,
    admin_phone VARCHAR(50) NULL,

    -- Subscription Management (Simplified for Phase 1)
    subscription_status ENUM('active', 'suspended', 'trial') DEFAULT 'trial',
    trial_ends_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Phase 1 Limits (Fixed for small-scale)
    max_users INT DEFAULT 5,
    max_properties INT DEFAULT 100,
    max_user_role ENUM('User', 'Subcontractor', 'Manager') DEFAULT 'Manager',

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_subdomain (subdomain),
    INDEX idx_status (subscription_status),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create default tenant for existing installation (ID = 1)
INSERT INTO tenants (
    id, company_name, subdomain, admin_email,
    subscription_status, max_users, max_properties, max_user_role
) VALUES (
    1,
    'Primary Account',
    'primary',
    'admin@contractorportal.com',
    'active',
    9999,  -- Unlimited for primary account
    9999,  -- Unlimited for primary account
    'Manager'  -- Can have all roles including Admin
) ON DUPLICATE KEY UPDATE id=id;
