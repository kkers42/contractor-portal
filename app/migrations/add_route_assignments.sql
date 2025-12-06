-- Migration: Add route_assignments table
-- This allows routes to be assigned to multiple users

CREATE TABLE IF NOT EXISTS route_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    user_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_route_user (route_id, user_id)
);

CREATE INDEX idx_route_assignments_route ON route_assignments(route_id);
CREATE INDEX idx_route_assignments_user ON route_assignments(user_id);
