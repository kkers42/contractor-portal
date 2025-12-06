# SAAS Multi-Tenancy Architecture Plan

## Executive Summary
This document outlines the architecture and implementation plan for converting the Contractor Portal into a multi-tenant SAAS application, allowing multiple independent contractor companies to use the same platform while maintaining complete data isolation.

## 1. Multi-Tenancy Strategy

### Chosen Approach: Row-Level Isolation (Shared Database, Shared Schema)

**Rationale:**
- Cost-effective for scaling (single database instance)
- Easier maintenance and updates (single codebase, single schema)
- Good balance between isolation and efficiency
- Suitable for SMB market (contractor companies)

**Key Characteristics:**
- All tenants share the same database and tables
- Data isolation achieved through `tenant_id` column in all tables
- Application layer enforces tenant-specific data access
- Centralized user management with tenant association

## 2. Database Schema Changes

### 2.1 New Tables

#### `tenants` Table
Stores information about each contractor company (tenant).

```sql
CREATE TABLE tenants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE,
    subdomain VARCHAR(100) NOT NULL UNIQUE,
    custom_domain VARCHAR(255) NULL,

    -- Contact Information
    admin_email VARCHAR(255) NOT NULL,
    admin_phone VARCHAR(50) NULL,

    -- Subscription Management
    subscription_tier ENUM('trial', 'basic', 'professional', 'enterprise') DEFAULT 'trial',
    subscription_status ENUM('active', 'suspended', 'cancelled', 'trial') DEFAULT 'trial',
    trial_ends_at DATETIME NULL,
    subscription_started_at DATETIME NULL,

    -- Billing
    billing_email VARCHAR(255) NULL,
    stripe_customer_id VARCHAR(255) NULL,

    -- Customization
    logo_url VARCHAR(500) NULL,
    primary_color VARCHAR(7) DEFAULT '#80ff80',

    -- Limits (based on subscription tier)
    max_users INT DEFAULT 5,
    max_properties INT DEFAULT 50,
    max_storage_gb DECIMAL(10, 2) DEFAULT 1.0,

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,

    INDEX idx_subdomain (subdomain),
    INDEX idx_status (subscription_status)
);
```

#### `tenant_invitations` Table
Manages invitations for new tenants to sign up.

```sql
CREATE TABLE tenant_invitations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    invitation_token VARCHAR(255) NOT NULL UNIQUE,
    invited_by VARCHAR(255) NULL,
    status ENUM('pending', 'accepted', 'expired') DEFAULT 'pending',
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_token (invitation_token),
    INDEX idx_email (email)
);
```

### 2.2 Modify Existing Tables

Add `tenant_id` to ALL existing tables that store tenant-specific data:

```sql
-- Core Tables
ALTER TABLE users ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE locations ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE winter_logs ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE green_logs ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE equipment_rates ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE property_assignments ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE routes ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE route_properties ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE route_assignments ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE property_lists ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE property_list_items ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE tickets ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE api_keys ADD COLUMN tenant_id INT NOT NULL AFTER id;

-- Add Foreign Keys
ALTER TABLE users ADD CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE locations ADD CONSTRAINT fk_locations_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE winter_logs ADD CONSTRAINT fk_winter_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE green_logs ADD CONSTRAINT fk_green_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE equipment_rates ADD CONSTRAINT fk_equipment_rates_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE property_assignments ADD CONSTRAINT fk_property_assignments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE routes ADD CONSTRAINT fk_routes_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE route_properties ADD CONSTRAINT fk_route_properties_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE route_assignments ADD CONSTRAINT fk_route_assignments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE property_lists ADD CONSTRAINT fk_property_lists_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE property_list_items ADD CONSTRAINT fk_property_list_items_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE tickets ADD CONSTRAINT fk_tickets_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE api_keys ADD CONSTRAINT fk_api_keys_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- Add Composite Indexes for Performance
CREATE INDEX idx_users_tenant ON users(tenant_id, id);
CREATE INDEX idx_locations_tenant ON locations(tenant_id, id);
CREATE INDEX idx_winter_logs_tenant ON winter_logs(tenant_id, id);
CREATE INDEX idx_routes_tenant ON routes(tenant_id, id);
CREATE INDEX idx_tickets_tenant ON tickets(tenant_id, id);
```

