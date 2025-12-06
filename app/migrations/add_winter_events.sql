-- Winter Events Table
-- Manual tracking of winter events (storms) for reporting and billing purposes
-- Controlled by Managers and Admins

CREATE TABLE IF NOT EXISTS winter_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,

    -- Event Details
    event_name VARCHAR(255) NOT NULL,
    description TEXT NULL,

    -- Time Period
    start_date DATETIME NOT NULL,
    end_date DATETIME NULL,

    -- Status
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',

    -- Metadata
    created_by INT NULL COMMENT 'User ID who created the event',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign Keys
    CONSTRAINT fk_winter_events_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_winter_events_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,

    -- Indexes
    INDEX idx_tenant_status (tenant_id, status),
    INDEX idx_tenant_dates (tenant_id, start_date, end_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add winter_event_id to winter_ops_logs table
ALTER TABLE winter_ops_logs ADD COLUMN winter_event_id INT NULL AFTER tenant_id;
ALTER TABLE winter_ops_logs ADD CONSTRAINT fk_winter_ops_logs_event
    FOREIGN KEY (winter_event_id) REFERENCES winter_events(id) ON DELETE SET NULL;
CREATE INDEX idx_winter_ops_logs_event ON winter_ops_logs(winter_event_id);
