# Winter Event Workflow

**Purpose**: How snow storm events are managed from start to finish
**Last Updated**: 2025-12-23

---

## Overview

A Winter Event represents a snow storm that triggers contractor mobilization. The system manages:
1. Event creation and activation
2. Contractor check-ins
3. Property assignments
4. Service tracking (tickets)
5. Event completion

---

## Event Lifecycle

```
[PENDING]
    ↓ (Manager starts event)
[ACTIVE]
    ↓ (Contractors check in)
[CONTRACTORS READY]
    ↓ (Properties assigned)
[SERVICING PROPERTIES]
    ↓ (Tickets completed)
[ALL COMPLETE]
    ↓ (Manager ends event)
[COMPLETED]
```

---

## Step-by-Step Workflow

### 1. Event Creation

**Who**: Manager or Admin
**Where**: ManageWinterEvents.html

**Process**:
1. Manager clicks "❄️ Winter Events (Start/End Storm Events)"
2. Fills out form:
   - Event name (e.g., "December 23 Snowstorm")
   - Start time (optional, defaults to now)
   - Notes (optional)
3. Clicks "Create Event"

**Backend**:
```sql
INSERT INTO winter_events (tenant_id, event_name, start_time, status, notes)
VALUES (1, 'December 23 Snowstorm', NOW(), 'pending', 'Heavy snow expected');
```

**API**: POST `/winter-events/create`
**File**: `app/routes/winter_event_routes.py`

---

### 2. Event Activation

**Who**: Manager or Admin
**Where**: ManageWinterEvents.html

**Process**:
1. Manager sees list of events
2. Clicks "▶️ Start Event" on a pending event
3. System activates event

**Backend**:
```sql
-- Deactivate all other events
UPDATE winter_events SET status = 'completed' WHERE status = 'active';

-- Activate selected event
UPDATE winter_events SET status = 'active', start_time = NOW() WHERE id = <event_id>;
```

**Effect**:
- Event becomes "active" (only one active at a time)
- Contractors can now check in via:
  - SMS: "READY"
  - Web: EventCheckIn.html
  - Mobile: Check-in button on dashboards

**API**: POST `/winter-events/<event_id>/activate`

---

### 3. Contractor Check-In

**Who**: Contractors (Users)
**Where**:
- EventCheckIn.html (web)
- SMS (text "READY")
- Dashboard check-in button

#### Via Web (EventCheckIn.html):

**Process**:
1. Contractor clicks "🔔 Event Check-In / Checkout" button
2. System shows active event
3. Contractor selects equipment from dropdown (or uses default)
4. Clicks "Check In"

**Backend**:
```sql
-- Check if already checked in
SELECT id FROM event_checkins
WHERE winter_event_id = <event_id> AND user_id = <user_id> AND checked_out_at IS NULL;

-- If not checked in, create new record
INSERT INTO event_checkins (winter_event_id, user_id, equipment_in_use, status, notes)
VALUES (<event_id>, <user_id>, 'F350, Plow, Salter', 'checked_in', 'Checked in via web');

-- If already checked in, update status
UPDATE event_checkins
SET status = 'checked_in', equipment_in_use = 'F350, Plow, Salter'
WHERE winter_event_id = <event_id> AND user_id = <user_id>;
```

**API**: POST `/checkin/checkin`
**File**: `app/routes/checkin_routes.py`

#### Via SMS:

**Process**:
1. Contractor texts: "READY"
2. System finds active event
3. System creates/updates check-in

**Backend**: Same SQL as above

**SMS Response**:
```
✅ Checked in for December 23 Snowstorm!

Equipment: F350, Plow, Salter

You may receive assignments soon.

Reply:
- WORKING when servicing
- HOME when finished
```

**File**: `app/routes/sms_routes.py`

---

### 4. Property Assignment

**Who**: Manager or Admin
**Where**: PropertyBoard.html

**Process**:
1. Manager opens Property Board
2. Sees all properties in a grid
3. Sees all checked-in contractors in sidebar
4. Drags contractor onto property (or clicks assign button)
5. System assigns property to contractor

**Backend**:
```sql
UPDATE properties
SET assigned_to = <user_id>
WHERE id = <property_id>;
```

**Auto-Assignment** (optional):
- Manager can bulk-assign based on routes
- System respects `users.available_for_assignment` flag

**API**: POST `/properties/<property_id>/assign`
**File**: `app/routes/property_routes.py`

---

### 5. Contractor Servicing

#### Option A: Manual Ticket Creation (Web)

**Who**: Contractor
**Where**: WinterOpsLog.html

**Process**:
1. Contractor clicks "Submit Winter Log"
2. Selects property from dropdown
3. Fills in:
   - Equipment used
   - Bulk salt (yards)
   - Bagged salt (count)
   - Calcium bags
   - Start time (defaults to now, snapped to 15-min intervals)
   - End time
   - Notes
4. Clicks "Submit Log"