## 3. Authentication & Authorization Changes

### 3.1 JWT Token Structure
Modify JWT payload to include tenant information:

```python
# Current JWT payload
{
    "user_id": 123,
    "username": "john_doe",
    "role": "Admin"
}

# New Multi-tenant JWT payload
{
    "user_id": 123,
    "username": "john_doe",
    "role": "Admin",
    "tenant_id": 5,
    "tenant_subdomain": "acme-contractors"
}
```

### 3.2 Tenant Identification Methods

**Primary Method: Subdomain-based**
- `acme-contractors.contractorportal.com` → tenant: acme-contractors
- `snowpros.contractorportal.com` → tenant: snowpros

**Fallback Method: Custom Domain**
- `portal.acmecontractors.com` → resolve to tenant via custom_domain field

**Implementation:**
```python
# auth.py - Enhanced tenant resolution
def get_tenant_from_request(request: Request):
    """Extract tenant from subdomain or custom domain"""
    host = request.headers.get("host", "")

    # Check for custom domain first
    tenant = fetch_query(
        "SELECT * FROM tenants WHERE custom_domain = %s AND is_active = TRUE",
        (host,)
    )

    if tenant:
        return tenant[0]

    # Extract subdomain
    # portal.acme-contractors.contractorportal.com -> acme-contractors
    parts = host.split('.')
    if len(parts) >= 3:
        subdomain = parts[0]
        tenant = fetch_query(
            "SELECT * FROM tenants WHERE subdomain = %s AND is_active = TRUE",
            (subdomain,)
        )
        if tenant:
            return tenant[0]

    raise HTTPException(status_code=404, detail="Tenant not found")

def get_current_user_with_tenant(token: str = Depends(oauth2_scheme), request: Request = None):
    """Enhanced auth to include tenant validation"""
    # Decode JWT
    payload = verify_token(token)
    user_id = payload.get("user_id")
    tenant_id = payload.get("tenant_id")

    # Get tenant from request
    request_tenant = get_tenant_from_request(request)

    # Validate user belongs to the correct tenant
    if tenant_id != request_tenant['id']:
        raise HTTPException(status_code=403, detail="Access denied - tenant mismatch")

    # Fetch user
    user = fetch_query(
        "SELECT * FROM users WHERE id = %s AND tenant_id = %s",
        (user_id, tenant_id)
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    return {
        "user": user[0],
        "tenant": request_tenant
    }
```

## 4. Application Layer Changes

### 4.1 Database Query Middleware

Create a tenant-scoped query wrapper to automatically filter by tenant_id:

```python
# db.py - Add tenant-aware query functions
from contextvars import ContextVar

# Context variable to store current tenant
current_tenant: ContextVar[int] = ContextVar('current_tenant', default=None)

def set_current_tenant(tenant_id: int):
    """Set the current tenant context"""
    current_tenant.set(tenant_id)

def get_current_tenant():
    """Get the current tenant context"""
    tenant_id = current_tenant.get()
    if tenant_id is None:
        raise HTTPException(status_code=500, detail="No tenant context set")
    return tenant_id

def fetch_query_tenant_scoped(query: str, params: tuple = None):
    """
    Execute query with automatic tenant filtering
    Automatically adds WHERE tenant_id = ? to queries
    """
    tenant_id = get_current_tenant()

    # Add tenant_id filter if not already present
    if "WHERE" in query.upper():
        # Append to existing WHERE clause
        query = query.replace("WHERE", f"WHERE tenant_id = {tenant_id} AND", 1)
    elif "FROM" in query.upper():
        # Add WHERE clause after FROM
        query = query.replace("FROM", f"FROM", 1)
        # Find table name and add WHERE
        # This is simplified - production would use SQL parsing
        parts = query.split()
        table_index = parts.index("FROM") + 1
        parts.insert(table_index + 1, f"WHERE tenant_id = {tenant_id}")
        query = " ".join(parts)

    return fetch_query(query, params)

def execute_query_tenant_scoped(query: str, params: tuple = None):
    """
    Execute INSERT/UPDATE/DELETE with automatic tenant_id injection
    """
    tenant_id = get_current_tenant()

    if query.strip().upper().startswith("INSERT"):
        # Add tenant_id to INSERT
        # Production: Use SQL parsing library
        pass
    elif query.strip().upper().startswith("UPDATE"):
        # Add tenant_id to WHERE clause
        if "WHERE" in query.upper():
            query = query.replace("WHERE", f"WHERE tenant_id = {tenant_id} AND", 1)

    return execute_query(query, params)
```

