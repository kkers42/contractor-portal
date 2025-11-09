-- Migration: Create green_services_logs table
-- Date: 2025-11-03
-- Description: Creates the green_services_logs table for tracking lawn/landscaping service operations

CREATE TABLE IF NOT EXISTS green_services_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    subcontractor_name VARCHAR(255) NOT NULL,
    time_in DATETIME NOT NULL,
    time_out DATETIME NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    products_used VARCHAR(255) NULL,
    quantity_used DECIMAL(10, 2) DEFAULT 0,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES locations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
