-- Migration: Add billing type fields to locations table
-- This allows properties to have billing based on hourly rate OR per occurrence rates

-- Add billing_type column (hourly or per_occurrence)
ALTER TABLE locations ADD COLUMN billing_type ENUM('hourly', 'per_occurrence') DEFAULT 'hourly';

-- Add per-occurrence pricing columns
ALTER TABLE locations ADD COLUMN plow_rate DECIMAL(10, 2) DEFAULT NULL COMMENT 'Per occurrence rate for plowing';
ALTER TABLE locations ADD COLUMN salt_rate DECIMAL(10, 2) DEFAULT NULL COMMENT 'Per occurrence rate for salting';
ALTER TABLE locations ADD COLUMN sidewalk_deice_rate DECIMAL(10, 2) DEFAULT NULL COMMENT 'Per occurrence rate for sidewalk de-icing';
ALTER TABLE locations ADD COLUMN sidewalk_snow_rate DECIMAL(10, 2) DEFAULT NULL COMMENT 'Per occurrence rate for sidewalk snow removal';
