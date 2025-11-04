-- Migration: Add contractor fields to winter_ops_logs
-- Date: 2025-11-03
-- Description: Adds contractor_id and contractor_name to track both contractor and subcontractor

-- Add contractor fields
ALTER TABLE winter_ops_logs
ADD COLUMN contractor_id INT NULL AFTER property_id,
ADD COLUMN contractor_name VARCHAR(255) NULL AFTER contractor_id;

-- Add foreign key for contractor
ALTER TABLE winter_ops_logs
ADD CONSTRAINT fk_winter_contractor
    FOREIGN KEY (contractor_id)
    REFERENCES users(id)
    ON DELETE SET NULL;

-- Add index for contractor lookups
CREATE INDEX idx_winter_contractor_id ON winter_ops_logs(contractor_id);

-- Rename subcontractor_name to worker_name for clarity
ALTER TABLE winter_ops_logs
CHANGE COLUMN subcontractor_name worker_name VARCHAR(255) NOT NULL;
