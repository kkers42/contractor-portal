-- Migration: Update green_services_logs to contractor/worker structure
-- Date: 2025-11-04
-- Description: Adds contractor fields and renames subcontractor_name to worker_name for consistency with winter_ops_logs

-- Add contractor_id and contractor_name columns
ALTER TABLE green_services_logs
ADD COLUMN contractor_id INT NULL AFTER property_id,
ADD COLUMN contractor_name VARCHAR(255) NULL AFTER contractor_id;

-- Rename subcontractor_name to worker_name for consistency
ALTER TABLE green_services_logs
CHANGE COLUMN subcontractor_name worker_name VARCHAR(255) NOT NULL;

-- Add foreign key constraint
ALTER TABLE green_services_logs
ADD CONSTRAINT fk_green_contractor
    FOREIGN KEY (contractor_id)
    REFERENCES users(id)
    ON DELETE SET NULL;

-- Add index for performance
CREATE INDEX idx_green_contractor_id ON green_services_logs(contractor_id);

-- Add index on worker_name for filtering
CREATE INDEX idx_green_worker_name ON green_services_logs(worker_name);
