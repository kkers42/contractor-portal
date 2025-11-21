# Contractor Portal - Version 0.5.1 Roadmap

## Version Strategy
Starting with **v0.5.1** and incrementing for each feature release:
- **v0.5.x** - Route management, property filtering, and alerts
- **v0.6.x** - Weather monitoring and AI decision making
- **v0.7.x** - Integrations (QuickBooks, GPS tracking)
- **v0.8.x** - Advanced features and optimizations
- **v1.0.0** - Production-ready release

---

## Feature List - Prioritized

### Phase 1: Route Management & Property Organization (v0.5.1 - v0.5.3)

#### 1. **Optional Routes for Each Login** ⭐ High Priority
**Description**: Allow users to create, save, and manage custom routes for snow plowing
**User Story**: "As a contractor, I want to create and save my preferred plowing routes so I can work efficiently during storms"

**Technical Requirements**:
- New table: `routes` (id, user_id, name, description, created_at)
- New table: `route_properties` (route_id, property_id, sequence_order)
- New page: `ManageRoutes.html`
- API endpoints:
  - `GET /routes/` - Get user's routes
  - `POST /routes/` - Create new route
  - `PUT /routes/{id}` - Update route
  - `DELETE /routes/{id}` - Delete route
  - `POST /routes/{id}/add-property` - Add property to route
  - `PUT /routes/{id}/reorder` - Change property sequence

**Features**:
- Drag-and-drop property ordering
- Route templates (save commonly used routes)
- Quick-assign route to driver
- Print route sheets

**Estimated Effort**: 2-3 days
**Cost Impact**: $0 (backend only)

---

#### 2. **Map View of Routes** ⭐⭐ High Priority
**Description**: Visual map showing properties and routes using Google Maps or Mapbox
**User Story**: "As a manager, I want to see all properties on a map so I can optimize routes visually"

**Technical Requirements**:
- Frontend: Mapbox GL JS or Google Maps JavaScript API
- New page: `RouteMap.html`
- Geocoding API for property addresses
- Clustering for dense property areas

**Features**:
- Interactive map with property markers
- Color-coded by status (pending, in-progress, completed)
- Draw route lines between properties
- Click property for details
- Real-time driver location (if GPS enabled)

**Cost**:
- **Google Maps**: $7 per 1,000 map loads, $5 per 1,000 geocodes
- **Mapbox**: Free up to 50,000 map loads/month, then $0.50 per 1,000
- **Recommendation**: Mapbox (free tier sufficient for most contractors)

**Estimated Effort**: 3-4 days
**Dependencies**: Optional Routes feature

---

#### 3. **Property List Filtering** ⭐ High Priority
**Description**: Create custom lists and filters for better property management
**User Story**: "As a manager, I want to group properties by priority, region, or contract type"

**Technical Requirements**:
- New table: `property_lists` (id, name, user_id, is_shared, created_at)
- New table: `property_list_items` (list_id, property_id)
- Update `PropertyInfo.html` with filter UI

**Features**:
- Create named property lists (e.g., "High Priority", "Downtown Route")
- Filter by:
  - Assigned manager
  - Assigned contractor
  - Service type (plow, salt, both)
  - Contract tier (zero tolerance, 1", 2" trigger)
  - Custom tags
- Save filter combinations
- Share lists between managers
- Bulk actions on filtered properties

**Estimated Effort**: 2 days
**Cost Impact**: $0

---

#### 4. **Filter Properties by Manager and Contractor** ⭐ Medium Priority
**Description**: Quick filtering on property lists
**User Story**: "As an admin, I want to see which properties are assigned to each manager/contractor"

**Technical Requirements**:
- Update `PropertyInfo.html` with dropdown filters
- Add indexes to database for performance
- Export filtered lists to Excel

**Features**:
- Multi-select filter dropdowns
- Search by name, address, or manager
- Sort by various columns
- Remember last filter settings

**Estimated Effort**: 1 day
**Cost Impact**: $0

---

### Phase 2: Time-Based Alerts & Triggers (v0.5.4 - v0.5.6)

#### 5. **Property Open-By Time with Alarms** ⭐⭐⭐ Critical Priority
**Description**: Set required opening times for properties with automated alerts
**User Story**: "As a manager, I need to know if a zero-tolerance property isn't serviced by 6am"

