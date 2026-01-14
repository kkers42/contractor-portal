# Snow Contractor Portal - Complete Workflow Documentation

**Last Updated:** 2025-12-31
**Purpose:** Comprehensive documentation of all user workflows to ensure correct implementation and prevent breaking changes

---

## 1. USER WORKFLOW (Subcontractor/Field Worker)

### Role Overview
- **Access Level:** Limited - can only see their assigned properties
- **Primary Tasks:** Start/finish work tickets, view their assignments
- **Cannot:** Manage properties, assign work, view reports

### Step-by-Step Workflow

#### A. Login and Dashboard Access
1. Navigate to login page
2. Enter credentials (email/password)
3. Redirected to **User Dashboard**

#### B. User Dashboard Features
**URL:** `/static/UserDashboard.html`

Available options:
- 🎫 **My Active Tickets** - View and manage assigned work
- 📍 **Property Map** - See locations of assigned properties
- 🌨️ **Weather Dashboard** - View current weather conditions
- 👤 **User Profile** - Manage personal settings

#### C. My Active Tickets Workflow (PRIMARY WORKFLOW)
**URL:** `/static/MyTickets.html`

**Step 1: View Assigned Properties**
- System loads all properties assigned via Property Board
- Each property card shows:
  - Property name and address
  - Square footage
  - Manager name
  - Services (Plow/Salt)
  - Current ticket status

**Step 2: Start Work Ticket**
- User finds property they're working on
- Clicks **"▶ Start Ticket"** button
- System creates `winter_ops_logs` entry with:
  - `time_in` = current timestamp
  - `status` = 'open'
  - `user_id` = logged in user
  - `property_id` = selected property
- Card updates to show "⏰ Active Ticket"

**Step 3: Complete Work**
- When done with property, click **"⏹ Finish Ticket"**
- Redirected to **Winter Ops Log** form (`/static/WinterOpsLog.html`)
- Fill out completion details:
  - Equipment used
  - Materials (bulk salt, bag salt, calcium chloride)
  - Time out (auto-filled)
  - Notes about work performed
- Click **"Submit Log"**
- System sets:
  - `time_out` = current timestamp
  - `status` = 'closed'

**Step 4: Repeat for Next Property**
- Return to My Active Tickets
- Start next assigned property

#### D. Property Map
**URL:** `/static/PropertyMap.html`
- View map with pins for all assigned properties
- Click pin to see property details
- Helps plan route for the day

#### E. Weather Dashboard
**URL:** `/static/WeatherDashboard.html`
- View current conditions
- Check forecasts
- Monitor storm progression

### BUGS FOUND DURING USER WORKFLOW TESTING:
```
BUG-001: [TO BE TESTED]
Description: Need to verify "Start Ticket" doesn't require Admin role
File: app/routes/ops_routes.py
Status: UNTESTED

BUG-002: [TO BE TESTED]
Description: Verify property assignments show correctly in My Active Tickets
File: app/routes/property_routes.py - /my-properties/ endpoint
Status: UNTESTED
```

---

## 2. CONTRACTOR WORKFLOW (Subcontractor with team)

### Role Overview
- **Access Level:** Mid-level - manages their own work and team
- **Primary Tasks:** Same as User + view their team's work
- **Cannot:** Assign properties to others, manage all properties, view billing reports

### Step-by-Step Workflow

#### A. Login and Dashboard
1. Login with contractor credentials
2. Redirected to **User Dashboard** (same as User role)

#### B. Contractor-Specific Features
**Differences from User:**
- May see multiple team members' tickets if they manage subcontractors
- Can view winter logs for their team
- May have access to field service reports

#### C. Work Ticket Workflow
**Identical to User workflow** - see Section 1.C above

### BUGS FOUND DURING CONTRACTOR WORKFLOW TESTING:
```
BUG-003: [TO BE TESTED]
Description: Verify Contractor can see team members' work
File: TBD
Status: UNTESTED
```

---

## 3. MANAGER WORKFLOW

### Role Overview
- **Access Level:** High - manages properties and assignments
- **Primary Tasks:** Assign work, monitor progress, create winter events, manage routes
- **Cannot:** Modify users, change system settings, view billing

### Step-by-Step Workflow

#### A. Login and Dashboard
1. Login with manager credentials
2. Redirected to **Manager Dashboard**

#### B. Manager Dashboard Features
**URL:** `/static/ManagerDashboard.html`

