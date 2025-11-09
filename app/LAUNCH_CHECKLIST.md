# Contractor Portal - Launch Checklist

**Repository:** [kkers42/contractor-portal](https://github.com/kkers42/contractor-portal)
**Target Launch Date:** Monday (Production Deployment to Hostinger)
**Current Status:** Testing Phase on Ubuntu Test Server

---

## Pre-Launch Checklist (MUST DO Before Monday)

### Security & Configuration (Critical)

#### 🔴 Priority 1 - Security Hardening
- [ ] **Generate strong JWT secret** - Replace `APP_JWT_SECRET=CHANGE_ME_IN_PRODUCTION`
  - Command: `openssl rand -base64 64`
  - Update in production `.env` file
  - **Impact:** Without this, JWT tokens can be forged

- [ ] **Rotate database passwords**
  - [ ] Change root MySQL password
  - [ ] Change contractor user password
  - [ ] Update `.env` with new passwords
  - **Impact:** Default passwords are security risk

- [ ] **Disable or change backdoor admin credentials**
  - Option 1: Change password in `.env` (BACKDOOR_ADMIN_PASSWORD)
  - Option 2: Set to empty string to disable
  - Option 3: Remove from `.env` entirely
  - **Impact:** Known default credentials = security vulnerability

- [ ] **Restrict CORS origins** in main.py
  - Currently: `allow_origins=["*"]` (allows ALL domains)
  - Change to: `allow_origins=["https://yourdomain.com"]`
  - **Impact:** Prevents unauthorized API access from other sites

- [ ] **Configure SSL/TLS with Let's Encrypt**
  - [ ] Install certbot on Hostinger server
  - [ ] Obtain SSL certificate
  - [ ] Configure nginx/Apache reverse proxy
  - [ ] Update `APP_BASE_URL` in `.env` to use `https://`
  - **Impact:** REQUIRED - passwords sent in plain text without HTTPS

#### 🟡 Priority 2 - Environment Configuration
- [ ] **Update database credentials in production `.env`**
  - DB_HOST (if different from 127.0.0.1)
  - DB_USER
  - DB_PASSWORD
  - DB_NAME

- [ ] **Update APP_BASE_URL in production `.env`**
  - Change from `http://localhost:8080` to production domain
  - Example: `https://contractor-portal.yourdomain.com`
  - Used for OAuth callbacks

- [ ] **Configure email settings** (if email features are used)
  - EMAIL_USER
  - EMAIL_PASSWORD
  - Test email sending functionality

### Testing & Verification

#### 🟢 Priority 3 - Functional Testing
- [ ] **Test backdoor admin login**
  - Navigate to login page
  - Enter: admin@contractor.local / ContractorAdmin2025!
  - Verify successful login and redirect to AdminDashboard
  - Verify Admin role permissions work

- [ ] **Test traditional password signup/login**
  - [ ] Create new user via signup form
  - [ ] Verify user can log in
  - [ ] Test Manager role access
  - [ ] Test User role access

- [ ] **Test admin user management**
  - [ ] Create new user from AdminDashboard
  - [ ] Edit existing user
  - [ ] Delete user
  - [ ] Verify role changes work

- [ ] **Test property management**
  - [ ] Add new property
  - [ ] Edit property
  - [ ] Delete property
  - [ ] Verify properties show in dropdowns

- [ ] **Test operations logging**
  - [ ] Create winter ops log
  - [ ] Create green services log
  - [ ] Verify data saves correctly
  - [ ] Test required field validation

- [ ] **Test report generation**
  - [ ] Report by product (with/without filters)
  - [ ] Report by property (with/without filters)
  - [ ] Report by user (with/without filters)
  - [ ] Verify data accuracy
  - [ ] Test date range filtering

- [ ] **Test role-based access control**
  - [ ] Verify Admin can access all pages
  - [ ] Verify Manager cannot access admin-only pages
  - [ ] Verify User cannot access manager/admin pages
  - [ ] Test 403 errors for unauthorized access

### Database & Deployment

#### 🟡 Priority 4 - Database Preparation
- [ ] **Run database migration on production server**
  ```bash
  mysql -u root -p contractor_portal < migrations/2025-10-31_oauth_identities_v2.sql
  ```

- [ ] **Verify database schema**
  - [ ] Check users table has all columns (status, display_name, etc.)
  - [ ] Check identities table exists
  - [ ] Verify indexes are created
  - [ ] Check all foreign keys are valid

- [ ] **Seed initial data** (if needed)
  - [ ] Create first admin user (or rely on backdoor)
  - [ ] Add initial properties
  - [ ] Add landscape products

- [ ] **Set up database backups**
  - [ ] Configure daily automated backups
  - [ ] Test backup restoration process
  - Recommendation: Cron job with mysqldump

#### 🟢 Priority 5 - Server Deployment
- [ ] **Clone repository to Hostinger server**
  ```bash
  cd /opt
  git clone https://github.com/kkers42/contractor-portal.git
  cd contractor-portal
  git checkout feature/passwordless-sso
  ```

- [ ] **Set up Python virtual environment**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] **Create production `.env` file**
  - Copy from `.env.example`
  - Fill in all production values
  - Secure file permissions: `chmod 600 .env`

