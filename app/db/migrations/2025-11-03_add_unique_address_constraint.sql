-- Migration: Add unique constraint to locations.address
-- Date: 2025-11-03
-- Description: Prevents duplicate properties with same address

-- First, remove any existing duplicates (keep the oldest one)
DELETE t1 FROM locations t1
INNER JOIN locations t2
WHERE t1.id > t2.id
AND t1.address = t2.address;

-- Add unique constraint to address column
ALTER TABLE locations ADD UNIQUE KEY unique_address (address);
