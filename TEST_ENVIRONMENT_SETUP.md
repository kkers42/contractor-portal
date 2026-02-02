# Test Environment Setup - Port 1050

## Overview
This document provides step-by-step instructions for setting up a test environment on the VPS at port 1050 with a duplicated database for testing the multi-tenant v0.6.0 implementation.

**VPS:** 72.61.0.186
**Test Port:** 1050
**Test Database:** contractor_portal_test
**Purpose:** Test multi-tenant customer_id implementation before production deployment

---

## Prerequisites

- SSH access to VPS (72.61.0.186)
- Root privileges
- MySQL credentials (contractor/Bimmer325i)
- Multi-tenant code pushed to GitHub branch: feature/v0.6.0-multi-tenant

---

## Step 1: SSH into VPS

```bash
ssh root@72.61.0.186
```

---

## Step 2: Create Test Database

```bash
# Login to MySQL
mysql -u contractor -pBimmer325i

# Create test database
CREATE DATABASE contractor_portal_test;

# Grant permissions
GRANT ALL PRIVILEGES ON contractor_portal_test.* TO 'contractor'@'localhost';
FLUSH PRIVILEGES;

# Exit MySQL
exit;
```

---

## Step 3: Duplicate Production Database to Test

```bash
# Dump production database
mysqldump -u contractor -pBimmer325i contractor_portal > /tmp/contractor_portal_dump.sql

# Import into test database
mysql -u contractor -pBimmer325i contractor_portal_test < /tmp/contractor_portal_dump.sql

# Verify tables copied
mysql -u contractor -pBimmer325i contractor_portal_test -e "SHOW TABLES;"

# Clean up dump file
rm /tmp/contractor_portal_dump.sql
```

Expected output should show all tables:
- users
- locations
- winter_ops_logs
- winter_events
- property_contractors
- routes
- property_lists
- equipment_rates
- weather_data
- sms_context
- api_keys
- jobber_auth
- quickbooks_auth
- event_checkins
- (and any other tables)

---

## Step 4: Run Multi-Tenant Migrations on Test Database

```bash
# Navigate to project directory
cd /opt/contractor-portal

# Checkout multi-tenant branch
git fetch origin
git checkout feature/v0.6.0-multi-tenant

# Run migration 001 - Create customers table
mysql -u contractor -pBimmer325i contractor_portal_test < app/migrations/001_create_customers_table.sql

# Verify customers table created
mysql -u contractor -pBimmer325i contractor_portal_test -e "DESCRIBE customers;"

# Verify LEGACY001 customer created
mysql -u contractor -pBimmer325i contractor_portal_test -e "SELECT * FROM customers;"

# Run migration 002 - Add customer_id to all tables
mysql -u contractor -pBimmer325i contractor_portal_test < app/migrations/002_add_customer_id_to_tables.sql

# Verify customer_id column added to users table
mysql -u contractor -pBimmer325i contractor_portal_test -e "DESCRIBE users;"

# Verify all existing data has customer_id = 'LEGACY001'
mysql -u contractor -pBimmer325i contractor_portal_test -e "SELECT COUNT(*) as total, customer_id FROM users GROUP BY customer_id;"
mysql -u contractor -pBimmer325i contractor_portal_test -e "SELECT COUNT(*) as total, customer_id FROM locations GROUP BY customer_id;"
```

Expected results:
- All tables should have customer_id column
- All existing records should have customer_id = 'LEGACY001'
- Foreign key constraints should be in place

---

## Step 5: Create Test Environment Configuration

```bash
# Create test environment .env file
cd /opt/contractor-portal
cp app/.env app/.env.test

# Edit test .env file
nano app/.env.test
```

Update these values in `.env.test`:
```bash
# Database Configuration
DB_NAME=contractor_portal_test
DB_HOST=127.0.0.1
DB_USER=contractor
DB_PASSWORD=Bimmer325i

# Application Settings
PORT=1050
ENVIRONMENT=test

# Keep all other settings the same as production .env
```

---

## Step 6: Create Test Service

```bash
# Create systemd service file for test environment
nano /etc/systemd/system/contractor-portal-test.service
```

