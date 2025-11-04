-- Migration: Add equipment field to winter_ops_logs table
-- Date: 2025-11-03
-- Description: Adds equipment/service field to track what equipment was used

ALTER TABLE winter_ops_logs
ADD COLUMN equipment VARCHAR(255) NULL AFTER subcontractor_name;