Available options:
- 📍 **Property Board** - Assign contractors to properties
- 🗺️ **Property Map** - View all properties on map
- ❄️ **Manage Winter Events** - Create/manage snow events
- 📊 **View Winter Logs** - Monitor all work tickets
- 🛣️ **Manage Routes** - Create property routes for efficient work
- 📋 **Manage Property Lists** - Organize properties into lists
- 🌨️ **Weather Dashboard** - Monitor weather
- 👥 **Manage Users** - Add/edit contractors (if permitted)

#### C. Property Assignment Workflow (CRITICAL)
**URL:** `/static/PropertyBoard.html`

**Step 1: Access Property Board**
- Click "Property Board" from dashboard
- System loads all properties in columnar layout

**Step 2: Filter Properties (Optional)**
- Use filters:
  - Property name search
  - Address search
  - Manager name search
  - Route/List filter
  - Trigger type filter (Zero tolerance, 0.5", 1", 2", Custom)

**Step 3: Assign Contractor to Property**
- Locate property column
- Find "Assign Contractor" dropdown
- Select contractor from list
- Click dropdown to assign
- System creates entry in `property_contractors` table:
  - `property_id`
  - `contractor_id`
  - `is_primary` = false (initially)
  - `acceptance_status` = 'pending'
  - `assigned_date` = current timestamp

**Step 4: Set Primary Contractor (Optional)**
- If property has multiple contractors assigned
- Click **"Set as Primary"** on one contractor card
- System updates `is_primary` = true for selected contractor

**Step 5: Remove Contractor (If Needed)**
- Click **"✕ Remove"** button on contractor card
- System deletes from `property_contractors` table
- **CRITICAL:** Filters must be preserved after removal

**Step 6: Verify Assignment**
- Contractor should now see property in their "My Active Tickets"
- Property shows in contractor's Property Map

#### D. Winter Event Management Workflow
**URL:** `/static/ManageWinterEvents.html`

**Step 1: Create New Event**
- Click **"+ Create Winter Event"**
- Fill out form:
  - Event name (e.g., "January 2nd Storm")
  - Start date/time
  - Expected duration
  - Notes
- Click **"Save"**
- System creates entry in `winter_events` table
- Status = 'active' (or 'planned')

**Step 2: Activate Event**
- When storm begins, set status to 'active'
- Contractors see active event
- Work logs associate with this event

**Step 3: Complete Event**
- When storm ends, set status to 'completed'
- All logs now historical
- Ready for billing

#### E. Route Management Workflow
**URL:** `/static/ManageRoutes.html`

**Step 1: Create Route**
- Click **"+ Create Route"**
- Enter route name (e.g., "East Side Route A")
- Enter description
- Click **"Save"**

**Step 2: Add Properties to Route**
- Click route card to open
- Click **"+ Add Properties"**
- Select properties from list
- Properties added with sequence order
- Enter estimated time per property (optional)
- Add notes per property (optional)

**Step 3: Reorder Properties**
- Drag and drop properties in desired order
- Click **"💾 Save Order"**
- Sequence numbers update

**Step 4: View Route as Reference**
- Routes are organizational lists only
- Contractors can view route to see planned order
- **DOES NOT AUTO-CREATE TICKETS**
- Contractors still manually start/finish each property

#### F. Monitor Work Progress
**URL:** `/static/ViewWinterLogs.html`

**Step 1: View All Logs**
- See all contractor work tickets
- Filter by:
  - Date range
  - Property
  - Contractor
  - Winter event
  - Equipment type
  - Status (open/closed)

**Step 2: Export Reports**
- Select filters
- Click export options
- Download Excel with work details

### BUGS FOUND DURING MANAGER WORKFLOW TESTING:
```
BUG-004: [TO BE TESTED]
Description: Property Board filter reset after assigning/removing contractor
File: app/static/PropertyBoard.html
Status: FIXED (need to verify)

BUG-005: [TO BE TESTED]
Description: Route activation creates automatic tickets (should not)
File: app/routes/route_routes.py
Status: FIXED (activation endpoint removed)
```

---

## 4. ADMIN WORKFLOW

### Role Overview
- **Access Level:** Full - complete system control
- **Primary Tasks:** Everything Manager can do + user management, system settings, billing reports
- **Full Access:** All features

### Step-by-Step Workflow

#### A. Login and Dashboard
1. Login with admin credentials
2. Redirected to **Admin Dashboard**

#### B. Admin Dashboard Features
**URL:** `/static/AdminDashboard.html`

All Manager features PLUS:
- 👥 **Manage Users** - Full user CRUD operations
- ⚙️ **Settings** - System configuration
- 📊 **Reports** - Billing and analytics reports
- 🔗 **Jobber Integration** - Sync with Jobber
- 💰 **QuickBooks Integration** - Accounting integration
- 🔑 **API Keys** - Manage integrations

#### C. User Management Workflow
**URL:** `/static/ManageUsers.html` (if exists)

**Step 1: Create New User**
- Click **"+ Add User"**
- Fill form:
  - Name
  - Email
  - Phone
  - Role (User, Contractor, Manager, Admin)
  - Password (temporary)
- Click **"Save"**
- System sends invitation email

**Step 2: Edit User**
- Click user row
- Update details
- Change role if needed
- Click **"Save"**

**Step 3: Deactivate User**
- Click **"Deactivate"**
- User can no longer login
- Historical data preserved

#### D. Reports Workflow
**URL:** `/static/Reports.html`

**Available Reports:**
1. **Billing Report** - Invoice generation
   - Select date range
   - Select contractors
   - Export to Excel
   - One sheet per contractor
   - Includes property details, times, materials

2. **Property Equipment Report**
   - Equipment usage by property
   - Material consumption
   - Service frequency

3. **Multi-Contractor Report**
   - Compare contractor performance
   - Time analysis
   - Material usage

4. **Weather Report**
   - Correlate work with weather events
   - Storm severity vs work performed

#### E. Integration Management

**Jobber Integration:**
**URL:** `/static/JobberIntegration.html`
- Connect Jobber account
- Sync clients/properties
- Map fields
- Schedule automatic syncs

**QuickBooks Integration:**
**URL:** `/static/QuickBooksIntegration.html`
- Connect QuickBooks account
- Map accounts
- Export invoices
- Sync payments

### BUGS FOUND DURING ADMIN WORKFLOW TESTING:
```
BUG-006: [TO BE TESTED]
Description: Verify all reports generate correctly
File: app/routes/report_routes.py
Status: UNTESTED

BUG-007: [TO BE TESTED]
Description: Check Jobber integration UI completeness
File: app/static/JobberIntegration.html
Status: INCOMPLETE (per previous todos)
```

---

## 5. CROSS-ROLE WORKFLOWS

### A. Property Lifecycle
1. **Admin/Manager:** Create property in system
2. **Manager:** Assign contractor via Property Board
3. **Contractor:** Accept assignment (implicit)
4. **User/Contractor:** View in My Active Tickets
5. **User/Contractor:** Start work ticket
6. **User/Contractor:** Complete and submit log
7. **Manager/Admin:** Review logs
8. **Admin:** Generate billing report
9. **Admin:** Export to QuickBooks

### B. Winter Event Lifecycle
1. **Manager/Admin:** Create winter event (storm forecast)
2. **Manager:** Assign contractors to properties (pre-storm)
3. **Manager/Admin:** Activate event (storm begins)
4. **Contractors:** Start work on assigned properties
5. **System:** Associates all tickets with active winter event
6. **Contractors:** Complete work, submit logs
7. **Manager/Admin:** Monitor progress in real-time
8. **Manager/Admin:** Mark event complete (storm ends)
9. **Admin:** Generate billing report for event
10. **Admin:** Invoice customers

### C. Route Usage Workflow
1. **Manager:** Create route with property sequence
2. **Manager:** Share route with contractor (reference only)
3. **Contractor:** Views route to plan day
4. **Contractor:** Goes to My Active Tickets
5. **Contractor:** Manually starts first property in route
6. **Contractor:** Completes property
7. **Contractor:** Manually starts next property in route
8. **Repeat:** Until all route properties complete
9. **Manager:** Reviews completion times vs estimates

---

## 6. CRITICAL SYSTEM RULES

### Property Assignment Rules
- ✅ Property can have multiple contractors assigned
- ✅ Only one can be "primary"
- ✅ Assignment creates `property_contractors` record
- ✅ Does NOT create `winter_ops_logs` automatically
- ✅ Contractor sees property in "My Active Tickets"
- ✅ Contractor manually starts work with "Start Ticket"

### Ticket Creation Rules
- ❌ Tickets are NEVER auto-created
- ✅ Tickets created ONLY when contractor clicks "Start Ticket"
- ✅ One open ticket per property per contractor at a time
- ✅ Ticket associates with active winter event (if exists)
- ✅ Time in = when "Start Ticket" clicked
- ✅ Time out = when "Finish Ticket" clicked and log submitted

### Route Rules
- ✅ Routes are organizational/reference lists only
- ❌ Routes do NOT auto-create tickets
- ❌ Routes do NOT auto-assign contractors to properties
- ✅ Routes CAN include estimated times (planning only)
- ✅ Contractors view route for optimal sequence
- ✅ Contractors still manually start each property

### Winter Event Rules
- ✅ Only one event can be "active" at a time
- ✅ All tickets during active event auto-associate
- ✅ Events can be planned, active, or completed
- ✅ Completed events are historical/reporting only

### Filter Preservation Rules
- ✅ Property Board filters MUST persist after:
  - Assigning contractor
  - Removing contractor
  - Setting primary contractor
  - Any board refresh
- ✅ Filters reset ONLY on page reload or explicit "Clear Filters"

---

## 7. BUG TRACKING FROM WORKFLOW TESTING

### High Priority Bugs
```
BUG-001: User role access to "Start Ticket"
Priority: HIGH
Status: UNTESTED
Impact: Users cannot start work if blocked by role check
File: app/routes/ops_routes.py - /submit-winter-log/ endpoint
Test: Login as User, try to start ticket
```

```
BUG-004: Property Board filter reset
Priority: HIGH
Status: FIXED (needs verification)
Impact: Managers lose filter context when assigning/removing contractors
File: app/static/PropertyBoard.html
Test: Filter by route, assign contractor, verify filter still active
```

```
BUG-005: Route activation auto-creates tickets
Priority: CRITICAL
Status: FIXED (needs verification)
Impact: Created unwanted automatic tickets, bypassed manual workflow
File: app/routes/route_routes.py - /routes/activate/ endpoint
Test: Activate route, verify NO tickets created automatically
```

### Medium Priority Bugs
```
BUG-002: Property assignments not showing in My Active Tickets
Priority: MEDIUM
Status: UNTESTED
Impact: Contractors don't see assigned work
File: app/routes/property_routes.py - /my-properties/ endpoint
Test: Assign property via Property Board, login as contractor, check My Active Tickets
```

```
BUG-006: Report generation completeness
Priority: MEDIUM
Status: UNTESTED
Impact: Billing reports may be missing data
File: app/routes/report_routes.py
Test: Generate each report type, verify data accuracy
```

### Low Priority Bugs
```
BUG-007: Jobber integration UI incomplete
Priority: LOW
Status: KNOWN INCOMPLETE
Impact: Feature not fully usable
File: app/static/JobberIntegration.html
Test: N/A - known incomplete from previous todos
```

---

## 8. TESTING CHECKLIST

### Phase 1: User Role Testing
- [ ] Login as User
- [ ] Access My Active Tickets
- [ ] Verify assigned properties show
- [ ] Start a ticket
- [ ] Verify time_in recorded
- [ ] Finish ticket and submit log
- [ ] Verify time_out recorded
- [ ] Verify ticket status = 'closed'
- [ ] Check Property Map displays assigned properties
- [ ] Check Weather Dashboard loads

### Phase 2: Manager Role Testing
- [ ] Login as Manager
- [ ] Access Property Board
- [ ] Assign contractor to property
- [ ] Verify contractor sees property in their tickets
- [ ] Remove contractor from property
- [ ] Verify filters preserved after assignment/removal
- [ ] Create winter event
- [ ] Activate winter event
- [ ] Create route
- [ ] Add properties to route
- [ ] Reorder route properties
- [ ] Save route
- [ ] Verify route does NOT create tickets
- [ ] View winter logs
- [ ] Export logs to Excel

### Phase 3: Admin Role Testing
- [ ] Login as Admin
- [ ] Create new user
- [ ] Edit user
- [ ] Deactivate user
- [ ] Generate billing report
- [ ] Export billing report
- [ ] Generate property equipment report
- [ ] Test Jobber integration (if complete)
- [ ] Test QuickBooks integration (if complete)

### Phase 4: Cross-Role Integration Testing
- [ ] Manager assigns property
- [ ] User sees assignment
- [ ] User starts ticket
- [ ] Manager sees active ticket in logs
- [ ] User finishes ticket
- [ ] Admin generates report with completed ticket
- [ ] Verify data flows correctly through entire lifecycle

---

## NEXT STEPS

1. **Systematic Testing:** Go through each workflow step-by-step
2. **Document Bugs:** Add to bug list with reproduction steps
3. **Prioritize Fixes:** High priority = blocking workflows
4. **Fix One at a Time:** Test fix before moving to next
5. **Update Workflows:** Keep this document current as changes are made

---

**END OF WORKFLOW DOCUMENTATION**