Add this content:
```ini
[Unit]
Description=Contractor Portal Test Environment (v0.6.0)
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/contractor-portal
Environment="PATH=/opt/contractor-portal/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/contractor-portal/venv/bin/uvicorn main:app --host 0.0.0.0 --port 1050 --app-dir /opt/contractor-portal/app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## Step 7: Update Nginx for Test Environment

```bash
# Edit nginx configuration
nano /etc/nginx/sites-available/contractor-portal-test
```

Add this configuration:
```nginx
server {
    listen 1050;
    server_name 72.61.0.186;

    location / {
        proxy_pass http://localhost:1050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/contractor-portal/app/static/;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/contractor-portal-test /etc/nginx/sites-enabled/

# Test nginx configuration
nginx -t

# Reload nginx
systemctl reload nginx
```

---

## Step 8: Start Test Environment

```bash
# Reload systemd to recognize new service
systemctl daemon-reload

# Enable test service to start on boot
systemctl enable contractor-portal-test

# Start test service
systemctl start contractor-portal-test

# Check status
systemctl status contractor-portal-test

# View logs
journalctl -u contractor-portal-test -n 50 --no-pager

# Follow logs in real-time
journalctl -u contractor-portal-test -f
```

---

## Step 9: Verify Test Environment

```bash
# Test that service is listening on port 1050
lsof -i :1050

# Test API endpoint
curl http://localhost:1050/

# Test from external machine
curl http://72.61.0.186:1050/
```

Expected: Should return the Home.html page

---

## Step 10: Create Test Customers for Multi-Tenant Testing

```bash
# Login to test database
mysql -u contractor -pBimmer325i contractor_portal_test

# Create second test customer
INSERT INTO customers (
    customer_id,
    company_name,
    contact_name,
    contact_email,
    status,
    subscription_tier,
    max_users,
    max_properties,
    features
) VALUES (
    'TEST0001',
    'Test Company A',
    'Test Admin',
    'test@example.com',
    'active',
    'enterprise',
    50,
    500,
    '{"jobber": true, "quickbooks": true, "sms": true, "weather": true, "ai": true}'
);

# Create third test customer
INSERT INTO customers (
    customer_id,
    company_name,
    contact_name,
    contact_email,
    status,
    subscription_tier,
    max_users,
    max_properties,
    features
) VALUES (
    'TEST0002',
    'Test Company B',
    'Test Admin',
    'test2@example.com',
    'active',
    'professional',
    20,
    200,
    '{"jobber": false, "quickbooks": true, "sms": true, "weather": true, "ai": false}'
);

# Create test users for TEST0001
INSERT INTO users (
    name,
    phone,
    username,
    email,
    role,
    password,
    password_hash,
    status,
    customer_id
) VALUES (
    'Test Admin A',
    '555-0001',
    'testadmin1',
    'testadmin1@test.com',
    'Admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFAOj4LBgi',  -- password: test123
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFAOj4LBgi',
    'active',
    'TEST0001'
);

# Create test users for TEST0002
INSERT INTO users (
    name,
    phone,
    username,
    email,
    role,
    password,
    password_hash,
    status,
    customer_id
) VALUES (
    'Test Admin B',
    '555-0002',
    'testadmin2',
    'testadmin2@test.com',
    'Admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFAOj4LBgi',  -- password: test123
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYFAOj4LBgi',
    'active',
    'TEST0002'
);

# Create test properties for TEST0001
INSERT INTO locations (
    name,
    address,
    sqft,
    area_manager,
    plow,
    salt,
    customer_id
) VALUES (
    'Test Property A1',
    '123 Test St, Test City A',
    5000,
    'Test Manager A',
    TRUE,
    TRUE,
    'TEST0001'
);

# Create test properties for TEST0002
INSERT INTO locations (
    name,
    address,
    sqft,
    area_manager,
    plow,
    salt,
    customer_id
) VALUES (
    'Test Property B1',
    '456 Test Ave, Test City B',
    7500,
    'Test Manager B',
    TRUE,
    TRUE,
    'TEST0002'
);

# Verify data isolation
SELECT 'LEGACY001 Users:' as label, COUNT(*) as count FROM users WHERE customer_id = 'LEGACY001'
UNION ALL
SELECT 'TEST0001 Users:', COUNT(*) FROM users WHERE customer_id = 'TEST0001'
UNION ALL
SELECT 'TEST0002 Users:', COUNT(*) FROM users WHERE customer_id = 'TEST0002'
UNION ALL
SELECT 'LEGACY001 Properties:', COUNT(*) FROM locations WHERE customer_id = 'LEGACY001'
UNION ALL
SELECT 'TEST0001 Properties:', COUNT(*) FROM locations WHERE customer_id = 'TEST0001'
UNION ALL
SELECT 'TEST0002 Properties:', COUNT(*) FROM locations WHERE customer_id = 'TEST0002';

exit;
```

---

## Step 11: Test Multi-Tenant Data Isolation

### Test 1: Login as LEGACY001 user
```bash
# Login with existing production user
curl -X POST http://72.61.0.186:1050/api/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@contractor.local&password=ContractorAdmin2025!"

# Save the access_token from response
```

### Test 2: Verify LEGACY001 can only see their data
```bash
# Use token to get properties
curl http://72.61.0.186:1050/properties/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Expected: Should see all LEGACY001 properties, but NOT TEST0001 or TEST0002 properties
```

### Test 3: Login as TEST0001 user
```bash
curl -X POST http://72.61.0.186:1050/api/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testadmin1@test.com&password=test123"
```

### Test 4: Verify TEST0001 can only see their data
```bash
curl http://72.61.0.186:1050/properties/ \
  -H "Authorization: Bearer YOUR_TEST0001_TOKEN"

# Expected: Should see only TEST0001 properties
```

### Test 5: Verify data isolation at database level
```bash
mysql -u contractor -pBimmer325i contractor_portal_test -e "
SELECT
    'User can see their properties' as test_case,
    COUNT(*) as count
FROM locations
WHERE customer_id = 'TEST0001';

SELECT
    'User cannot see other customer properties' as test_case,
    COUNT(*) as count
FROM locations
WHERE customer_id = 'TEST0002';
"
```

---

## Step 12: Test Customer Management API

### Test as Super Admin
```bash
# Get all customers
curl http://72.61.0.186:1050/api/customers/ \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"

# Get specific customer
curl http://72.61.0.186:1050/api/customers/TEST0001 \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"

# Get customer usage stats
curl http://72.61.0.186:1050/api/my-customer/usage \
  -H "Authorization: Bearer TEST0001_TOKEN"
```

---

## Troubleshooting

### Service won't start
```bash
# Check logs
journalctl -u contractor-portal-test -n 100 --no-pager

# Check if port is already in use
lsof -i :1050

# Check if venv has dependencies
/opt/contractor-portal/venv/bin/pip list | grep -E "fastapi|uvicorn|mysql"
```

### Database connection errors
```bash
# Test MySQL connection
mysql -u contractor -pBimmer325i contractor_portal_test -e "SELECT 1;"

# Check if migrations ran
mysql -u contractor -pBimmer325i contractor_portal_test -e "SHOW TABLES LIKE 'customers';"
```

### Nginx errors
```bash
# Test nginx config
nginx -t

# Check nginx logs
tail -f /var/log/nginx/error.log
```

---

## Useful Commands

```bash
# Service management
systemctl status contractor-portal-test
systemctl restart contractor-portal-test
systemctl stop contractor-portal-test
systemctl start contractor-portal-test

# View logs
journalctl -u contractor-portal-test -f
journalctl -u contractor-portal-test -n 100 --no-pager

# Database queries
mysql -u contractor -pBimmer325i contractor_portal_test
mysql -u contractor -pBimmer325i contractor_portal_test -e "SELECT customer_id, COUNT(*) FROM users GROUP BY customer_id;"

# Git operations
cd /opt/contractor-portal
git status
git log -5 --oneline
git checkout feature/v0.6.0-multi-tenant
git pull origin feature/v0.6.0-multi-tenant
```

---

## Cleanup (When Done Testing)

```bash
# Stop test service
systemctl stop contractor-portal-test
systemctl disable contractor-portal-test

# Remove service file
rm /etc/systemd/system/contractor-portal-test.service
systemctl daemon-reload

# Remove nginx config
rm /etc/nginx/sites-enabled/contractor-portal-test
rm /etc/nginx/sites-available/contractor-portal-test
nginx -t
systemctl reload nginx

# Drop test database (CAREFUL!)
mysql -u contractor -pBimmer325i -e "DROP DATABASE contractor_portal_test;"

# Remove test .env
rm /opt/contractor-portal/app/.env.test
```

---

## Success Criteria

The test environment is successfully set up when:

1. ✅ Test database exists with all tables
2. ✅ Migrations have run successfully
3. ✅ Service is running on port 1050
4. ✅ Can access test environment at http://72.61.0.186:1050
5. ✅ Multiple test customers exist (LEGACY001, TEST0001, TEST0002)
6. ✅ Test users can login and get JWT tokens
7. ✅ Data isolation is verified (users can only see their customer's data)
8. ✅ Customer management API endpoints work
9. ✅ No errors in service logs
10. ✅ Production environment (port 8000) still works normally

---

## Notes

- Test environment uses same codebase as production (different branch)
- Test database is isolated from production database
- Port 1050 is only for testing, not for public access
- Always test on port 1050 before deploying to production port 8000
- Keep test environment data separate from production
- Document any issues found during testing in GitHub issues

---

## Next Steps After Testing

Once testing is complete and all features verified:

1. Merge feature/v0.6.0-multi-tenant into main branch
2. Run migrations on production database
3. Deploy to production (port 8000)
4. Monitor logs for errors
5. Create first real customer account
6. Update production documentation