### 4.2 Middleware for Request Context

```python
# main.py - Add tenant context middleware
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip tenant resolution for public endpoints
        if request.url.path in ["/signup", "/login", "/health"]:
            response = await call_next(request)
            return response

        try:
            # Get tenant from request
            tenant = get_tenant_from_request(request)

            # Set tenant context for this request
            set_current_tenant(tenant['id'])

            # Add tenant to request state
            request.state.tenant = tenant

            response = await call_next(request)
            return response
        except Exception as e:
            return JSONResponse(
                status_code=404,
                content={"detail": "Tenant not found or inactive"}
            )

# Add middleware to app
app.add_middleware(TenantContextMiddleware)
```

### 4.3 Route Updates

Update ALL route handlers to use tenant-scoped queries:

```python
# Example: property_routes.py
@router.get("/properties/")
def get_properties(auth: dict = Depends(get_current_user_with_tenant)):
    tenant_id = auth['tenant']['id']

    # Explicitly filter by tenant_id
    properties = fetch_query(
        "SELECT * FROM locations WHERE tenant_id = %s",
        (tenant_id,)
    )
    return properties if properties else []

@router.post("/add-property/")
def add_property(
    property_data: PropertyData,
    auth: dict = Depends(get_current_user_with_tenant)
):
    tenant_id = auth['tenant']['id']

    # Check if property exists within THIS tenant
    check_query = "SELECT id, name FROM locations WHERE address = %s AND tenant_id = %s"
    existing = fetch_query(check_query, (property_data.address, tenant_id))

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A property already exists at this address: {existing[0]['name']}"
        )

    query = """
        INSERT INTO locations (tenant_id, name, address, sqft, area_manager, plow, salt, ...)
        VALUES (%s, %s, %s, %s, %s, %s, %s, ...)
    """
    params = (
        tenant_id,  # ADD TENANT_ID AS FIRST PARAM
        property_data.name,
        property_data.address,
        # ... rest of fields
    )
    execute_query(query, params)
    return {"message": "Property added successfully"}
```

## 5. Tenant Onboarding Flow

### 5.1 Signup Process

```
1. User visits contractorportal.com
2. Clicks "Start Free Trial"
3. Signup form:
   - Company Name
   - Subdomain (auto-generated from company name, editable)
   - Admin Email
   - Admin Password
   - Admin Name
4. Validation:
   - Check subdomain availability
   - Validate email format
   - Password strength check
5. Create tenant record
6. Create admin user for tenant
7. Send welcome email
8. Redirect to {subdomain}.contractorportal.com/setup
```

### 5.2 Initial Setup Wizard

After signup, guide tenant through:
1. Upload company logo
2. Set primary color theme
3. Import initial properties (CSV upload)
4. Invite team members
5. Configure equipment rates
6. Set up billing (if not trial)

### 5.3 Implementation

