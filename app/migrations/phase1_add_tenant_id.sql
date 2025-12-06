-- Phase 1 SAAS Multi-Tenancy Migration
-- Add tenant_id to core tables

-- Add tenant_id to users table
ALTER TABLE users ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE users ADD CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_users_tenant ON users(tenant_id, id);

-- Add tenant_id to locations table
ALTER TABLE locations ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE locations ADD CONSTRAINT fk_locations_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_locations_tenant ON locations(tenant_id, id);

-- Add tenant_id to winter_logs table
ALTER TABLE winter_logs ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE winter_logs ADD CONSTRAINT fk_winter_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_winter_logs_tenant ON winter_logs(tenant_id, log_date);

-- Add tenant_id to green_logs table
ALTER TABLE green_logs ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE green_logs ADD CONSTRAINT fk_green_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_green_logs_tenant ON green_logs(tenant_id, log_date);

-- Add tenant_id to equipment_rates table
ALTER TABLE equipment_rates ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE equipment_rates ADD CONSTRAINT fk_equipment_rates_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_equipment_rates_tenant ON equipment_rates(tenant_id);

-- Add tenant_id to routes table
ALTER TABLE routes ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE routes ADD CONSTRAINT fk_routes_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_routes_tenant ON routes(tenant_id, id);

-- Add tenant_id to route_properties table
ALTER TABLE route_properties ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE route_properties ADD CONSTRAINT fk_route_properties_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- Add tenant_id to route_assignments table
ALTER TABLE route_assignments ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE route_assignments ADD CONSTRAINT fk_route_assignments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- Add tenant_id to property_lists table
ALTER TABLE property_lists ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE property_lists ADD CONSTRAINT fk_property_lists_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_property_lists_tenant ON property_lists(tenant_id);

-- Add tenant_id to property_list_items table
ALTER TABLE property_list_items ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE property_list_items ADD CONSTRAINT fk_property_list_items_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- Add tenant_id to tickets table
ALTER TABLE tickets ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE tickets ADD CONSTRAINT fk_tickets_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_tickets_tenant ON tickets(tenant_id, status);

-- Add tenant_id to api_keys table
ALTER TABLE api_keys ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE api_keys ADD CONSTRAINT fk_api_keys_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);

-- Add tenant_id to property_assignments table
ALTER TABLE property_assignments ADD COLUMN tenant_id INT NOT NULL DEFAULT 1 AFTER id;
ALTER TABLE property_assignments ADD CONSTRAINT fk_property_assignments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
