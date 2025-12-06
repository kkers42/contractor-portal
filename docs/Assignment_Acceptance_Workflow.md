# Assignment Acceptance Workflow

## Overview
The assignment acceptance system provides accountability and tracking for property and route assignments while maintaining flexibility for emergency or ad-hoc work.

## Design Philosophy

### ✅ Assignment Workflow (Property Board & Routes)
- **Purpose**: Formal assignment tracking and acceptance
- **Visual Indicators**: Yellow glow for pending, green for accepted
- **Enforcement**: Optional - provides visibility and accountability
- **Use Case**: Planned work, scheduled routes, regular assignments

### ✅ Backup: Unrestricted Log Submission
- **Purpose**: Emergency and ad-hoc work can always be logged
- **Access**: ALL contractors, subcontractors, and users
- **No Restrictions**: Can submit logs for ANY property
- **Use Case**: Storm emergencies, urgent repairs, unplanned work

## Why This Matters

### Assignment System Benefits:
1. **Accountability** - Track who accepted which assignments
2. **Planning** - See assignment acceptance status at a glance
3. **Workflow** - Sequential route completion (finish one property before starting next)
4. **History** - Complete audit trail of assignments, acceptances, and declines

### Open Log Submission Benefits:
1. **Emergency Response** - During storms, anyone can log work immediately
2. **Flexibility** - Contractors can help at any property without admin intervention
3. **No Bottlenecks** - Work isn't blocked by assignment bureaucracy
4. **Backup Option** - System continues to function even if assignment workflow breaks

## How It Works

### Property Board Assignment Flow:
```
1. Manager assigns Contractor to Property
   → Status: PENDING (yellow pulsing glow)
   → Assignment tracked in property_contractors table

2. Contractor accepts assignment
   → Status: ACCEPTED (green glow)
   → accepted_at timestamp recorded
   → Shows "✓ ACCEPTED" badge

3. Contractor performs work
   → Submits winter ops log
   → Log created for that property
   → No validation of assignment required
```

### Route Assignment Flow:
```
1. Manager assigns Contractor to Route
   → Status: PENDING
   → Route contains multiple properties

2. Contractor accepts route
   → Status: ACCEPTED
   → Can now start properties

3. Contractor starts Property #1
   → current_property_id set
   → current_property_started_at recorded
   → Cannot start Property #2 until #1 is completed

4. Contractor completes Property #1
   → Submits winter ops log
   → Marks property complete
   → current_property_id cleared
   → Can now start Property #2

5. Repeat for all properties in route
```

### Emergency/Ad-Hoc Work Flow:
```
1. Storm hits unexpectedly
2. Contractor goes to any property (assigned or not)
3. Performs work
4. Opens WinterOpsLog.html
5. Selects ANY property from dropdown
6. Submits log successfully
7. Work is recorded - no assignment required
```

## Visual Indicators

### Property Board:
- **Yellow Pulsing Glow** + "⏳ PENDING" = Waiting for contractor acceptance
- **Green Glow** + "✓ ACCEPTED" = Contractor accepted assignment
- **Gray Faded** + "✗ DECLINED" = Contractor declined assignment

### Route Board:
- Similar visual indicators
- Additional tracking: current property being worked on
- Prevents starting multiple properties simultaneously

## Database Schema

### property_contractors
- `acceptance_status` - ENUM('pending', 'accepted', 'declined')
- `accepted_at` - DATETIME (when contractor accepted)
- `declined_at` - DATETIME (when contractor declined)

### route_assignments
- `acceptance_status` - ENUM('pending', 'accepted', 'declined')
- `accepted_at` - DATETIME
- `declined_at` - DATETIME
- `current_property_id` - INT (which property is being worked on)
- `current_property_started_at` - DATETIME

### assignment_history
- Complete audit trail of all actions
- Tracks: assigned, accepted, declined, started, completed

## API Endpoints

### Property Assignments
- `GET /my-assignments/properties` - View your assignments
- `POST /assignments/property/{id}/accept` - Accept assignment
- `POST /assignments/property/{id}/decline` - Decline assignment

### Route Assignments
- `GET /my-assignments/routes` - View your route assignments
- `POST /assignments/route/{id}/accept` - Accept route
- `POST /assignments/route/{id}/decline` - Decline route
- `POST /assignments/route/{id}/start-property/{property_id}` - Start property
- `POST /assignments/route/{id}/complete-property` - Complete current property

### Winter Ops Logs (Unrestricted)
- `POST /submit-winter-log/` - Submit log for ANY property
- `GET /winter-logs/` - View all logs
- **No assignment validation** - Always works

## Best Practices

### For Managers:
1. **Assign properties proactively** - Use Property Board to assign contractors
2. **Monitor acceptance** - Yellow glow indicates pending acceptance
3. **Plan routes** - Use routes for sequential work
4. **Trust the system** - Logs can be submitted regardless of assignments

### For Contractors:
1. **Accept assignments promptly** - Clear yellow glows to green
2. **Follow route sequence** - Complete one property before starting next
3. **Log all work** - Even work at unassigned properties
4. **Communicate declines** - If declining, add a note explaining why

### For Emergencies:
1. **Work first, paperwork later** - Respond to emergencies immediately
2. **Log everything** - Submit logs for all work performed
3. **Don't worry about assignments** - Log submission always works
4. **Update assignments later** - Managers can assign retroactively

## Edge Cases Handled

### Contractor logs work at unassigned property:
- ✅ Log submission succeeds
- ⚠️ No assignment record in property_contractors
- 📋 Log appears in reports normally
- 👤 Manager can assign retroactively if needed

### Contractor declines assignment but does work anyway:
- ✅ Log submission succeeds
- 📋 Assignment shows "DECLINED"
- 💡 Manager sees both decline and completed work
- 🔄 Can discuss and update assignment status

### Route property started but not completed:
- 🔒 Blocks starting next property
- ✅ Can still submit log for current property
- 🔄 Mark complete to unblock next property
- ⚠️ Manager can see which property is in progress

### Multiple contractors at same property:
- ✅ All can submit logs
- ✅ All assignments tracked independently
- 📊 Reports show all work performed
- 🏆 Primary contractor designation available

## Future Enhancements (Optional)

### Possible Additions:
- Notification when contractor accepts/declines
- Auto-decline after X hours
- Bulk acceptance for route assignments
- Performance metrics by acceptance speed
- Gamification: badges for quick acceptance

### NOT Planned:
- ❌ Blocking log submission for unassigned properties
- ❌ Requiring acceptance before work
- ❌ Preventing work at declined properties
- ❌ Strict enforcement of assignments

## Summary

The assignment acceptance workflow adds **visibility and accountability** without creating **bottlenecks or restrictions**. The system encourages proper assignment management while ensuring that work can always be logged, especially during emergencies.

**Key Principle**: *Assignments guide workflow; they don't gate it.*