```python
# routes/tenant_routes.py
from pydantic import BaseModel, EmailStr
import secrets

class TenantSignup(BaseModel):
    company_name: str
    subdomain: str
    admin_email: EmailStr
    admin_password: str
    admin_name: str

@router.post("/signup/")
async def tenant_signup(signup_data: TenantSignup):
    # Validate subdomain availability
    existing = fetch_query(
        "SELECT id FROM tenants WHERE subdomain = %s",
        (signup_data.subdomain,)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    # Validate email uniqueness
    existing_email = fetch_query(
        "SELECT id FROM users WHERE username = %s",
        (signup_data.admin_email,)
    )
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create tenant
    tenant_query = """
        INSERT INTO tenants (
            company_name, subdomain, admin_email,
            subscription_tier, subscription_status, trial_ends_at
        ) VALUES (%s, %s, %s, 'trial', 'trial', DATE_ADD(NOW(), INTERVAL 14 DAY))
    """
    tenant_id = execute_query(
        tenant_query,
        (signup_data.company_name, signup_data.subdomain, signup_data.admin_email)
    )

    # Hash password
    from auth import hash_password
    password_hash = hash_password(signup_data.admin_password)

    # Create admin user
    user_query = """
        INSERT INTO users (tenant_id, username, password, role, full_name)
        VALUES (%s, %s, %s, 'Admin', %s)
    """
    execute_query(
        user_query,
        (tenant_id, signup_data.admin_email, password_hash, signup_data.admin_name)
    )

    # Send welcome email
    send_welcome_email(signup_data.admin_email, signup_data.subdomain)

    return {
        "message": "Tenant created successfully",
        "subdomain": signup_data.subdomain,
        "login_url": f"https://{signup_data.subdomain}.contractorportal.com/login"
    }
```

## 6. Subscription & Billing

### 6.1 Subscription Tiers

| Feature | Trial | Basic | Professional | Enterprise |
|---------|-------|-------|--------------|------------|
| Duration | 14 days | Monthly | Monthly | Annual |
| Max Users | 3 | 10 | 50 | Unlimited |
| Max Properties | 25 | 100 | 500 | Unlimited |
| Storage | 500 MB | 5 GB | 50 GB | 500 GB |
| Routes | ✓ | ✓ | ✓ | ✓ |
| Property Lists | ✓ | ✓ | ✓ | ✓ |
| Weather Integration | ✗ | ✗ | ✓ | ✓ |
| Custom Branding | ✗ | ✗ | ✓ | ✓ |
| Custom Domain | ✗ | ✗ | ✓ | ✓ |
| API Access | ✗ | ✗ | ✗ | ✓ |
| Price/month | $0 | $49 | $149 | $499 |

### 6.2 Stripe Integration

```python
# routes/billing_routes.py
import stripe
from config import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY

@router.post("/create-subscription/")
async def create_subscription(
    tier: str,
    auth: dict = Depends(get_current_user_with_tenant)
):
    tenant = auth['tenant']

    # Create or get Stripe customer
    if not tenant['stripe_customer_id']:
        customer = stripe.Customer.create(
            email=tenant['admin_email'],
            name=tenant['company_name'],
            metadata={'tenant_id': tenant['id']}
        )

        # Update tenant with Stripe customer ID
        execute_query(
            "UPDATE tenants SET stripe_customer_id = %s WHERE id = %s",
            (customer.id, tenant['id'])
        )
    else:
        customer = stripe.Customer.retrieve(tenant['stripe_customer_id'])

    # Create subscription
    price_map = {
        'basic': 'price_basic_monthly',
        'professional': 'price_pro_monthly',
        'enterprise': 'price_enterprise_annual'
    }

    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{'price': price_map[tier]}],
        trial_period_days=14 if tier != 'trial' else 0
    )

    # Update tenant subscription
    execute_query(
        """UPDATE tenants
           SET subscription_tier = %s,
               subscription_status = 'active',
               subscription_started_at = NOW()
           WHERE id = %s""",
        (tier, tenant['id'])
    )

    return {
        "subscription_id": subscription.id,
        "status": subscription.status
    }

# Webhook to handle Stripe events
@router.post("/stripe-webhook/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle events
    if event['type'] == 'invoice.payment_failed':
        # Suspend tenant
        customer_id = event['data']['object']['customer']
        tenant = fetch_query(
            "SELECT id FROM tenants WHERE stripe_customer_id = %s",
            (customer_id,)
        )
        if tenant:
            execute_query(
                "UPDATE tenants SET subscription_status = 'suspended' WHERE id = %s",
                (tenant[0]['id'],)
            )

    elif event['type'] == 'customer.subscription.deleted':
        # Cancel tenant subscription
        customer_id = event['data']['object']['customer']
        tenant = fetch_query(
            "SELECT id FROM tenants WHERE stripe_customer_id = %s",
            (customer_id,)
        )
        if tenant:
            execute_query(
                "UPDATE tenants SET subscription_status = 'cancelled' WHERE id = %s",
                (tenant[0]['id'],)
            )

    return {"status": "success"}
```