**Backend**:
```sql
INSERT INTO winter_ops_log (
    property_id, contractor_id, contractor_name,
    equipment, bulk_salt_yards, bags_applied, calcium_bags,
    start_time, end_time, duration_hours, notes, status
)
VALUES (
    <property_id>, <user_id>, 'John Doe',
    'F350, Plow, Salter', 3.0, 5, 2,
    '2025-12-23 14:30:00', '2025-12-23 16:00:00', 1.5,
    'Parking lot and sidewalks cleared', 'completed'
);
```

**API**: POST `/ops/create-log`
**File**: `app/routes/ops_routes.py`

#### Option B: SMS Ticket Creation

**Who**: Contractor
**Where**: SMS

**Process**:
1. Contractor texts: "START"
2. System lists assigned properties
3. Contractor texts property number (e.g., "1")
4. System creates ticket with start_time = NOW()
5. Contractor texts updates: "Plow truck 3 yards salt"
6. System updates ticket with equipment and salt
7. Contractor texts: "DONE"
8. System sets end_time, calculates duration, marks completed

**Backend**: Same SQL as above, but built incrementally

**See**: [SMS_WORKFLOW.md](./SMS_WORKFLOW.md) for full details

---

### 6. Status Updates

**Who**: Contractor
**Where**: SMS or EventCheckIn.html

**Status Progression**:
- `checked_in` → Ready for assignment
- `working` → Actively servicing a property
- `completed` → Checked out

**SMS Commands**:
- "READY" → Sets status to 'checked_in'
- "WORKING" → Sets status to 'working'
- "HOME" → Sets status to 'completed' and checks out

**Backend**:
```sql
UPDATE event_checkins
SET status = 'working', updated_at = NOW()
WHERE winter_event_id = <event_id> AND user_id = <user_id>;
```

---

### 7. Manager Monitoring

**Who**: Manager or Admin
**Where**: Multiple pages

#### Event Overview (ManageWinterEvents.html)
Shows:
- Active event name
- Start time
- Number of checked-in contractors
- Event status

#### Property Board (PropertyBoard.html)
Shows:
- All properties
- Which contractor is assigned to each
- Check-in status of contractors
- Real-time updates

#### Winter Logs (ViewWinterLogs.html)
Shows:
- All service tickets for date range
- Filter by property, contractor, equipment
- Export to Excel

#### Check-in Dashboard
Shows:
- Who is checked in
- Their equipment
- Their current status (ready/working)
- Time checked in

---

### 8. Event Completion

**Who**: Manager or Admin
**Where**: ManageWinterEvents.html

**Process**:
1. All properties serviced
2. All contractors checked out
3. Manager clicks "⏹️ End Event"
4. System deactivates event

**Backend**:
```sql
-- Check out any remaining contractors
UPDATE event_checkins
SET checked_out_at = NOW(), status = 'completed'
WHERE winter_event_id = <event_id> AND checked_out_at IS NULL;

-- Complete event
UPDATE winter_events
SET status = 'completed', end_time = NOW()
WHERE id = <event_id>;
```

**API**: POST `/winter-events/<event_id>/complete`

---

## Database Tables Involved

### winter_events
```sql
id, tenant_id, event_name, start_time, end_time, status, notes, created_at, updated_at
```

**Statuses**:
- `pending` - Created but not started
- `active` - Currently ongoing (only one active at a time)
- `completed` - Finished

### event_checkins
```sql
id, winter_event_id, user_id, checked_in_at, checked_out_at,
equipment_in_use, status, notes, created_at, updated_at
```

**Statuses**:
- `checked_in` - Ready for work
- `working` - Currently servicing
- `completed` - Checked out

### winter_ops_log
```sql
id, property_id, contractor_id, contractor_name,
equipment, bulk_salt_yards, bags_applied, calcium_bags,
start_time, end_time, duration_hours, notes, status, created_at, updated_at
```

**Status**: 'in_progress', 'completed'

---

## API Endpoints

### Winter Events
**File**: `app/routes/winter_event_routes.py`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/winter-events/` | List all events |
| GET | `/winter-events/active` | Get active event |
| POST | `/winter-events/create` | Create new event |
| POST | `/winter-events/<id>/activate` | Start event |
| POST | `/winter-events/<id>/complete` | End event |
| DELETE | `/winter-events/<id>` | Delete event |

### Check-ins
**File**: `app/routes/checkin_routes.py`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/checkin/checkin` | Check in to event |
| POST | `/checkin/checkout` | Check out from event |
| POST | `/checkin/update-status` | Update status |
| GET | `/checkin/my-status` | Get my check-in status |
| GET | `/checkin/event/<event_id>` | Get all check-ins for event |

---

## Business Rules

### Only One Active Event
- System automatically deactivates previous event when new one starts
- Prevents confusion about which event contractors are working on

### Check-in Requires Active Event
- Contractors can't check in if no event is active
- SMS: "❌ No active snow event..."
- Web: Check-in button disabled

### Equipment Defaults
- If contractor has `default_equipment` set in profile, it's pre-filled
- Saves time during rapid mobilization

