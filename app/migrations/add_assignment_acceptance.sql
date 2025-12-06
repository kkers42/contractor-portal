-- Assignment Acceptance Workflow
-- Adds acceptance status for property assignments and route assignments
-- Contractors must accept assignments before starting work

-- Add acceptance fields to property_contractors table
ALTER TABLE property_contractors
ADD COLUMN acceptance_status ENUM('pending', 'accepted', 'declined') DEFAULT 'pending' AFTER contractor_id;

ALTER TABLE property_contractors
ADD COLUMN accepted_at DATETIME NULL AFTER acceptance_status;

ALTER TABLE property_contractors
ADD COLUMN declined_at DATETIME NULL AFTER accepted_at;

-- Add index for filtering by acceptance status
CREATE INDEX idx_property_contractors_status ON property_contractors(acceptance_status);

-- Add acceptance fields to route_assignments table
ALTER TABLE route_assignments
ADD COLUMN acceptance_status ENUM('pending', 'accepted', 'declined') DEFAULT 'pending' AFTER user_id;

ALTER TABLE route_assignments
ADD COLUMN accepted_at DATETIME NULL AFTER acceptance_status;

ALTER TABLE route_assignments
ADD COLUMN declined_at DATETIME NULL AFTER accepted_at;

-- Add current_property_id to track which property user is working on in a route
ALTER TABLE route_assignments
ADD COLUMN current_property_id INT NULL AFTER declined_at;

ALTER TABLE route_assignments
ADD COLUMN current_property_started_at DATETIME NULL AFTER current_property_id;

-- Add index for filtering by acceptance status
CREATE INDEX idx_route_assignments_status ON route_assignments(acceptance_status);

-- Create assignment_history table to track acceptance/decline history
CREATE TABLE IF NOT EXISTS assignment_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,

    -- Assignment Details
    assignment_type ENUM('property', 'route') NOT NULL,
    assignment_id INT NOT NULL COMMENT 'property_contractors.id or route_assignments.id',
    user_id INT NOT NULL,
    property_id INT NULL COMMENT 'For property assignments',
    route_id INT NULL COMMENT 'For route assignments',

    -- Action Details
    action ENUM('assigned', 'accepted', 'declined', 'started', 'completed') NOT NULL,
    action_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NULL,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    CONSTRAINT fk_assignment_history_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_assignment_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_assignment_history_type (assignment_type, assignment_id),
    INDEX idx_assignment_history_user (user_id),
    INDEX idx_assignment_history_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
