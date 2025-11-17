# User Role Equivalence Summary

## Overview
The "User" role has been made equivalent to the "Subcontractor" role throughout the entire Contractor Portal application.

## Changes Made

### Frontend Access Control (12 HTML Files Updated)
All pages that previously allowed only `['Admin', 'Manager', 'Subcontractor']` now allow `['Admin', 'Manager', 'Subcontractor', 'User']`:

1. **UserDashboard.html** - Changed from `checkAccess(['Subcontractor'])` to `checkAccess(['Subcontractor', 'User'])`
2. **EquipmentUsageReport.html** - Added 'User' role
3. **GreenOpsAdmin.html** - Added 'User' role
4. **GreenOpsLog.html** - Added 'User' role
5. **LawnMowing.html** - Added 'User' role
6. **PropertyInfo.html** - Added 'User' role
7. **Reports.html** - Added 'User' role
8. **SnowRemoval.html** - Added 'User' role
9. **ViewGreenLogs.html** - Added 'User' role
10. **ViewWinterLogs.html** - Added 'User' role
11. **WinterOpsAdmin.html** - Added 'User' role
12. **WinterOpsLog.html** - Added 'User' role

### Backend Access Control
**equipment_routes.py** - Line 20: Updated to hide pricing for both User and Subcontractor roles:
```python
# Hide pricing information for Subcontractors and Users
if rates and current_user["role"] in ["Subcontractor", "User"]:
    for rate in rates:
        rate["hourly_rate"] = None
```

### Documentation Updates
**create_system_map.py** and **ContractorPortal_SystemMap.xlsx**:
- Added "User" column to Role Access Matrix
- Updated all role descriptions to include "User"
- Added "My Active Tickets" feature to documentation
- Updated navigation flow to reflect User role access

## User Role Capabilities

Users with the "User" role now have access to:

### ✅ Full Access
- **User Dashboard** - Main dashboard with navigation
- **My Active Tickets** - Start and finish work tickets
- **View Properties** - See all assigned properties
- **Submit Winter Logs** - Log winter operations work
- **Submit Green Logs** - Log landscaping work
- **View Winter Logs** - See winter operations history
- **View Green Logs** - See landscaping history
- **Equipment Usage Report** - View equipment usage (pricing hidden)
- **Generate Reports** - Create and export reports
- **Change Password** - Update their own password

### ❌ No Access
- **Admin Dashboard** - Admin only
- **Manager Dashboard** - Manager/Admin only
- **Manage Users** - Admin only
- **Approve Pending Users** - Admin only
- **Add/Edit/Delete Properties** - Manager/Admin only
- **Manage Equipment Rates** - Manager/Admin only
- **Manage Winter Products** - Manager/Admin only
- **Manage Landscape Products** - Admin only

## Role Comparison Table

| Feature | Admin | Manager | Subcontractor | User |
|---------|-------|---------|---------------|------|
| Login | ✅ | ✅ | ✅ | ✅ |
| User Dashboard | ❌ | ❌ | ✅ | ✅ |
| My Active Tickets | ✅ | ✅ | ✅ | ✅ |
| View Properties | ✅ | ✅ | ✅ | ✅ |
| Submit Logs | ✅ | ✅ | ✅ | ✅ |
| View Logs | ✅ | ✅ | ✅ | ✅ |
| Generate Reports | ✅ | ✅ | ✅ | ✅ |
| View Equipment Rates | ✅ (with pricing) | ✅ (with pricing) | ✅ (no pricing) | ✅ (no pricing) |
| Manage Properties | ✅ | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ | ❌ |
| Manage Equipment | ✅ | ✅ | ❌ | ❌ |

## Deployment Status

All changes have been deployed to production VPS at `snow-contractor.com`:
- ✅ All HTML files updated and deployed
- ✅ Backend route updated and service restarted
- ✅ Documentation updated and committed to git

## Testing Recommendations

When testing the User role, verify:
1. ✅ Can log in successfully
2. ✅ Redirected to UserDashboard.html
3. ✅ Can access all Subcontractor features
4. ✅ Cannot access Admin/Manager features
5. ✅ Equipment pricing is hidden
6. ✅ Can start and finish tickets via My Active Tickets
7. ✅ Can view assigned properties
8. ✅ Can submit winter and green logs

## Notes

- **User** and **Subcontractor** roles are now functionally identical
- Both roles have pricing information hidden from equipment rates
- Both roles redirect to the same UserDashboard after login
- The primary difference is the role name in the database and JWT token

## Related Files

- Frontend: `app/static/*.html` (12 files)
- Backend: `app/routes/equipment_routes.py`
- Documentation: `app/create_system_map.py`, `app/ContractorPortal_SystemMap.xlsx`
- Auth: `app/routes/auth_routes.py` (already had "User" in valid_roles)

---

**Last Updated:** 2025-11-16
**Deployed By:** Claude Code
**Git Commit:** fb06daf - "Make User role equivalent to Subcontractor role"