- [ ] **Configure systemd service**
  - Copy service file from test server or create new
  - Enable service: `sudo systemctl enable contractor-portal`
  - Start service: `sudo systemctl start contractor-portal`
  - Verify status: `sudo systemctl status contractor-portal`

- [ ] **Configure firewall**
  - Allow port 8080 (or proxy port)
  - Block direct database access from outside
  - Configure fail2ban for SSH protection

### Documentation & Handoff

#### 🟡 Priority 6 - Documentation
- [ ] **Update README.md with production info**
  - Server access instructions
  - Environment variables list
  - Deployment process

- [ ] **Document admin procedures**
  - How to approve new users
  - How to create/manage users
  - How to access reports

- [ ] **Create backup/restore guide**
  - Database backup commands
  - Restoration procedure
  - Emergency contacts

---

## Post-Launch Improvements (Can Do After Monday)

### Performance & Optimization

#### Phase 1 - Immediate Post-Launch (Week 1)
- [ ] **Add request rate limiting**
  - Library: slowapi or fastapi-limiter
  - Target: `/api/login/` endpoint (prevent brute force)
  - Rate: 5 login attempts per minute per IP

- [ ] **Implement connection pooling**
  - Configure MySQL connection pool
  - Set max connections limit
  - Add connection timeout

- [ ] **Add application logging**
  - Log all login attempts (success and failure)
  - Log admin actions (user creation, role changes)
  - Log API errors and exceptions
  - Use Python logging module or loguru

- [ ] **Set up monitoring**
  - Server uptime monitoring
  - Application health checks
  - Database connection monitoring
  - Alert on service failures

### Feature Enhancements

#### Phase 2 - Feature Improvements (Week 2-3)
- [ ] **OAuth Provider Configuration** (Optional)
  - [ ] Set up Google OAuth
  - [ ] Set up Microsoft OAuth
  - [ ] Test OAuth signup flow
  - [ ] Test OAuth login flow
  - [ ] Test pending user approval workflow

- [ ] **Password complexity requirements**
  - Minimum 8 characters
  - Must contain: uppercase, lowercase, digit, special char
  - Check against common password lists
  - Add password strength indicator on signup

- [ ] **Email notifications**
  - New user signup notification (to admin)
  - Account approval notification (to user)
  - Password reset functionality
  - Welcome email after approval

- [ ] **Session management improvements**
  - Implement refresh tokens
  - Add "Remember me" functionality
  - Configurable session timeout
  - Auto-logout after inactivity

- [ ] **Audit logging**
  - Track all admin actions
  - Log data modifications
  - Record login history
  - Export audit logs

#### Phase 3 - UI/UX Improvements (Week 4+)
- [ ] **Responsive mobile design**
  - Mobile-friendly login/signup
  - Touch-optimized dashboards
  - Mobile operations logging

- [ ] **Dashboard improvements**
  - Add charts/graphs for reports
  - Real-time data updates
  - Quick stats on dashboard
  - Recent activity feed

- [ ] **Report enhancements**
  - Export to PDF
  - Export to Excel/CSV
  - Email reports to managers
  - Scheduled report generation

