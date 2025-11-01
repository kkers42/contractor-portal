# Contractor Portal - Project Tracking

**Repository:** [kkers42/contractor-portal](https://github.com/kkers42/contractor-portal)
**Branch:** feature/passwordless-sso
**Last Updated:** November 1, 2025

---

## How to Use This File with GitHub Projects

### Quick Start:
1. Go to https://github.com/kkers42/contractor-portal/projects
2. Create a new Project (Board view)
3. Name it: "Contractor Portal Development"
4. Create Issues from the tasks below
5. Add Issues to your Project board

---

## Epic 1: Critical Bug Fixes and Setup
**Status:** ✅ COMPLETE

### Issue #1: Fix Import Error in db/identities.py
- **Status:** ✅ Completed
- **Priority:** Critical
- **Labels:** bug, backend, blocking
- **Description:** Fixed ModuleNotFoundError preventing application startup
- **Solution:**
  - Created db/ package structure (db/__init__.py, db/db.py)
  - Added get_conn alias for compatibility
  - Fixed emoji encoding issues
- **Commit:** [View Changes](https://github.com/kkers42/contractor-portal/tree/feature/passwordless-sso)

### Issue #2: Add Backdoor Admin Credentials
- **Status:** ✅ Completed
- **Priority:** High
- **Labels:** feature, auth, security
- **Description:** Added default admin login for fresh installations
- **Credentials:** admin@contractor.local / ContractorAdmin2025!
- **Location:** routes/auth_routes.py:65-72
- **Environment Variables:**
  - BACKDOOR_ADMIN_EMAIL
  - BACKDOOR_ADMIN_PASSWORD

### Issue #3: Secure Environment Variables
- **Status:** ✅ Completed
- **Priority:** Critical
- **Labels:** security, config
- **Description:** Prevent credentials from being committed to git
- **Changes:**
  - Added .env to .gitignore
  - Created .env.example template
  - Added SQL backup files to gitignore

### Issue #4: Add Input Validation to Report Routes
- **Status:** ✅ Completed
- **Priority:** Medium
- **Labels:** enhancement, backend, security
- **Description:** Added Pydantic models for type validation
- **Changes:**
  - Created ReportFilters model
  - Added type hints for all parameters
- **Note:** SQL injection was NOT present - code already used parameterized queries

### Issue #5: Database Migration for OAuth Support
- **Status:** ✅ Completed
- **Priority:** High
- **Labels:** database, feature
- **Description:** Add OAuth columns and identities table
- **Migration File:** migrations/2025-10-31_oauth_identities_v2.sql
- **Changes:**
  - Added columns: display_name, avatar_url, last_login_at, status
  - Created identities table for OAuth providers
  - Added indexes for performance

---

## Epic 2: Server Deployment
**Status:** ✅ COMPLETE

### Issue #6: Ubuntu Server Deployment
- **Status:** ✅ Completed
- **Priority:** Critical
- **Labels:** deployment, infrastructure
- **Environment:**
  - OS: Ubuntu 24.04 LTS
  - Python: 3.12
  - MySQL: 8.0+
  - Service: systemd (contractor-portal.service)
- **Deployment Steps:**
  1. Cloned repository from GitHub
  2. Created Python virtual environment
  3. Installed dependencies (including httpx fix)
  4. Created MySQL user with mysql_native_password
  5. Ran database migration
  6. Configured systemd service
  7. Service running on port 8080

### Issue #7: Fix Port Configuration
- **Status:** ✅ Completed
- **Priority:** High
- **Labels:** bug, frontend, config
- **Description:** Fixed port mismatch and added local network detection
- **Changes:**
  - Changed port from 8000 to 8080 in config.js
  - Added detection for 192.168.x.x, 10.x.x.x, 172.16-31.x.x
  - Made API_BASE_URL dynamic based on hostname

### Issue #8: Resolve httpx Dependency Issue
- **Status:** ✅ Completed
- **Priority:** Critical
- **Labels:** bug, dependencies, blocking
- **Description:** Application failed to start due to missing httpx module
- **Root Cause:** authlib requires httpx for OAuth functionality
- **Solution:** Installed all requirements via pip install -r requirements.txt

---

## Epic 3: Testing and Verification
**Status:** 🟡 IN PROGRESS

### Issue #9: Test Backdoor Admin Login
- **Status:** 🔲 To Do
- **Priority:** High
- **Labels:** testing, auth
- **Description:** Verify backdoor login works on Ubuntu server
- **Test Steps:**
  1. Navigate to login page
  2. Enter: admin@contractor.local / ContractorAdmin2025!
  3. Verify successful login and redirect to admin dashboard
  4. Check JWT token is properly generated
- **Acceptance Criteria:**
  - Login succeeds without database user
  - Admin role is assigned
  - Can access admin-only features

### Issue #10: Test Existing User Login
- **Status:** 🔲 To Do
- **Priority:** High
- **Labels:** testing, auth
- **Description:** Verify password-based login still works
- **Test Steps:**
  1. Create test user via backdoor admin
  2. Log out
  3. Log in with test user credentials
  4. Verify role-based access controls

### Issue #11: Test Report Generation
- **Status:** 🔲 To Do
- **Priority:** Medium
- **Labels:** testing, reports
- **Description:** Verify all report endpoints work correctly
- **Test Cases:**
  - Report by product
  - Report by property
  - Report by user
  - Test with filters: date range, property_id, user_id

### Issue #12: Test Role-Based Access Control
- **Status:** 🔲 To Do
- **Priority:** High
- **Labels:** testing, security, auth
- **Description:** Verify RBAC works across all roles
- **Test Scenarios:**
  - Admin can access all pages
  - Manager can access manager pages only
  - User/Subcontractor can access user pages only
  - Verify 403 errors for unauthorized access

---

## Epic 4: OAuth Integration (Optional)
**Status:** 🔲 TO DO

### Issue #13: Configure Google OAuth
- **Status:** 🔲 To Do
- **Priority:** Low
- **Labels:** feature, oauth, google
- **Description:** Set up Google Sign-In
- **Setup Steps:**
  1. Go to Google Cloud Console
  2. Create OAuth 2.0 credentials
  3. Set redirect URI: http://your-server:8080/auth/google/callback
  4. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env
- **Documentation:** [OAUTH_SETUP_GUIDE.md](OAUTH_SETUP_GUIDE.md)

### Issue #14: Configure Microsoft OAuth
- **Status:** 🔲 To Do
- **Priority:** Low
- **Labels:** feature, oauth, microsoft
- **Description:** Set up Microsoft Sign-In
- **Setup Steps:**
  1. Go to Azure Portal
  2. Register new application
  3. Set redirect URI: http://your-server:8080/auth/microsoft/callback
  4. Add MS_CLIENT_ID, MS_CLIENT_SECRET, MS_TENANT to .env

### Issue #15: Test OAuth Signup Flow
- **Status:** 🔲 To Do
- **Priority:** Medium
- **Labels:** testing, oauth
- **Description:** Verify OAuth signup and approval workflow
- **Test Cases:**
  - Google OAuth signup creates pending user
  - Microsoft OAuth signup creates pending user
  - Admin can see pending users
  - Admin can approve/reject users
  - Approved users can log in with OAuth
  - Rejected users are removed from database

---

## Epic 5: Production Readiness
**Status:** 🔲 TO DO

### Issue #16: Generate Strong JWT Secret
- **Status:** 🔲 To Do
- **Priority:** High
- **Labels:** security, config
- **Description:** Replace default JWT secret with cryptographically strong random key
- **Command:** `openssl rand -base64 64`
- **Location:** APP_JWT_SECRET in .env
- **Note:** Deferred for test environment

### Issue #17: Rotate Database Passwords
- **Status:** 🔲 To Do
- **Priority:** High
- **Labels:** security, database
- **Description:** Change default database passwords
- **Affected:**
  - Root MySQL password
  - Contractor user password
  - Update .env file

### Issue #18: Restrict CORS Origins
- **Status:** 🔲 To Do
- **Priority:** High
- **Labels:** security, backend
- **Description:** Limit CORS to specific domains (currently allows all origins)
- **Location:** main.py CORS configuration
- **Recommendation:** Whitelist only production domain

### Issue #19: Add Rate Limiting
- **Status:** 🔲 To Do
- **Priority:** Medium
- **Labels:** security, enhancement
- **Description:** Prevent brute force attacks on login endpoint
- **Suggested Library:** slowapi or fastapi-limiter
- **Target:** /api/login/ endpoint

### Issue #20: Implement Password Complexity Requirements
- **Status:** 🔲 To Do
- **Priority:** Medium
- **Labels:** security, auth
- **Description:** Enforce strong password policy
- **Requirements:**
  - Minimum 8 characters
  - At least one uppercase, lowercase, digit, special char
  - Check against common password lists

### Issue #21: Configure HTTPS with Let's Encrypt
- **Status:** 🔲 To Do
- **Priority:** Critical (for production)
- **Labels:** security, deployment
- **Description:** Enable SSL/TLS for production deployment
- **Steps:**
  1. Install certbot
  2. Obtain SSL certificate
  3. Configure nginx/Apache reverse proxy
  4. Update APP_BASE_URL to use https://

### Issue #22: Set Up Automated Backups
- **Status:** 🔲 To Do
- **Priority:** High
- **Labels:** database, infrastructure
- **Description:** Daily MySQL backups to prevent data loss
- **Solution:** Cron job with mysqldump
- **Retention:** 7 days of backups

---

## Epic 6: Known Issues and Bugs
**Status:** 🔲 TO DO

### Issue #23: Schema Inconsistency - Role Enum
- **Status:** 🔲 To Do
- **Priority:** Medium
- **Labels:** bug, database
- **Description:** Role enum values inconsistent across database and code
- **Problem:**
  - Database: 'Admin', 'Manager', 'Subcontractor'
  - Migration: 'Admin', 'Manager', 'User'
  - Frontend: Mixed usage
- **Solution:** Standardize on one set of role names

### Issue #24: Clean Up Duplicate Migration Files
- **Status:** 🔲 To Do
- **Priority:** Low
- **Labels:** cleanup, database
- **Description:** Multiple migration files causing confusion
- **Files:**
  - migrations/2025-10-31_oauth_identities.sql (incompatible syntax)
  - db/migrations/2025-10-28_passwordless.sql (different schema)
  - migrations/2025-10-31_oauth_identities_v2.sql ✅ (canonical)
- **Action:** Archive old files, document canonical migration

### Issue #25: Investigate Login 401 Errors
- **Status:** 🔲 To Do
- **Priority:** Medium
- **Labels:** bug, auth
- **Description:** Occasional login failures with valid credentials
- **Suspected Cause:** Password hash mismatch or database connection issue
- **Investigation Needed:**
  - Check bcrypt rounds configuration
  - Review database connection pooling
  - Add detailed logging

---

## Statistics

### Completed: 8 issues
### In Progress: 1 issue
### To Do: 16 issues
### Total: 25 issues

### By Epic:
- Epic 1 (Critical Fixes): 5/5 ✅
- Epic 2 (Deployment): 3/3 ✅
- Epic 3 (Testing): 0/4 🔲
- Epic 4 (OAuth): 0/3 🔲
- Epic 5 (Production): 0/7 🔲
- Epic 6 (Known Issues): 0/3 🔲

---

## Quick Commands for GitHub CLI (Optional)

If you install GitHub CLI (`gh`), you can create issues automatically:

```bash
# Install GitHub CLI (Windows)
winget install --id GitHub.cli

# Or download from https://cli.github.com/

# Authenticate
gh auth login

# Create an issue from this file (example)
gh issue create --title "Test Backdoor Admin Login" \
  --body "Verify backdoor login works on Ubuntu server..." \
  --label "testing,auth" \
  --project "Contractor Portal Development"
```

---

## Current Sprint Focus

**Sprint Goal:** Complete testing and verification of core functionality

**Priority Tasks:**
1. Issue #9: Test backdoor admin login
2. Issue #10: Test existing user login
3. Issue #11: Test report generation
4. Issue #12: Test RBAC

**Next Sprint:** Production security hardening (Issues #16-#22)

---

## Notes

- JWT security improvements deferred for test environment
- OAuth configuration is optional based on business requirements
- Production deployment to Hostinger scheduled for Monday
- Test server: Ubuntu 24.04 LTS, running on local network
- Application accessible at http://192.168.x.x:8080
