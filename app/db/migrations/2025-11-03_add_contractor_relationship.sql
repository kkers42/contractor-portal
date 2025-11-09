-- Migration: Add contractor relationship to users table
-- Date: 2025-11-03
-- Description: Adds contractor_id to link subcontractors to their contractor (manager)

-- Add contractor_id column to users table
ALTER TABLE users
ADD COLUMN contractor_id INT NULL AFTER role,
ADD CONSTRAINT fk_contractor
    FOREIGN KEY (contractor_id)
    REFERENCES users(id)
    ON DELETE SET NULL;

-- Add index for contractor lookups
CREATE INDEX idx_contractor_id ON users(contractor_id);

-- Update existing Manager users to be Contractors (role change will be done in app)
-- Subcontractors will be linked to their Manager (now Contractor) by contractor_id
