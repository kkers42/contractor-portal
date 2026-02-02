# Multi-Tenant Architecture Plan - v0.6.0

## Overview
Transform the contractor portal into a multi-tenant SaaS platform similar to QuickBooks Online, Salesforce, or GitHub where multiple companies can use the same application with complete data isolation.

## Core Concept

### Customer ID
- **Format:** 9-character alphanumeric string (e.g., `A3K7M2P9Q`)
- **Characters:** A-Z and 0-9 (excluding similar-looking: O/0, I/1, L/l)
- **Total possible combinations:** ~2.8 billion (34^9)
- **Collision prevention:** Check uniqueness before assignment
- **Generation:** Secure random with validation

### Data Isolation
Every tenant's data is completely isolated by `customer_id` filtering in queries.

---

## Database Schema Changes

### 1. New `customers` Table
```sql
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(9) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address TEXT,
    status ENUM('active', 'suspended', 'cancelled') DEFAULT 'active',
    subscription_tier ENUM('free', 'basic', 'professional', 'enterprise') DEFAULT 'basic',
    max_users INT DEFAULT 10,
    max_properties INT DEFAULT 100,
    features JSON,  -- Feature flags per customer
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status)
);
```

### 2. Add `customer_id` to Existing Tables

**Tables that need customer_id:**
- `users` - Each user belongs to one customer
- `locations` (properties) - Properties belong to customers
- `winter_ops_logs` - Logs belong to customer
- `winter_events` - Events are customer-specific
- `property_contractors` - Assignments are customer-specific
- `routes` - Routes belong to customers
- `property_lists` - Lists belong to customers
- `equipment_rates` - Equipment rates per customer
- `weather_data` - Customer-specific weather tracking
- `sms_context` - SMS conversations per customer
- `api_keys` - API keys per customer
- `jobber_auth` - Integration credentials per customer
- `quickbooks_auth` - Integration credentials per customer

**Migration Pattern:**
```sql
ALTER TABLE table_name
ADD COLUMN customer_id VARCHAR(9) NOT NULL DEFAULT 'DEFAULT01',
ADD INDEX idx_customer_id (customer_id),
ADD FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE;
```

### 3. Initial Data Migration
- Create first customer with ID from existing data
- Set all existing records to this customer_id
- Remove DEFAULT constraint after migration

---

## Authentication Changes

### JWT Token Enhancement
```python
# Current payload
{
    "sub": "user_id",
    "role": "Admin",
    "email": "user@example.com"
}

# New payload (v0.6.0+)
{
    "sub": "user_id",
    "customer_id": "A3K7M2P9Q",
    "role": "Admin",
    "email": "user@example.com"
}
```

### Middleware for Customer Context
- Extract `customer_id` from JWT
- Add to request context
- Validate user belongs to customer
- Automatically filter all queries by customer_id

---

## Query Updates

### Before (Single Tenant)
```python
query = "SELECT * FROM locations WHERE id = %s"
results = fetch_query(query, (property_id,))
```

### After (Multi-Tenant)
```python
query = """
    SELECT * FROM locations
    WHERE id = %s AND customer_id = %s
"""
results = fetch_query(query, (property_id, customer_id))
```

**Every query must include customer_id filtering for security.**

---

## New Endpoints

### Customer Management (Super Admin Only)
```
POST   /api/customers/                    # Create new customer
GET    /api/customers/                    # List all customers (super admin)
GET    /api/customers/{customer_id}       # Get customer details
PUT    /api/customers/{customer_id}       # Update customer
DELETE /api/customers/{customer_id}       # Deactivate customer

POST   /api/customers/{customer_id}/users # Invite user to customer
```

### Customer Self-Service (Customer Admin)
```
GET    /api/my-customer/                  # Get own customer info
PUT    /api/my-customer/                  # Update own customer info
GET    /api/my-customer/usage             # Usage statistics
GET    /api/my-customer/users             # List customer's users
```

---

## Customer ID Generator

### Implementation
```python
import secrets
import string

# Exclude confusing characters: O, 0, I, 1, L
SAFE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

def generate_customer_id():
    """Generate a unique 9-character alphanumeric customer ID"""
    while True:
        customer_id = ''.join(secrets.choice(SAFE_CHARS) for _ in range(9))

        # Check for uniqueness
        existing = fetch_query(
            "SELECT customer_id FROM customers WHERE customer_id = %s",
            (customer_id,)
        )

        if not existing:
            return customer_id
```

---

## User Roles Enhancement

### New Role: Super Admin
- **Access:** All customers
- **Permissions:** Create/manage customers, system-wide settings
- **Special:** Not tied to any customer_id (or special customer_id = "SYSTEM001")

### Customer-Level Roles (existing)
- **Customer Admin:** Full access within their customer
- **Manager:** Property and event management
- **Contractor:** Work execution
- **User:** Basic work execution

---

## Migration Strategy

### Phase 1: Database Setup (v0.6.0-alpha)
1. Create `customers` table
2. Create first customer from existing data
3. Add `customer_id` columns to all tables
4. Migrate existing data to first customer

### Phase 2: Application Updates (v0.6.0-beta)
1. Update authentication to include customer_id
2. Add customer_id filtering to all queries
3. Create customer management endpoints
4. Update all route files

### Phase 3: Testing (v0.6.0-rc)
1. Test data isolation
2. Test multi-customer scenarios
3. Security audit
4. Performance testing

### Phase 4: Production (v0.6.0)
1. Deploy to production
2. Create customer onboarding flow
3. Enable new customer signup

---

## Security Considerations

### Critical Rules
1. **NEVER trust customer_id from client** - Always extract from JWT
2. **ALWAYS filter by customer_id** in queries
3. **Validate user belongs to customer** before any operation
4. **Prevent cross-customer data leaks** - Test thoroughly
5. **Audit logs** - Track all customer data access

### Example Security Middleware
```python
async def verify_customer_context(
    current_user: dict = Depends(get_current_user)
):
    """Ensure user's customer_id is valid and user belongs to customer"""
    customer_id = current_user.get("customer_id")
    user_id = current_user.get("sub")

    # Verify user still belongs to this customer
    user = fetch_query(
        "SELECT customer_id FROM users WHERE id = %s",
        (user_id,)
    )

    if not user or user[0]['customer_id'] != customer_id:
        raise HTTPException(403, "Invalid customer context")

    return customer_id
```

---

## Benefits

### For the Business
- **Scalability:** Support unlimited customers on same infrastructure
- **Revenue:** Subscription-based pricing per customer
- **Isolation:** Each customer's data is completely separate
- **Efficiency:** Shared infrastructure reduces costs

### For Customers
- **Independence:** Each company has their own isolated system
- **Security:** Cannot see other customers' data
- **Customization:** Per-customer feature flags
- **Branding:** Potential for customer-specific theming

---

## Next Steps

1. ✅ Create architecture document (this file)
2. 🔄 Generate database migrations
3. ⏳ Implement customer_id generator
4. ⏳ Update authentication system
5. ⏳ Update all queries with customer_id filtering
6. ⏳ Create customer management UI
7. ⏳ Testing and validation
8. ⏳ Push to GitHub as v0.6.0-dev branch

---

## Rollback Plan

If issues arise:
1. Keep old schema in place during testing
2. Use feature flags to enable/disable multi-tenancy
3. Can revert to single-tenant by setting all customer_ids to same value
4. Database backups before migration
