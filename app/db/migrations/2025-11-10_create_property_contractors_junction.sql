-- Migration: Create property_contractors junction table
-- Date: 2025-11-10
-- Description: Creates many-to-many relationship between properties and contractors

CREATE TABLE IF NOT EXISTS property_contractors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    contractor_id INT NOT NULL,
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES locations(id) ON DELETE CASCADE,
    FOREIGN KEY (contractor_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_assignment (property_id, contractor_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Index for faster queries
CREATE INDEX idx_property_id ON property_contractors(property_id);
CREATE INDEX idx_contractor_id ON property_contractors(contractor_id);
