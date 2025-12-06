-- SMS Support for Ticket Management
-- Adds phone numbers and SMS conversation tracking

-- Add phone number to users table
ALTER TABLE users
ADD COLUMN phone_number VARCHAR(20) NULL AFTER email,
ADD COLUMN sms_notifications_enabled BOOLEAN DEFAULT TRUE AFTER phone_number;

-- Create SMS conversations table to track ongoing SMS interactions
CREATE TABLE IF NOT EXISTS sms_conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,

    -- User and Phone Info
    user_id INT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,

    -- Conversation Context
    conversation_state ENUM('idle', 'awaiting_start_confirmation', 'collecting_ticket_details', 'awaiting_completion', 'collecting_completion_details') DEFAULT 'idle',
    active_ticket_id INT NULL COMMENT 'winter_ops_logs.id for active ticket',
    active_property_id INT NULL COMMENT 'locations.id for context',

    -- AI Context
    context_data JSON NULL COMMENT 'Stores partial ticket data, conversation history, etc.',

    -- Timestamps
    last_message_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign Keys
    CONSTRAINT fk_sms_conv_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_sms_conv_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Indexes
    INDEX idx_phone_number (phone_number),
    INDEX idx_user_id (user_id),
    INDEX idx_conversation_state (conversation_state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create SMS messages log table
CREATE TABLE IF NOT EXISTS sms_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,

    -- Message Details
    conversation_id INT NULL,
    phone_number VARCHAR(20) NOT NULL,
    direction ENUM('inbound', 'outbound') NOT NULL,
    message_body TEXT NOT NULL,

    -- Twilio Details
    twilio_sid VARCHAR(100) NULL,
    twilio_status VARCHAR(50) NULL,

    -- AI Processing
    ai_processed BOOLEAN DEFAULT FALSE,
    ai_interpretation JSON NULL COMMENT 'AI extracted data from message',

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    CONSTRAINT fk_sms_msg_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_sms_msg_conversation FOREIGN KEY (conversation_id) REFERENCES sms_conversations(id) ON DELETE SET NULL,

    -- Indexes
    INDEX idx_phone_number (phone_number),
    INDEX idx_direction (direction),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create SMS notification preferences table
CREATE TABLE IF NOT EXISTS sms_notification_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    user_id INT NOT NULL,

    -- Notification Types
    notify_on_assignment BOOLEAN DEFAULT TRUE,
    notify_on_route_assignment BOOLEAN DEFAULT TRUE,
    notify_on_weather_alert BOOLEAN DEFAULT TRUE,
    notify_on_winter_event_start BOOLEAN DEFAULT TRUE,
    notify_on_ticket_reminder BOOLEAN DEFAULT TRUE,

    -- Quiet Hours (EST)
    quiet_hours_start TIME NULL COMMENT 'No SMS during these hours',
    quiet_hours_end TIME NULL,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign Keys
    CONSTRAINT fk_sms_pref_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_sms_pref_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Unique Constraint
    UNIQUE KEY unique_user_preferences (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