## 7. Feature Gating & Limits

### 7.1 Middleware for Limit Enforcement

```python
# middleware/limits.py
def check_user_limit(auth: dict):
    """Check if tenant can add more users"""
    tenant = auth['tenant']

    current_users = fetch_query(
        "SELECT COUNT(*) as count FROM users WHERE tenant_id = %s",
        (tenant['id'],)
    )[0]['count']

    if current_users >= tenant['max_users']:
        raise HTTPException(
            status_code=403,
            detail=f"User limit reached. Upgrade to add more users. Current: {current_users}/{tenant['max_users']}"
        )

def check_property_limit(auth: dict):
    """Check if tenant can add more properties"""
    tenant = auth['tenant']

    current_properties = fetch_query(
        "SELECT COUNT(*) as count FROM locations WHERE tenant_id = %s",
        (tenant['id'],)
    )[0]['count']

    if current_properties >= tenant['max_properties']:
        raise HTTPException(
            status_code=403,
            detail=f"Property limit reached. Upgrade to add more properties. Current: {current_properties}/{tenant['max_properties']}"
        )

def check_feature_access(auth: dict, feature: str):
    """Check if tenant has access to a feature"""
    tenant = auth['tenant']
    tier = tenant['subscription_tier']

    feature_matrix = {
        'weather': ['professional', 'enterprise'],
        'custom_branding': ['professional', 'enterprise'],
        'custom_domain': ['professional', 'enterprise'],
        'api_access': ['enterprise']
    }

    if tier not in feature_matrix.get(feature, []):
        raise HTTPException(
            status_code=403,
            detail=f"Feature '{feature}' not available in {tier} plan"
        )
```

### 7.2 Apply Limits to Routes

```python
# routes/user_routes.py
@router.post("/add-user/")
def add_user(
    user_data: UserCreate,
    auth: dict = Depends(get_current_user_with_tenant)
):
    # Check user limit before adding
    check_user_limit(auth)

    # Proceed with user creation
    # ...

# routes/property_routes.py
@router.post("/add-property/")
def add_property(
    property_data: PropertyData,
    auth: dict = Depends(get_current_user_with_tenant)
):
    # Check property limit before adding
    check_property_limit(auth)

    # Proceed with property creation
    # ...

# routes/weather_routes.py
@router.get("/weather/")
def get_weather(auth: dict = Depends(get_current_user_with_tenant)):
    # Check feature access
    check_feature_access(auth, 'weather')

    # Proceed with weather data
    # ...
```

## 8. Data Migration for Existing Data

### 8.1 Create Default Tenant for Current System

```sql
-- Create the primary tenant for existing installation
INSERT INTO tenants (
    id, company_name, subdomain, admin_email,
    subscription_tier, subscription_status,
    max_users, max_properties, max_storage_gb
) VALUES (
    1,
    'Primary Account',
    'primary',
    'admin@example.com',
    'enterprise',
    'active',
    9999,
    9999,
    9999.0
);

-- Assign all existing users to default tenant
UPDATE users SET tenant_id = 1;
UPDATE locations SET tenant_id = 1;
UPDATE winter_logs SET tenant_id = 1;
UPDATE green_logs SET tenant_id = 1;
UPDATE equipment_rates SET tenant_id = 1;
UPDATE property_assignments SET tenant_id = 1;
UPDATE routes SET tenant_id = 1;
UPDATE route_properties SET tenant_id = 1;
UPDATE route_assignments SET tenant_id = 1;
UPDATE property_lists SET tenant_id = 1;
UPDATE property_list_items SET tenant_id = 1;
UPDATE tickets SET tenant_id = 1;
UPDATE api_keys SET tenant_id = 1;
```