**Technical Requirements**:
- Add columns to `locations`:
  - `open_by_time` (TIME) - e.g., "06:00:00"
  - `alert_offset_minutes` (INT) - Alert X minutes before deadline
  - `alert_contacts` (JSON) - Phone numbers or emails to alert
- New table: `alerts` (id, property_id, alert_time, alert_type, sent_at, acknowledged_at)
- Background task: Check every 5 minutes for pending alerts
- SMS/Email service integration

**Features**:
- Set open-by time per property
- Configure alert lead time (e.g., alert 30 min before deadline)
- Multi-channel alerts:
  - SMS (Twilio)
  - Email
  - Push notification (optional)
  - Dashboard banner
- Escalation (if not acknowledged, alert manager)
- Historical alert log

**Cost**:
- **Twilio SMS**: $0.0075 per SMS
- **SendGrid Email**: Free up to 100/day, then $0.0006 per email
- **Example**: 10 alerts/storm × 20 storms/season = $1.50/season

**Estimated Effort**: 3-4 days
**Dependencies**: None

---

#### 6. **Snow Trigger Amount per Property** ⭐⭐⭐ Critical Priority
**Description**: Set accumulation thresholds for service requirements
**User Story**: "As a manager, I need to track which properties need service based on contract (1", 2", zero tolerance)"

**Technical Requirements**:
- Add columns to `locations`:
  - `trigger_amount` (DECIMAL) - Inches of snow to trigger service
  - `trigger_type` (ENUM) - 'zero_tolerance', 'accumulation', 'event'
  - `contract_tier` (VARCHAR) - "Premium", "Standard", etc.
- Dashboard view: Properties needing service based on current snowfall
- Integration with weather API