### Time Snapping
- All start/end times snap to nearest 15-minute interval
- Simplifies billing calculations
- Prevents "worked 1 hour 7 minutes" → becomes "1.25 hours"

**Function**: `snap_to_15_minutes()` in `ops_routes.py`

### Availability Flag
- `users.available_for_assignment` determines if contractor appears in assignment lists
- Set to FALSE when contractor texts "HOME"
- Manager must manually re-enable

### Automatic Check-out
- When contractor texts "HOME", system:
  - Checks out from event
  - Closes any open tickets
  - Sets available_for_assignment = FALSE

---

## Common Queries

### Get Active Event with Check-ins
```sql
SELECT we.*, COUNT(ec.id) as checked_in_count
FROM winter_events we
LEFT JOIN event_checkins ec ON we.id = ec.winter_event_id
    AND ec.checked_out_at IS NULL
WHERE we.status = 'active'
GROUP BY we.id;
```

### Get All Checked-In Contractors
```sql
SELECT u.id, u.name, u.phone, ec.equipment_in_use, ec.status, ec.checked_in_at
FROM event_checkins ec
JOIN users u ON ec.user_id = u.id
JOIN winter_events we ON ec.winter_event_id = we.id
WHERE we.status = 'active' AND ec.checked_out_at IS NULL
ORDER BY ec.checked_in_at ASC;
```

### Get Tickets for Event
```sql
SELECT w.*, p.name as property_name, u.name as contractor_name
FROM winter_ops_log w
JOIN properties p ON w.property_id = p.id
JOIN users u ON w.contractor_id = u.id
JOIN winter_events we ON we.status = 'active'
WHERE DATE(w.created_at) = DATE(we.start_time)
ORDER BY w.created_at DESC;
```

---

## Reporting

### Event Summary Report
**Generated from**: Reports.html
**Includes**:
- Total contractors checked in
- Total properties serviced
- Total salt used (bulk + bagged)
- Total hours worked
- Cost breakdown by contractor
- Timeline of activities

### Property Service History
**Generated from**: ViewWinterLogs.html
**Filters**:
- Date range
- Property
- Contractor
- Equipment type

**Export**: Excel spreadsheet with all ticket details

---

## Notifications

### When Event Starts
- (Future) Send SMS to all available contractors: "❄️ Snow event started! Text READY to check in."

### When Assigned to Property
- (Future) Send SMS: "📍 You've been assigned to Main Street Plaza. Text START when you arrive."

### Zero Tolerance Properties
- If weather forecast shows snow
- Send alert to manager about zero-tolerance properties
- Manager can pre-assign contractors

---

## Mobile Considerations

### Check-In Button on All Dashboards
- UserDashboard.html
- ManagerDashboard.html
- AdminDashboard.html

**Placement**: Top of page, prominent green button

**Responsive Design**:
```css
@media (max-width: 768px) {
    .checkin-button {
        width: 100%;
        font-size: 18px;
        padding: 15px;
    }
}
```

### SMS is Primary for Field Workers
- Contractors in trucks prefer SMS over web
- Quick commands: READY, WORKING, HOME, START, DONE
- No need to navigate complex UI while driving

---

## Error Handling

### Duplicate Check-In
- If contractor already checked in, update existing record
- Don't create duplicate

### No Active Event
- Check-in disabled
- Clear error message

### Orphaned Check-Ins
- If event is completed but check-ins still open
- Admin can manually close via SQL:
  ```sql
  UPDATE event_checkins
  SET checked_out_at = NOW(), status = 'completed'
  WHERE winter_event_id = <event_id> AND checked_out_at IS NULL;
  ```

### Incomplete Tickets
- If contractor texts START but never DONE
- Ticket remains in_progress
- Manager can manually complete via ViewWinterLogs.html

---

## Future Enhancements

1. **Automatic Event Creation**: Based on weather API (if >2" snow forecast)
2. **Push Notifications**: Native mobile app notifications
3. **Real-time Dashboard**: WebSocket updates for Property Board
4. **Contractor Leaderboard**: Gamification (most properties serviced)
5. **Photo Requirements**: MMS photos for high-value properties
6. **GPS Verification**: Ensure contractor is actually at property
7. **Overtime Alerts**: Warn manager if contractor > 8 hours

---

## Troubleshooting

### Event Won't Activate
- Check if another event is already active
- Only one event can be active at a time
- Complete or delete other active events first

### Contractor Can't Check In
1. Verify active event exists
2. Check user status (must be 'active')
3. Verify phone number (for SMS)
4. Check event_checkins table for errors

### Property Assignment Not Showing
1. Verify property exists
2. Check if contractor is checked in
3. Refresh Property Board

### Ticket Not Created via SMS
1. Check conversation state (should be 'collecting_data')
2. Verify property assignment
3. Check winter_ops_log for partial tickets
4. Review SMS logs in journalctl

---

## Related Documentation

- [SMS_WORKFLOW.md](./SMS_WORKFLOW.md) - SMS ticket creation
- [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) - Table structures
- [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) - Overall system