## 9. Security Considerations

### 9.1 Tenant Isolation Validation

**CRITICAL:** All database queries MUST filter by tenant_id to prevent data leakage.

**Testing Strategy:**
1. Create automated tests that verify tenant isolation
2. Attempt to access data from different tenant
3. Monitor logs for cross-tenant queries

```python
# tests/test_tenant_isolation.py
def test_properties_isolation():
    """Test that Tenant A cannot see Tenant B's properties"""
    # Create two tenants
    tenant_a = create_test_tenant("tenant-a")
    tenant_b = create_test_tenant("tenant-b")

    # Create property for Tenant A
    property_a = create_test_property(tenant_a['id'], "Property A")

    # Try to fetch properties as Tenant B
    token_b = get_auth_token(tenant_b['id'])
    response = client.get(
        "/properties/",
        headers={"Authorization": f"Bearer {token_b}"}
    )

    # Assert Tenant B cannot see Property A
    properties = response.json()
    assert len(properties) == 0
    assert property_a['id'] not in [p['id'] for p in properties]
```

### 9.2 SQL Injection Prevention

Always use parameterized queries:

```python
# GOOD
fetch_query("SELECT * FROM locations WHERE tenant_id = %s AND name = %s", (tenant_id, name))

# BAD - SQL injection vulnerability
fetch_query(f"SELECT * FROM locations WHERE tenant_id = {tenant_id} AND name = '{name}'")
```

### 9.3 Cross-Tenant Data Leakage Prevention

**Best Practices:**
1. ALWAYS include tenant_id in WHERE clauses
2. Use foreign keys with ON DELETE CASCADE
3. Implement database views with tenant filtering
4. Use row-level security (MySQL 8.0+)
5. Regular security audits

## 10. Frontend Changes

### 10.1 Subdomain Routing

Update `config.js` to detect subdomain:

```javascript
// config.js
window.getTenantSubdomain = function() {
    const hostname = window.location.hostname;
    // Extract subdomain from hostname
    // portal.acme-contractors.contractorportal.com -> acme-contractors
    const parts = hostname.split('.');
    if (parts.length >= 3) {
        return parts[0];
    }
    return null;
};

// Update API_BASE_URL to use subdomain
const subdomain = getTenantSubdomain();
if (subdomain) {
    window.API_BASE_URL = `https://${subdomain}.contractorportal.com/api`;
} else {
    window.API_BASE_URL = 'https://contractorportal.com/api';
}
```

### 10.2 Custom Branding

Add CSS variables for tenant customization:

```html
<!-- Add to all HTML pages -->
<style id="tenant-branding">
    :root {
        --primary-color: #80ff80; /* Default */
        --tenant-logo: url('/static/default-logo.svg');
    }

    body {
        /* Use tenant primary color */
        --theme-primary: var(--primary-color);
    }

    .logo {
        background-image: var(--tenant-logo);
    }
</style>