- [ ] **Property/Operations features**
  - Attach photos to operations logs
  - GPS location tracking
  - Weather integration
  - Mobile app for field workers

### Advanced Features

#### Phase 4 - Advanced Capabilities (Future)
- [ ] **Multi-tenant support**
  - Support multiple contractor companies
  - Company-level data isolation
  - Company branding customization

- [ ] **Client portal**
  - Clients can view their properties
  - Clients can see service history
  - Clients can approve/request services

- [ ] **Invoice generation**
  - Generate invoices from operations logs
  - Track payment status
  - Send invoices to clients

- [ ] **Mobile application**
  - Native iOS/Android apps
  - Offline operation logging
  - Photo uploads from field
  - Push notifications

- [ ] **API for integrations**
  - RESTful API documentation
  - API keys for third-party access
  - Webhooks for events
  - Integration with QuickBooks/accounting software

---

## Overlapping Items (Can Be Done Pre or Post Launch)

These items could be done before launch (if time permits) or after launch (lower priority):

### Can Do Either Time
- [ ] **OAuth configuration** - Works without it, but nice to have
- [ ] **Rate limiting** - Security feature, but not blocking
- [ ] **Email notifications** - Nice to have, not critical
- [ ] **Logging improvements** - Useful for debugging, but not required
- [ ] **Monitoring setup** - Important but can be added post-launch
- [ ] **Password complexity** - Security improvement, not blocking

### Recommended Approach
- **Before launch:** Focus on security (JWT secrets, CORS, HTTPS, passwords)
- **After launch:** Focus on features (OAuth, emails, monitoring, UX)

---

## Risk Assessment

### High Risk (Must Fix Before Launch)
🔴 No HTTPS → Passwords sent in plain text
🔴 Default JWT secret → Tokens can be forged
🔴 CORS allows all origins → API exposed to any website
🔴 Backdoor admin with known password → Unauthorized access

### Medium Risk (Should Fix Soon)
🟡 No rate limiting → Vulnerable to brute force
🟡 No audit logging → Can't track suspicious activity
🟡 No monitoring → Won't know if service goes down
🟡 No backups configured → Risk of data loss

### Low Risk (Nice to Have)
🟢 OAuth not configured → Still have password login
🟢 No email notifications → Manual communication works
🟢 Basic UI → Functional but could be prettier
🟢 No mobile optimization → Desktop works fine

---

## Launch Day Checklist

### Final Pre-Launch (1-2 hours before)
- [ ] Pull latest code from GitHub
- [ ] Run database migration
- [ ] Verify all environment variables set
- [ ] Test backdoor login one last time
- [ ] Create first real admin user
- [ ] Disable backdoor admin
- [ ] Restart application service
- [ ] Verify service is running
- [ ] Test from external network

### Post-Launch Monitoring (First 24 hours)
- [ ] Monitor server logs for errors
- [ ] Check application is accessible
- [ ] Test login from multiple locations
- [ ] Verify database connections stable
- [ ] Monitor server resource usage (CPU, memory, disk)
- [ ] Have rollback plan ready

### Emergency Rollback Plan
If something goes wrong:
1. Stop the service: `sudo systemctl stop contractor-portal`
2. Restore previous code version
3. Restore database backup (if schema changed)
4. Restart service with old version
5. Notify users of maintenance window

---

## Summary

**Pre-Launch Must-Do (6 Critical Items):**
1. Generate JWT secret
2. Configure HTTPS/SSL
3. Restrict CORS
4. Change/disable backdoor admin
5. Test all core functionality
6. Set up database backups

**Time Estimate:** 4-6 hours for pre-launch tasks

**Post-Launch Priority (First Week):**
1. Rate limiting
2. Logging
3. Monitoring
4. OAuth configuration (optional)

**Total Post-Launch Items:** 20+ improvements identified

---

## Contact & Support

**Developer:** Claude Code
**Repository:** https://github.com/kkers42/contractor-portal
**Branch:** feature/passwordless-sso
**Documentation:** See CHANGES_SUMMARY.md, INSTALL_GUIDE.md, PROJECT_TRACKING.md

For issues or questions, refer to PROJECT_TRACKING.md for detailed implementation guidance.
