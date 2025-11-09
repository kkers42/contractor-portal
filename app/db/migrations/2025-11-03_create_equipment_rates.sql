-- Migration: Create equipment_rates table
-- Date: 2025-11-03
-- Description: Creates table to store hourly rates for each equipment type

CREATE TABLE IF NOT EXISTS equipment_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_name VARCHAR(255) NOT NULL UNIQUE,
    hourly_rate DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default equipment from SnowRemoval.html service dropdown
INSERT INTO equipment_rates (equipment_name, hourly_rate, description) VALUES
    ('Straight Blade Pickup', 85.00, 'Pickup truck with straight blade plow'),
    ('Plow truck w/ Bulk Spreader', 135.00, 'Plow truck with bulk salt spreader'),
    ('High Efficiency Plow w/ Bulk Spreader', 150.00, 'High efficiency plow with bulk spreader'),
    ('Large Plow Truck 4+yrd Bulk Spreader', 175.00, 'Large plow truck with 4+ yard bulk spreader'),
    ('Sidewalk Plow', 65.00, 'Sidewalk plow equipment'),
    ('Tractor small', 95.00, 'Small tractor for snow removal'),
    ('Loader no box', 125.00, 'Loader without pusher box'),
    ('Loader Box >10ft', 145.00, 'Loader with pusher box over 10ft'),
    ('Loader Box 11ft+', 165.00, 'Loader with pusher box 11ft or larger'),
    ('Sidewalk Snow Blower', 45.00, 'Snow blower for sidewalks'),
    ('Sidewalk Shovel', 25.00, 'Manual snow shoveling')
ON DUPLICATE KEY UPDATE equipment_name=equipment_name;
