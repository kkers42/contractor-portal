# Database Schema Documentation

**Database**: contractor_portal
**RDBMS**: MySQL 8.x
**Last Updated**: 2025-12-23

---

## Table of Contents
1. [Core Tables](#core-tables)
2. [Property Management](#property-management)
3. [Winter Operations](#winter-operations)
4. [Communication](#communication)
5. [Relationships](#relationships)
6. [Indexes](#indexes)

---

## Core Tables

### users
**Purpose**: All system users (Admins, Managers, Contractors, Subcontractors)

| Column | Type | Null | Key | Default | Description |
|--------|------|------|-----|---------|-------------|
| id | int | NO | PRI | AUTO_INCREMENT | Unique user ID |
| tenant_id | int | NO | MUL | 1 | Multi-tenancy support |
| name | varchar(255) | YES | | NULL | Full name |
| phone | varchar(20) | YES | | NULL | Phone number |
| phone_number | varchar(20) | YES | | NULL | Duplicate phone field |
| email | varchar(255) | NO | UNI | | Email (unique) |
| username | varchar(100) | YES | | NULL | Username |
| password | varchar(255) | YES | | NULL | bcrypt hashed password |
| password_hash | varchar(255) | YES | | NULL | Duplicate password field |
| role | enum | YES | MUL | 'User' | Admin, Manager, Contractor, Subcontractor, User |
| contractor_id | int | YES | MUL | NULL | Links subcontractor to contractor |
| default_equipment | varchar(255) | YES | MUL | NULL | Default equipment for user |
| available_for_assignment | tinyint(1) | YES | MUL | 1 | Can be auto-assigned properties? |
| sms_notifications_enabled | tinyint(1) | YES | | 1 | Receive SMS notifications? |
| status | enum | YES | MUL | 'pending' | pending, active, suspended |
| display_name | varchar(255) | YES | | NULL | Display name for UI |
| avatar_url | varchar(512) | YES | | NULL | Profile picture URL |
| address | text | YES | | NULL | User's address |
| last_login_at | datetime | YES | | NULL | Last login timestamp |
| created_at | datetime | YES | | CURRENT_TIMESTAMP | Account creation |
| updated_at | datetime | YES | | CURRENT_TIMESTAMP | Last update (auto) |

**Key Relationships**:
- Self-referencing: `contractor_id` → `users.id` (subcontractors link to contractors)

---

## Property Management

### properties
**Purpose**: Properties/locations to be serviced

| Column | Type | Null | Key | Default | Description |
|--------|------|------|-----|---------|-------------|
| id | int | NO | PRI | AUTO_INCREMENT | Property ID |
| tenant_id | int | NO | MUL | 1 | Multi-tenancy |
| name | varchar(255) | NO | | | Property name |
| address | text | YES | | NULL | Full address |
| latitude | decimal(10,7) | YES | | NULL | GPS latitude |
| longitude | decimal(10,7) | YES | | NULL | GPS longitude |
| zero_tolerance | tinyint(1) | YES | | 0 | Requires immediate service? |
| assigned_to | int | YES | MUL | NULL | User ID of assigned contractor |
| created_at | datetime | YES | | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | datetime | YES | | CURRENT_TIMESTAMP | Last update |

**Relationships**:
- `assigned_to` → `users.id`

---

### property_lists
**Purpose**: Named groups of properties (e.g., "Downtown Properties", "Priority Sites")

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | List ID |
| tenant_id | int | NO | MUL | Multi-tenancy |
| list_name | varchar(255) | NO | | Name of the list |
| description | text | YES | | Description |
| created_at | datetime | YES | | Creation timestamp |
| updated_at | datetime | YES | | Last update |

---

### property_list_items
**Purpose**: Properties belonging to lists (many-to-many relationship)

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Item ID |
| list_id | int | NO | MUL | Links to property_lists.id |
| property_id | int | NO | MUL | Links to properties.id |
| sort_order | int | YES | | Order in list |
| created_at | datetime | YES | | Creation timestamp |

**Relationships**:
- `list_id` → `property_lists.id`
- `property_id` → `properties.id`

---

### routes
**Purpose**: Predefined routes (sequences of properties)

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Route ID |
| tenant_id | int | NO | MUL | Multi-tenancy |
| route_name | varchar(255) | NO | | Name of route |
| description | text | YES | | Description |
| created_at | datetime | YES | | Creation timestamp |
| updated_at | datetime | YES | | Last update |

---

### route_properties
**Purpose**: Properties in routes (many-to-many, ordered)

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Item ID |
| route_id | int | NO | MUL | Links to routes.id |
| property_id | int | NO | MUL | Links to properties.id |
| sort_order | int | YES | | Order in route |
| created_at | datetime | YES | | Creation timestamp |

**Relationships**:
- `route_id` → `routes.id`
- `property_id` → `properties.id`

---

## Winter Operations

### winter_events
**Purpose**: Snow storm events (system-wide events that trigger contractor mobilization)

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Event ID |
| tenant_id | int | NO | MUL | Multi-tenancy |
| event_name | varchar(255) | NO | | Name (e.g., "December 23 Snowstorm") |
| start_time | datetime | YES | | Event start |
| end_time | datetime | YES | | Event end |
| status | enum | YES | | 'pending', 'active', 'completed' |
| notes | text | YES | | Notes about the event |
| created_at | datetime | YES | | Creation timestamp |
| updated_at | datetime | YES | | Last update |

---

### event_checkins
**Purpose**: Contractor check-ins for winter events (tracks availability during storms)

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Check-in ID |
| winter_event_id | int | NO | MUL | Links to winter_events.id |
| user_id | int | NO | MUL | Links to users.id |
| checked_in_at | datetime | YES | | Check-in timestamp |
| checked_out_at | datetime | YES | | Check-out timestamp |
| equipment_in_use | varchar(255) | YES | | Equipment for this event |
| status | enum | YES | | 'checked_in', 'working', 'completed' |
| notes | text | YES | | Notes |
| created_at | datetime | YES | | Creation timestamp |
| updated_at | datetime | YES | | Last update |

**Relationships**:
- `winter_event_id` → `winter_events.id`
- `user_id` → `users.id`

---

### winter_ops_log
**Purpose**: Service tickets (each property visit during a snow event)

| Column | Type | Null | Key | Default | Description |
|--------|------|------|-----|---------|-------------|
| id | int | NO | PRI | AUTO_INCREMENT | Ticket ID |
| tenant_id | int | NO | MUL | 1 | Multi-tenancy |
| property_id | int | NO | MUL | | Links to properties.id |
| contractor_id | int | NO | MUL | | Links to users.id (contractor) |
| contractor_name | varchar(255) | YES | | NULL | Contractor name (denormalized) |
| equipment | varchar(255) | YES | | NULL | Equipment used |
| bulk_salt_yards | decimal(10,2) | YES | | NULL | Bulk salt quantity |
| bags_applied | int | YES | | 0 | Bagged salt count |
| calcium_bags | int | YES | | 0 | Calcium bags count |
| start_time | datetime | YES | | NULL | Service start |
| end_time | datetime | YES | | NULL | Service end |
| duration_hours | decimal(5,2) | YES | | NULL | Calculated duration |
| notes | text | YES | | NULL | Service notes |
| status | varchar(50) | YES | | 'completed' | Ticket status |
| created_at | datetime | YES | | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | datetime | YES | | CURRENT_TIMESTAMP | Last update |

**Relationships**:
- `property_id` → `properties.id`
- `contractor_id` → `users.id`

---

## Communication

### sms_conversations
**Purpose**: SMS conversation threads with contractors

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Conversation ID |
| tenant_id | int | NO | MUL | Multi-tenancy |
| user_id | int | NO | MUL | Links to users.id |
| phone_number | varchar(20) | NO | | Contractor's phone |
| state | enum | YES | | 'idle', 'awaiting_property', 'collecting_data' |
| active_ticket_id | int | YES | | Current winter_ops_log.id |
| active_property_id | int | YES | | Current property.id |
| context_data | json | YES | | Conversation context |
| last_message_at | datetime | YES | | Last message timestamp |
| created_at | datetime | YES | | Creation timestamp |
| updated_at | datetime | YES | | Last update |

**Relationships**:
- `user_id` → `users.id`
- `active_ticket_id` → `winter_ops_log.id`
- `active_property_id` → `properties.id`

---

### sms_messages
**Purpose**: Individual SMS messages (sent and received)

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Message ID |
| conversation_id | int | NO | MUL | Links to sms_conversations.id |
| direction | enum | NO | | 'inbound', 'outbound' |
| from_number | varchar(20) | YES | | Sender phone |
| to_number | varchar(20) | YES | | Recipient phone |
| message_body | text | YES | | SMS content |
| ai_interpretation | json | YES | | ChatGPT analysis |
| twilio_sid | varchar(100) | YES | | Twilio message ID |
| status | varchar(50) | YES | | 'sent', 'delivered', 'failed' |
| created_at | datetime | YES | | Creation timestamp |

**Relationships**:
- `conversation_id` → `sms_conversations.id`

---

## Additional Tables

### equipment_rates
**Purpose**: Billing rates for equipment types

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Rate ID |
| tenant_id | int | NO | MUL | Multi-tenancy |
| equipment_name | varchar(255) | NO | | Equipment type |
| hourly_rate | decimal(10,2) | YES | | Rate per hour |
| created_at | datetime | YES | | Creation timestamp |
| updated_at | datetime | YES | | Last update |

---

### api_settings
**Purpose**: System-wide API keys and configuration

| Column | Type | Null | Key | Description |
|--------|------|------|-----|-------------|
| id | int | NO | PRI | Setting ID |
| tenant_id | int | NO | MUL | Multi-tenancy |
| setting_name | varchar(255) | NO | | Setting name |
| setting_value | text | YES | | Setting value (encrypted) |
| created_at | datetime | YES | | Creation timestamp |
| updated_at | datetime | YES | | Last update |

---

## Relationships Diagram

```
users
  ├──> properties (assigned_to)
  ├──> winter_ops_log (contractor_id)
  ├──> event_checkins (user_id)
  ├──> sms_conversations (user_id)
  └──> users (contractor_id) [self-referencing]

properties
  ├──> winter_ops_log (property_id)
  ├──> property_list_items (property_id)
  ├──> route_properties (property_id)
  └──> sms_conversations (active_property_id)

winter_events
  └──> event_checkins (winter_event_id)

sms_conversations
  ├──> sms_messages (conversation_id)
  ├──> winter_ops_log (active_ticket_id)
  └──> properties (active_property_id)

property_lists
  └──> property_list_items (list_id)

routes
  └──> route_properties (route_id)
```

---

## Indexes

### Primary Keys
All tables have an `id` primary key with AUTO_INCREMENT.

### Foreign Key Indexes
- `users.contractor_id` → `users(id)`
- `properties.assigned_to` → `users(id)`
- `winter_ops_log.property_id` → `properties(id)`
- `winter_ops_log.contractor_id` → `users(id)`
- `event_checkins.winter_event_id` → `winter_events(id)`
- `event_checkins.user_id` → `users(id)`
- `sms_conversations.user_id` → `users(id)`
- `sms_messages.conversation_id` → `sms_conversations(id)`

### Unique Indexes
- `users.email` (UNIQUE)

### Multi-tenancy Indexes
- All tables have `tenant_id` indexed for multi-tenant queries

---

## Common Queries

### Get all active contractors
```sql
SELECT id, name, phone, email, default_equipment
FROM users
WHERE status = 'active' AND role IN ('Contractor', 'User')
ORDER BY name;
```

### Get all properties assigned to a contractor
```sql
SELECT p.id, p.name, p.address, p.zero_tolerance
FROM properties p
WHERE p.assigned_to = <user_id>;
```

### Get all tickets for a property
```sql
SELECT w.*, u.name as contractor_name
FROM winter_ops_log w
JOIN users u ON w.contractor_id = u.id
WHERE w.property_id = <property_id>
ORDER BY w.created_at DESC;
```

### Get active winter event with checked-in contractors
```sql
SELECT we.*,
       COUNT(ec.id) as checked_in_count
FROM winter_events we
LEFT JOIN event_checkins ec ON we.id = ec.winter_event_id
    AND ec.checked_out_at IS NULL
WHERE we.status = 'active'
GROUP BY we.id;
```

### Get SMS conversation with recent messages
```sql
SELECT c.*, u.name, u.phone,
       (SELECT COUNT(*) FROM sms_messages WHERE conversation_id = c.id) as message_count
FROM sms_conversations c
JOIN users u ON c.user_id = u.id
WHERE c.id = <conversation_id>;
```

---

## Data Types Explained

### enum Types
- **users.role**: 'Admin', 'Manager', 'Contractor', 'Subcontractor', 'User'
- **users.status**: 'pending', 'active', 'suspended'
- **winter_events.status**: 'pending', 'active', 'completed'
- **event_checkins.status**: 'checked_in', 'working', 'completed'
- **sms_conversations.state**: 'idle', 'awaiting_property', 'collecting_data'
- **sms_messages.direction**: 'inbound', 'outbound'

### JSON Columns
- **sms_conversations.context_data**: Stores conversation state, partial ticket data
- **sms_messages.ai_interpretation**: ChatGPT's analysis of the message

### Timestamps
- All tables have `created_at` and `updated_at`
- `updated_at` has `ON UPDATE CURRENT_TIMESTAMP` trigger

---

## Migration History

Located in `app/migrations/`:
- `add_available_for_assignment.sql` - Added availability flag for contractors
- `add_default_equipment.sql` - Added default equipment to users
- `add_log_status.sql` - Added status field to winter_ops_log
- `add_quickbooks_integration.sql` - QuickBooks integration tables

---

## Backup Strategy

```bash
# Full backup
mysqldump -u contractor -pBimmer325i contractor_portal > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
mysql -u contractor -pBimmer325i contractor_portal < backup_20251223_120000.sql

# Schema only
mysqldump -u contractor -pBimmer325i --no-data contractor_portal > schema.sql
```
