# Testing Missing Functionality - URGENT FIX

## Issue Reported:
1. ❌ Ability to edit start/stop dates of events has vanished
2. ❌ Ability to assign logs that are not assigned to an event has vanished

## Endpoints That Should Exist:

### 1. Update Winter Event (Edit Start/End Dates)
**Endpoint:** `PUT /winter-events/{event_id}`
**File:** app/routes/winter_event_routes.py (line 272)
**Status:** ✅ EXISTS in code

**Request Body:**
```json
{
  "event_name": "January Freeze",
  "description": "Optional description",
  "start_date": "2026-01-15T00:00:00",
  "end_date": "2026-01-20T23:59:59"
}
```

**cURL Test:**
```bash
# Get auth token first
TOKEN=$(curl -X POST http://72.61.0.186:1051/api/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice.admin@testcompany-alpha.com&password=TestPass123" \
  | jq -r '.access_token')

# Update event dates
curl -X PUT http://72.61.0.186:1051/winter-events/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Test Event Updated",
    "description": "Updated description",
    "start_date": "2026-01-15T00:00:00",
    "end_date": "2026-01-20T23:59:59"
  }'
```

### 2. Assign Log to Event
**Endpoint:** `PUT /winter-logs/{log_id}/assign-to-event`
**File:** app/routes/ops_routes.py (line 271)
**Status:** ✅ EXISTS in code

**Request Body:**
```json
{
  "winter_event_id": 1
}
```

**cURL Test:**
```bash
# Assign log ID 123 to event ID 1
curl -X PUT http://72.61.0.186:1051/winter-logs/123/assign-to-event \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"winter_event_id": 1}'
```

## Verification Steps:

1. **Check if endpoints are registered in main.py:**
```bash
grep -n "winter_event_routes" /opt/contractor-portal/app/main.py
grep -n "ops_routes" /opt/contractor-portal/app/main.py
```

2. **Test on production vs test:**
- Production: https://snow-contractor.com
- Test: http://72.61.0.186:1051

3. **Check frontend calls:**
Look for JavaScript fetch/axios calls to these endpoints in:
- app/static/ManageWinterEvents.html
- app/static/ViewWinterLogs.html
- app/static/WinterOpsLog.html

## Likely Causes:

1. ✅ Code exists - endpoints are in the route files
2. ⚠️ May not be deployed to production (only in test environment)
3. ⚠️ Frontend might be calling wrong endpoint URLs
4. ⚠️ Authorization might be failing

## Fix Actions:

1. Deploy latest code to production
2. Verify frontend is calling correct endpoints
3. Check for JavaScript errors in browser console
4. Verify JWT tokens contain required fields

## Quick Test Script:

```bash
#!/bin/bash

# Test endpoints exist
echo "Testing if endpoints are accessible..."

# Login
echo "1. Login..."
RESPONSE=$(curl -s -X POST http://72.61.0.186:1051/api/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice.admin@testcompany-alpha.com&password=TestPass123")

TOKEN=$(echo $RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ]; then
  echo "❌ Login failed!"
  exit 1
fi

echo "✅ Login successful"

# Test get events
echo "2. Get winter events..."
curl -s -X GET http://72.61.0.186:1051/winter-events/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Test get logs
echo "3. Get winter logs..."
curl -s -X GET http://72.61.0.186:1051/winter-logs/ \
  -H "Authorization: Bearer $TOKEN" | jq '. | length'

echo "✅ Endpoints are working"
```

## IMMEDIATE ACTION REQUIRED:

The functionality IS in the code. We need to:
1. ✅ Deploy to test environment (DONE)
2. ⏳ Test the endpoints
3. ⏳ Deploy to production if tests pass
4. ⏳ Verify frontend is using correct URLs
