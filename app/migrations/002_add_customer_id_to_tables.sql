-- Migration: Add customer_id to all existing tables
-- Version: 0.6.0
-- Date: 2026-02-01

-- Add customer_id to users table
ALTER TABLE users
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_users_customer_id (customer_id),
ADD FOREIGN KEY fk_users_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to locations (properties) table
ALTER TABLE locations
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_locations_customer_id (customer_id),
ADD FOREIGN KEY fk_locations_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to winter_ops_logs table
ALTER TABLE winter_ops_logs
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_winter_ops_logs_customer_id (customer_id),
ADD FOREIGN KEY fk_winter_ops_logs_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to winter_events table
ALTER TABLE winter_events
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_winter_events_customer_id (customer_id),
ADD FOREIGN KEY fk_winter_events_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to property_contractors table
ALTER TABLE property_contractors
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_property_contractors_customer_id (customer_id),
ADD FOREIGN KEY fk_property_contractors_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to routes table
ALTER TABLE routes
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_routes_customer_id (customer_id),
ADD FOREIGN KEY fk_routes_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to property_lists table
ALTER TABLE property_lists
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_property_lists_customer_id (customer_id),
ADD FOREIGN KEY fk_property_lists_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to equipment_rates table (if exists)
ALTER TABLE equipment_rates
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_equipment_rates_customer_id (customer_id),
ADD FOREIGN KEY fk_equipment_rates_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to weather_data table (if exists)
ALTER TABLE weather_data
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_weather_data_customer_id (customer_id),
ADD FOREIGN KEY fk_weather_data_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to sms_context table
ALTER TABLE sms_context
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_sms_context_customer_id (customer_id),
ADD FOREIGN KEY fk_sms_context_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to api_keys table
ALTER TABLE api_keys
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_api_keys_customer_id (customer_id),
ADD FOREIGN KEY fk_api_keys_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to jobber_auth table (if exists)
ALTER TABLE jobber_auth
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_jobber_auth_customer_id (customer_id),
ADD FOREIGN KEY fk_jobber_auth_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to quickbooks_auth table (if exists)
ALTER TABLE quickbooks_auth
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_quickbooks_auth_customer_id (customer_id),
ADD FOREIGN KEY fk_quickbooks_auth_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Add customer_id to event_checkins table (if exists)
ALTER TABLE event_checkins
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'LEGACY001' COMMENT 'Customer tenant identifier',
ADD INDEX idx_event_checkins_customer_id (customer_id),
ADD FOREIGN KEY fk_event_checkins_customer (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;

-- Now remove the DEFAULT 'LEGACY001' constraint from all tables
-- This forces all future inserts to explicitly specify customer_id

ALTER TABLE users ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE locations ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE winter_ops_logs ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE winter_events ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE property_contractors ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE routes ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE property_lists ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE equipment_rates ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE weather_data ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE sms_context ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE api_keys ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE jobber_auth ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE quickbooks_auth ALTER COLUMN customer_id DROP DEFAULT;
ALTER TABLE event_checkins ALTER COLUMN customer_id DROP DEFAULT;