<script>
    // Fetch tenant branding on page load
    async function applyTenantBranding() {
        const token = localStorage.getItem('token');
        if (!token) return;

        try {
            const response = await fetch(`${API_BASE_URL}/tenant/branding/`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const branding = await response.json();

            // Apply custom colors
            if (branding.primary_color) {
                document.documentElement.style.setProperty(
                    '--primary-color',
                    branding.primary_color
                );
            }

            // Apply custom logo
            if (branding.logo_url) {
                document.documentElement.style.setProperty(
                    '--tenant-logo',
                    `url(${branding.logo_url})`
                );
            }
        } catch (err) {
            console.error('Failed to load tenant branding:', err);
        }
    }

    // Call on page load
    window.addEventListener('DOMContentLoaded', applyTenantBranding);
</script>
```

### 10.3 Signup Page

Create new `signup.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Sign Up - Contractor Portal</title>
    <!-- Include styles -->
</head>
<body>
    <div class="signup-container">
        <h1>Start Your Free Trial</h1>
        <p>14 days free, no credit card required</p>

        <form id="signupForm">
            <div class="form-group">
                <label>Company Name:</label>
                <input type="text" id="companyName" required>
            </div>

            <div class="form-group">
                <label>Subdomain:</label>
                <div class="subdomain-input">
                    <input type="text" id="subdomain" required>
                    <span>.contractorportal.com</span>
                </div>
                <small id="subdomainAvailability"></small>
            </div>

            <div class="form-group">
                <label>Admin Email:</label>
                <input type="email" id="adminEmail" required>
            </div>

            <div class="form-group">
                <label>Admin Name:</label>
                <input type="text" id="adminName" required>
            </div>

            <div class="form-group">
                <label>Password:</label>
                <input type="password" id="password" required minlength="8">
            </div>

            <button type="submit">Create Account</button>
        </form>
    </div>

    <script>
        // Auto-generate subdomain from company name
        document.getElementById('companyName').addEventListener('input', function(e) {
            const subdomain = e.target.value
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, '-')
                .replace(/^-|-$/g, '');
            document.getElementById('subdomain').value = subdomain;
        });

        // Check subdomain availability
        let checkTimeout;
        document.getElementById('subdomain').addEventListener('input', function(e) {
            clearTimeout(checkTimeout);
            const subdomain = e.target.value;

            if (subdomain.length < 3) {
                document.getElementById('subdomainAvailability').textContent =
                    'Subdomain must be at least 3 characters';
                return;
            }

            checkTimeout = setTimeout(async () => {
                try {
                    const response = await fetch(
                        `${API_BASE_URL}/check-subdomain/${subdomain}`
                    );
                    const result = await response.json();

                    document.getElementById('subdomainAvailability').textContent =
                        result.available ? '✓ Available' : '✗ Already taken';
                } catch (err) {
                    console.error('Error checking subdomain:', err);
                }
            }, 500);
        });

        // Handle form submission
        document.getElementById('signupForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const signupData = {
                company_name: document.getElementById('companyName').value,
                subdomain: document.getElementById('subdomain').value,
                admin_email: document.getElementById('adminEmail').value,
                admin_name: document.getElementById('adminName').value,
                admin_password: document.getElementById('password').value
            };

            try {
                const response = await fetch(`${API_BASE_URL}/signup/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(signupData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('Account created successfully! Redirecting to login...');
                    window.location.href = result.login_url;
                } else {
                    alert('Error: ' + result.detail);
                }
            } catch (err) {
                console.error('Signup error:', err);
                alert('Failed to create account. Please try again.');
            }
        });
    </script>
</body>
</html>
```

## 11. Implementation Phases

### Phase 1: Database & Core Infrastructure (Week 1-2)
- [ ] Create `tenants` table
- [ ] Add `tenant_id` to all existing tables
- [ ] Create migration script for existing data
- [ ] Implement tenant context middleware
- [ ] Update authentication to include tenant_id in JWT

### Phase 2: Tenant Isolation (Week 3-4)
- [ ] Update all route handlers to filter by tenant_id
- [ ] Implement tenant-scoped query functions
- [ ] Create automated tests for tenant isolation
- [ ] Add security audit logging

### Phase 3: Tenant Onboarding (Week 5-6)
- [ ] Create signup flow UI
- [ ] Implement tenant creation endpoint
- [ ] Build setup wizard
- [ ] Add subdomain resolution logic
- [ ] Configure DNS wildcard for *.contractorportal.com

### Phase 4: Subscription & Billing (Week 7-8)
- [ ] Integrate Stripe
- [ ] Implement subscription tiers
- [ ] Add feature gating middleware
- [ ] Create billing management UI
- [ ] Set up webhook handlers

### Phase 5: Customization (Week 9-10)
- [ ] Add custom branding support
- [ ] Implement logo upload
- [ ] Create tenant settings page
- [ ] Add custom domain support
- [ ] Update frontend for dynamic branding

### Phase 6: Testing & Launch (Week 11-12)
- [ ] Comprehensive security testing
- [ ] Performance optimization
- [ ] Load testing with multiple tenants
- [ ] Documentation
- [ ] Soft launch with beta customers

## 12. Operational Considerations

### 12.1 Monitoring & Alerts

Track key metrics per tenant:
- Active users
- Property count
- Log entries per month
- API calls per day
- Storage usage
- Failed login attempts

```python
# Create monitoring queries
def get_tenant_metrics(tenant_id: int):
    return {
        "users": fetch_query(
            "SELECT COUNT(*) as count FROM users WHERE tenant_id = %s",
            (tenant_id,)
        )[0]['count'],
        "properties": fetch_query(
            "SELECT COUNT(*) as count FROM locations WHERE tenant_id = %s",
            (tenant_id,)
        )[0]['count'],
        "logs_this_month": fetch_query(
            """SELECT COUNT(*) as count FROM winter_logs
               WHERE tenant_id = %s
               AND MONTH(log_date) = MONTH(NOW())
               AND YEAR(log_date) = YEAR(NOW())""",
            (tenant_id,)
        )[0]['count']
    }
```

### 12.2 Backup Strategy

- Daily automated backups
- Per-tenant backup restoration capability
- Test restoration monthly

### 12.3 Performance Optimization

- Index all `tenant_id` columns
- Use connection pooling
- Implement caching per tenant
- Monitor slow queries

```sql
-- Example indexes for performance
CREATE INDEX idx_winter_logs_tenant_date ON winter_logs(tenant_id, log_date);
CREATE INDEX idx_locations_tenant_manager ON locations(tenant_id, area_manager);
CREATE INDEX idx_users_tenant_role ON users(tenant_id, role);
```

## 13. Cost Estimation

### Infrastructure Costs (Monthly)

| Component | Current | Multi-tenant | Notes |
|-----------|---------|--------------|-------|
| VPS Server | $40 | $80 | Upgrade to handle multiple tenants |
| Database | Included | Included | MySQL on same VPS |
| CDN/Static | $0 | $10 | Cloudflare for assets |
| Domain | $12/yr | $12/yr | contractorportal.com |
| Wildcard SSL | $0 | $0 | Let's Encrypt |
| Stripe Fees | $0 | 2.9% + $0.30 | Per transaction |
| Email Service | $0 | $15 | SendGrid for transactional emails |
| **Total** | **$40/mo** | **~$105/mo** | + Stripe fees |

### Revenue Projections

| Scenario | Tenants | Avg Plan | MRR | Annual |
|----------|---------|----------|-----|--------|
| Conservative | 10 | $75 | $750 | $9,000 |
| Moderate | 50 | $90 | $4,500 | $54,000 |
| Optimistic | 200 | $100 | $20,000 | $240,000 |

**Break-even:** ~2 paying customers at $75/mo average

## 14. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Data breach/leakage | Critical | Low | Automated testing, security audits, penetration testing |
| Performance degradation | High | Medium | Monitoring, caching, query optimization, vertical scaling |
| Tenant abuse | Medium | Low | Rate limiting, usage monitoring, ToS enforcement |
| Payment failures | Medium | Medium | Grace period, automated emails, suspension workflow |
| Data loss | Critical | Low | Daily backups, replication, disaster recovery plan |
| SQL injection | Critical | Low | Parameterized queries, code review, WAF |

## 15. Success Metrics

### Technical Metrics
- Query response time < 200ms (p95)
- API uptime > 99.9%
- Zero cross-tenant data leakage incidents
- Database backup success rate = 100%

### Business Metrics
- Trial-to-paid conversion > 15%
- Monthly churn rate < 5%
- Customer acquisition cost (CAC) < 3x monthly value
- Net Promoter Score (NPS) > 50

## 16. Conclusion

This multi-tenancy architecture provides a solid foundation for scaling the Contractor Portal into a SAAS product. The row-level isolation approach balances simplicity, cost-effectiveness, and security while maintaining the ability to scale.

**Next Steps:**
1. Review and approve this plan
2. Set up development environment for multi-tenant testing
3. Begin Phase 1 implementation
4. Establish weekly progress reviews

**Estimated Timeline:** 12 weeks for full implementation
**Estimated Cost:** ~$105/month operational + development time
**Break-even Point:** 2 paying customers
