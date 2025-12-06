"""
Tenant Management Routes for SAAS Multi-Tenancy
Handles CRUD operations for tenants (SAAS customers)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from auth import get_current_user
from db import fetch_query, execute_query

router = APIRouter()


class TenantCreate(BaseModel):
    company_name: str
    subdomain: str
    admin_email: str
    admin_phone: Optional[str] = None
    subscription_status: str = "trial"
    trial_ends_at: Optional[str] = None


class TenantUpdate(BaseModel):
    company_name: Optional[str] = None
    admin_email: Optional[str] = None
    admin_phone: Optional[str] = None
    subscription_status: Optional[str] = None
    max_users: Optional[int] = None
    max_properties: Optional[int] = None


@router.get("/tenants/")
def get_tenants(current_user: dict = Depends(get_current_user)):
    """
    Get all tenants (Super Admin only)
    Returns list of tenants with their stats
    """
    # Check if user is Admin (in production, check for Super Admin role)
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Fetch all tenants
    tenants_query = """
        SELECT
            t.*,
            (SELECT COUNT(*) FROM users WHERE tenant_id = t.id) as user_count,
            (SELECT COUNT(*) FROM locations WHERE tenant_id = t.id) as property_count
        FROM tenants t
        ORDER BY t.created_at DESC
    """

    tenants = fetch_query(tenants_query)
    return tenants if tenants else []


@router.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get a specific tenant by ID
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    tenant = fetch_query(
        """
        SELECT
            t.*,
            (SELECT COUNT(*) FROM users WHERE tenant_id = t.id) as user_count,
            (SELECT COUNT(*) FROM locations WHERE tenant_id = t.id) as property_count
        FROM tenants t
        WHERE t.id = %s
        """,
        (tenant_id,)
    )

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant[0]


@router.post("/tenants/")
def create_tenant(
    tenant_data: TenantCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new SAAS tenant
    Only accessible by Super Admin
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if subdomain already exists
    existing = fetch_query(
        "SELECT id FROM tenants WHERE subdomain = %s",
        (tenant_data.subdomain,)
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Subdomain '{tenant_data.subdomain}' is already taken"
        )

    # Check if company name already exists
    existing_company = fetch_query(
        "SELECT id FROM tenants WHERE company_name = %s",
        (tenant_data.company_name,)
    )
    if existing_company:
        raise HTTPException(
            status_code=400,
            detail=f"Company name '{tenant_data.company_name}' already exists"
        )

    # Set trial end date if trial status
    trial_ends_at = tenant_data.trial_ends_at
    if tenant_data.subscription_status == "trial" and not trial_ends_at:
        trial_ends_at = (datetime.now() + timedelta(days=14)).isoformat()

    # Create tenant
    query = """
        INSERT INTO tenants (
            company_name, subdomain, admin_email, admin_phone,
            subscription_status, trial_ends_at,
            max_users, max_properties, max_user_role
        ) VALUES (%s, %s, %s, %s, %s, %s, 5, 100, 'Manager')
    """

    try:
        tenant_id = execute_query(
            query,
            (
                tenant_data.company_name,
                tenant_data.subdomain,
                tenant_data.admin_email,
                tenant_data.admin_phone,
                tenant_data.subscription_status,
                trial_ends_at
            )
        )

        return {
            "message": "Tenant created successfully",
            "tenant_id": tenant_id,
            "subdomain": tenant_data.subdomain,
            "url": f"https://{tenant_data.subdomain}.contractorportal.com"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")


@router.put("/tenants/{tenant_id}")
def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update tenant information
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if tenant exists
    existing = fetch_query("SELECT id FROM tenants WHERE id = %s", (tenant_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Build update query dynamically based on provided fields
    update_fields = []
    params = []

    if tenant_data.company_name:
        update_fields.append("company_name = %s")
        params.append(tenant_data.company_name)

    if tenant_data.admin_email:
        update_fields.append("admin_email = %s")
        params.append(tenant_data.admin_email)

    if tenant_data.admin_phone is not None:
        update_fields.append("admin_phone = %s")
        params.append(tenant_data.admin_phone)

    if tenant_data.subscription_status:
        update_fields.append("subscription_status = %s")
        params.append(tenant_data.subscription_status)

    if tenant_data.max_users:
        update_fields.append("max_users = %s")
        params.append(tenant_data.max_users)

    if tenant_data.max_properties:
        update_fields.append("max_properties = %s")
        params.append(tenant_data.max_properties)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"UPDATE tenants SET {', '.join(update_fields)} WHERE id = %s"
    params.append(tenant_id)

    try:
        execute_query(query, tuple(params))
        return {"message": "Tenant updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tenant: {str(e)}")


@router.post("/tenants/{tenant_id}/suspend")
def suspend_tenant(tenant_id: int, current_user: dict = Depends(get_current_user)):
    """
    Suspend a tenant (they cannot access the system)
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Don't allow suspending tenant ID 1 (primary account)
    if tenant_id == 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot suspend the primary account"
        )

    try:
        execute_query(
            "UPDATE tenants SET subscription_status = 'suspended' WHERE id = %s",
            (tenant_id,)
        )
        return {"message": "Tenant suspended successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suspend tenant: {str(e)}")


@router.post("/tenants/{tenant_id}/activate")
def activate_tenant(tenant_id: int, current_user: dict = Depends(get_current_user)):
    """
    Activate a suspended tenant
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        execute_query(
            "UPDATE tenants SET subscription_status = 'active' WHERE id = %s",
            (tenant_id,)
        )
        return {"message": "Tenant activated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate tenant: {str(e)}")


@router.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a tenant (DANGEROUS - cascades to all tenant data)
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Don't allow deleting tenant ID 1 (primary account)
    if tenant_id == 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the primary account"
        )

    try:
        # Get tenant info before deletion
        tenant = fetch_query("SELECT company_name FROM tenants WHERE id = %s", (tenant_id,))
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Delete tenant (CASCADE will delete all related data)
        execute_query("DELETE FROM tenants WHERE id = %s", (tenant_id,))

        return {
            "message": f"Tenant '{tenant[0]['company_name']}' and all associated data deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tenant: {str(e)}")


@router.get("/check-subdomain/{subdomain}")
def check_subdomain_availability(subdomain: str):
    """
    Check if a subdomain is available (public endpoint for signup)
    """
    existing = fetch_query(
        "SELECT id FROM tenants WHERE subdomain = %s",
        (subdomain,)
    )

    return {
        "subdomain": subdomain,
        "available": not existing
    }