**Features**:
- Common presets:
  - Zero Tolerance (0")
  - 0.5" trigger
  - 1" trigger
  - 2" trigger
  - Custom amount
- Dashboard "Action Required" view:
  - Shows properties needing service based on current snowfall
  - Color-coded by urgency
  - One-click route assignment
- Contract tier pricing

**Estimated Effort**: 2 days
**Cost Impact**: $0 (backend only)
**Dependencies**: Weather monitoring (for automation)

---

### Phase 3: Weather Integration (v0.6.1 - v0.6.3)

#### 7. **Weather Monitoring with AI Decision Making** ⭐⭐⭐ High Priority
**Description**: Automated weather monitoring with AI-powered alerts and recommendations
**User Story**: "As a manager, I want the system to alert me when snow is forecasted and recommend which properties need servicing"

**Technical Requirements**:
- Weather API integration (multiple options below)
- Background job: Check forecast every 30 minutes
- AI analyzes forecast + property triggers → generates action plan
- Email alerts via Gmail API

**Weather API Options**:

1. **OpenWeatherMap** (Recommended)
   - Cost: Free up to 1,000 calls/day, then $0.0012 per call
   - Features: Current, hourly, daily forecasts; precipitation
   - Accuracy: Good
   - **Monthly cost**: $0-10

2. **Weather.gov (NOAA)** (Best for US)
   - Cost: **FREE** (government service)
   - Features: Excellent forecasts, alerts
   - Limitation: US only, no commercial SLA
   - **Monthly cost**: $0

3. **Tomorrow.io (formerly ClimaCell)**
   - Cost: Free up to 500 calls/day, then $5/month
   - Features: Hyperlocal, minute-by-minute precipitation
   - Accuracy: Excellent
   - **Monthly cost**: $0-5

**AI Features**:
- Parse forecast for snow events
- Match forecast to property locations
- Calculate which properties will exceed triggers
- Generate recommended routes
- Send email summary:
  - "Snow forecasted: 3-5" starting 10pm tonight"
  - "12 properties will exceed trigger amounts"
  - "Recommended routes: Downtown (6 props), North Zone (6 props)"
  - "Estimated start time: 11pm"
- Use OpenAI for natural language summaries

**Cost Breakdown**:
- Weather API: $0-10/month
- OpenAI (summaries): ~$1-2/month
- Gmail API: Free
- **Total**: $1-12/month

**Estimated Effort**: 4-5 days
**Dependencies**: Property triggers, Email integration

---

### Phase 4: Business Integrations (v0.7.1 - v0.7.5)

#### 8. **QuickBooks Integration** ⭐⭐ Medium Priority
**Description**: Automated billing and invoicing
**User Story**: "As an admin, I want to automatically generate invoices in QuickBooks based on completed work"

**Technical Requirements**:
- QuickBooks Online API (OAuth 2.0)
- New table: `quickbooks_sync` (log of synced invoices)
- Invoice generation from winter_ops_logs
- Customer matching (property → QuickBooks customer)

**Features**:
- One-click invoice creation
- Batch invoicing (all properties for date range)
- Line items from:
  - Hours worked (equipment × hourly rate)
  - Materials used (salt quantities × price)
- Automatic customer matching
- Sync payment status back to portal
- Monthly reconciliation report

**Cost**:
- QuickBooks API: Free (included with QuickBooks Online subscription)
- User must have QuickBooks Online ($30-200/month - they already have this)

**Estimated Effort**: 5-6 days
**Complexity**: High (OAuth, API integration, error handling)

---

#### 9. **GPS Truck Tracker Integration** ⭐ Medium Priority
**Description**: Real-time vehicle tracking integration
**User Story**: "As a manager, I want to see where my trucks are in real-time"

**Technical Requirements**:
- API integration with GPS providers
- New table: `vehicle_locations` (vehicle_id, lat, lng, timestamp, speed, heading)
- Real-time updates (webhook or polling)
- Display on map

**Supported GPS Providers**:

1. **Samsara** (Commercial fleet tracking)
   - API: RESTful + Webhooks
   - Cost: Included with Samsara subscription ($30-60/vehicle/month)
   - Features: Location, speed, route history, geofencing

2. **Verizon Connect** (Formerly Networkfleet)
   - API: RESTful
   - Cost: Included with subscription
   - Features: Similar to Samsara

3. **Generic GPS Tracker** (Traccar, etc.)
   - API: Various protocols (HTTP, MQTT)
   - Cost: Device cost only ($50-200 one-time)
   - Features: Basic tracking

**Features**:
- Live truck location on map
- Route history / breadcrumb trail
- Geofencing (know when truck arrives at property)
- Speed monitoring
- Idle time tracking
- Auto-update ticket times from GPS (time in/out)

**Cost**:
- API integration: $0 (use existing subscription)
- GPS hardware: User already has if they use fleet tracking

**Estimated Effort**: 4-5 days per provider
**Recommendation**: Start with Samsara (most common in snow industry)

---

#### 10. **Web-Based GPS for Accounts (Optional)** ⭐ Low Priority
**Description**: Simple GPS tracking without dedicated hardware
**User Story**: "As a small contractor, I want to track my location using my phone without buying GPS hardware"

**Technical Requirements**:
- HTML5 Geolocation API
- Mobile-responsive tracking page
- Background location updates (requires user permission)
- Store location history in database

**Features**:
- "Start Tracking" button on mobile
- Automatic location updates every 30 seconds
- Works in background (if browser supports)
- Battery-efficient mode
- Works on any smartphone

**Limitations**:
- Requires browser to stay open
- Less reliable than dedicated GPS
- Battery drain on phone
- No tracking if phone dies

**Cost**: $0 (HTML5 API is free)

**Estimated Effort**: 2-3 days
**Recommendation**: Good for small contractors or backup tracking

---

## Implementation Priority

### Immediate (v0.5.1) - Next 2 Weeks
1. ✅ Property List Filtering (1-2 days)
2. ✅ Filter by Manager/Contractor (1 day)
3. ✅ Snow Trigger Amount (2 days)

### Near-term (v0.5.2-0.5.3) - Weeks 3-4
4. Optional Routes (2-3 days)
5. Route Map View (3-4 days)

### Mid-term (v0.5.4-0.6.0) - Month 2
6. Property Open-By Time Alerts (3-4 days)
7. Weather Monitoring with AI (4-5 days)

### Long-term (v0.7.0+) - Months 3-4
8. QuickBooks Integration (5-6 days)
9. GPS Truck Tracker Integration (4-5 days per provider)
10. Web-Based GPS (optional, 2-3 days)

---

## Cost Summary

### Monthly Operating Costs (After Implementation)

| Feature | Cost Range | Recommended |
|---------|-----------|-------------|
| Weather API | $0-10/month | Weather.gov (free) or OpenWeatherMap ($0-10) |
| AI Summaries | $1-2/month | OpenAI GPT-4o-mini |
| Mapping | $0-5/month | Mapbox (free tier) |
| SMS Alerts | $0.0075/SMS | Twilio (pay per use) |
| Email | Free | Gmail API |
| QuickBooks API | Free | Included with QB subscription |
| GPS Integration | $0 | Use existing subscription |
| **TOTAL** | **$1-17/month** | **~$5-10/month typical** |

### One-Time Costs
- Development time (your cost, not operational)
- GPS hardware (if needed): $50-200 per truck (optional, many already have)

---

## Technical Architecture

### New Database Tables

```sql
-- Routes
CREATE TABLE routes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_template BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE route_properties (
    route_id INT NOT NULL,
    property_id INT NOT NULL,
    sequence_order INT NOT NULL,
    PRIMARY KEY (route_id, property_id)
);

-- Property Lists
CREATE TABLE property_lists (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    is_shared BOOLEAN DEFAULT FALSE,
    filters JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE property_list_items (
    list_id INT NOT NULL,
    property_id INT NOT NULL,
    PRIMARY KEY (list_id, property_id)
);

-- Alerts
CREATE TABLE alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT NOT NULL,
    alert_type ENUM('open_by', 'weather', 'trigger_exceeded'),
    alert_time DATETIME NOT NULL,
    message TEXT,
    sent_at DATETIME,
    acknowledged_at DATETIME,
    acknowledged_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather Cache
CREATE TABLE weather_forecasts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    location_lat DECIMAL(10, 7),
    location_lng DECIMAL(10, 7),
    forecast_time DATETIME,
    snow_amount DECIMAL(5, 2),
    forecast_data JSON,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- GPS Tracking
CREATE TABLE vehicle_locations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_id VARCHAR(100),
    user_id INT,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    speed DECIMAL(5, 2),
    heading INT,
    timestamp DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- QuickBooks Sync
CREATE TABLE quickbooks_sync (
    id INT PRIMARY KEY AUTO_INCREMENT,
    log_id INT NOT NULL,
    quickbooks_invoice_id VARCHAR(100),
    sync_status ENUM('pending', 'synced', 'error'),
    error_message TEXT,
    synced_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Update Existing Tables

```sql
-- Add to locations table
ALTER TABLE locations ADD COLUMN open_by_time TIME DEFAULT NULL;
ALTER TABLE locations ADD COLUMN alert_offset_minutes INT DEFAULT 30;
ALTER TABLE locations ADD COLUMN alert_contacts JSON DEFAULT NULL;
ALTER TABLE locations ADD COLUMN trigger_amount DECIMAL(4, 2) DEFAULT 2.0;
ALTER TABLE locations ADD COLUMN trigger_type ENUM('zero_tolerance', 'accumulation', 'event') DEFAULT 'accumulation';
ALTER TABLE locations ADD COLUMN contract_tier VARCHAR(50) DEFAULT 'Standard';
ALTER TABLE locations ADD COLUMN latitude DECIMAL(10, 7) DEFAULT NULL;
ALTER TABLE locations ADD COLUMN longitude DECIMAL(10, 7) DEFAULT NULL;
```

---

## Next Steps

### Week 1 (Starting Now)
- [x] Create v0.5.1 branch
- [ ] Create ROADMAP_v0.5.1.md (this document)
- [ ] Implement Property List Filtering
- [ ] Add Manager/Contractor filters
- [ ] Add trigger_amount to properties

### Week 2
- [ ] Design Route Management UI
- [ ] Implement Routes backend
- [ ] Start Map View (choose Mapbox)

### Week 3
- [ ] Complete Map View
- [ ] Implement Open-By Time alerts
- [ ] Set up Twilio for SMS

### Week 4
- [ ] Weather API integration (Weather.gov)
- [ ] AI weather decision engine
- [ ] Email alert system

---

## Questions for User

1. **Weather API**: Prefer free (Weather.gov) or paid for better accuracy (OpenWeatherMap $10/mo)?
2. **GPS**: Do you already use Samsara, Verizon Connect, or another tracker?
3. **QuickBooks**: Do you use QuickBooks Online? (Required for API access)
4. **Priority**: Which feature is most urgent for this season?
5. **Budget**: Comfortable with ~$5-10/month in API costs?

---

**Version**: 0.5.1-roadmap
**Created**: 2025-11-20
**Status**: Planning Phase
