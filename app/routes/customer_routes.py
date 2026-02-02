"""
Customer Management Routes - Multi-Tenant Administration
Endpoints for creating and managing customer accounts (tenants)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from db import fetch_query, execute_query
from auth import get_current_user, get_customer_id
from utils.customer_id_generator import generate_customer_id, validate_customer_id, customer_exists
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class Customer(BaseModel):
    """Customer model for multi-tenant system"""
    company_name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    status: str = Field(default="active", pattern="^(active|suspended|cancelled)$")
    subscription_tier: str = Field(default="basic", pattern="^(free|basic|professional|enterprise)$")
    max_users: int = Field(default=10, ge=1)
    max_properties: int = Field(default=100, ge=1)
    features: Optional[dict] = Field(default_factory=lambda: {
        "jobber": False,
        "quickbooks": False,
        "sms": False,
        "weather": True,
        "ai": False
    })
    billing_email: Optional[str] = None
    timezone: str = Field(default="America/New_York")


class CustomerResponse(BaseModel):
    """Customer response model with generated IDs"""
    id: int
    customer_id: str
    company_name: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    status: str
    subscription_tier: str
    max_users: int
    max_properties: int
    features: Optional[dict]
    billing_email: Optional[str]
    timezone: str
    created_at: datetime
    updated_at: datetime


def is_super_admin(current_user: dict) -> bool:
    """Check if current user is a super admin"""
    return current_user.get("role") == "Super Admin"


@router.post("/customers/", response_model=CustomerResponse)
async def create_customer(
    customer: Customer,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new customer (tenant) in the system.

    **Super Admin only**

    This creates a new isolated tenant with their own data space.
    """
    try:
        # Only Super Admins can create customers
        if not is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Only Super Admins can create customers")

        # Generate unique customer_id
        customer_id = generate_customer_id()
        logger.info(f"Generated new customer_id: {customer_id} for company: {customer.company_name}")

        # Insert customer
        query = """
            INSERT INTO customers (
                customer_id, company_name, contact_name, contact_email, contact_phone,
                address, status, subscription_tier, max_users, max_properties,
                features, billing_email, timezone
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            customer_id,
            customer.company_name,
            customer.contact_name,
            customer.contact_email,
            customer.contact_phone,
            customer.address,
            customer.status,
            customer.subscription_tier,
            customer.max_users,
            customer.max_properties,
            customer.features,
            customer.billing_email,
            customer.timezone
        )

        execute_query(query, values)

        # Fetch the created customer
        result = fetch_query(
            "SELECT * FROM customers WHERE customer_id = %s",
            (customer_id,)
        )

        if not result:
            raise HTTPException(status_code=500, detail="Customer created but could not be retrieved")

        logger.info(f"Successfully created customer: {customer_id} - {customer.company_name}")
        return result[0]

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")


@router.get("/customers/", response_model=List[CustomerResponse])
async def list_customers(
    current_user: dict = Depends(get_current_user)
):
    """
    List all customers in the system.

    **Super Admin only**
    """
    try:
        # Only Super Admins can list all customers
        if not is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Only Super Admins can list all customers")

        query = """
            SELECT * FROM customers
            ORDER BY created_at DESC
        """
        results = fetch_query(query)

        return results

    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing customers: {str(e)}")


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details for a specific customer.

    **Super Admin only**
    """
    try:
        # Only Super Admins can view any customer
        if not is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Only Super Admins can view customer details")

        # Validate customer_id format
        if not validate_customer_id(customer_id):
            raise HTTPException(status_code=400, detail="Invalid customer_id format")

        query = "SELECT * FROM customers WHERE customer_id = %s"
        results = fetch_query(query, (customer_id,))

        if not results:
            raise HTTPException(status_code=404, detail="Customer not found")

        return results[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching customer: {str(e)}")


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer: Customer,
    current_user: dict = Depends(get_current_user)
):
    """
    Update customer details.

    **Super Admin only**
    """
    try:
        # Only Super Admins can update customers
        if not is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Only Super Admins can update customers")

        # Validate customer_id format
        if not validate_customer_id(customer_id):
            raise HTTPException(status_code=400, detail="Invalid customer_id format")

        # Check customer exists
        if not customer_exists(customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")

        query = """
            UPDATE customers SET
                company_name = %s,
                contact_name = %s,
                contact_email = %s,
                contact_phone = %s,
                address = %s,
                status = %s,
                subscription_tier = %s,
                max_users = %s,
                max_properties = %s,
                features = %s,
                billing_email = %s,
                timezone = %s,
                updated_at = NOW()
            WHERE customer_id = %s
        """
        values = (
            customer.company_name,
            customer.contact_name,
            customer.contact_email,
            customer.contact_phone,
            customer.address,
            customer.status,
            customer.subscription_tier,
            customer.max_users,
            customer.max_properties,
            customer.features,
            customer.billing_email,
            customer.timezone,
            customer_id
        )

        execute_query(query, values)

        # Fetch updated customer
        result = fetch_query(
            "SELECT * FROM customers WHERE customer_id = %s",
            (customer_id,)
        )

        logger.info(f"Successfully updated customer: {customer_id}")
        return result[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deactivate (soft delete) a customer.

    **Super Admin only**

    Sets customer status to 'cancelled' rather than deleting data.
    """
    try:
        # Only Super Admins can delete customers
        if not is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Only Super Admins can delete customers")

        # Validate customer_id format
        if not validate_customer_id(customer_id):
            raise HTTPException(status_code=400, detail="Invalid customer_id format")

        # Check customer exists
        if not customer_exists(customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")

        # Soft delete - set status to cancelled
        query = """
            UPDATE customers
            SET status = 'cancelled', updated_at = NOW()
            WHERE customer_id = %s
        """
        execute_query(query, (customer_id,))

        logger.info(f"Successfully deactivated customer: {customer_id}")
        return {"message": f"Customer {customer_id} has been deactivated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting customer: {str(e)}")


# Customer Self-Service Endpoints (for Customer Admins)

@router.get("/my-customer/")
async def get_my_customer(
    customer_id: str = Depends(get_customer_id)
):
    """
    Get current user's customer information.

    Available to all users - shows their own customer details.
    """
    try:
        query = "SELECT * FROM customers WHERE customer_id = %s"
        results = fetch_query(query, (customer_id,))

        if not results:
            raise HTTPException(status_code=404, detail="Customer not found")

        return results[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer info: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching customer info: {str(e)}")


@router.get("/my-customer/usage")
async def get_customer_usage(
    customer_id: str = Depends(get_customer_id)
):
    """
    Get usage statistics for current customer.

    Shows: user count, property count, storage usage, etc.
    """
    try:
        # Get customer limits
        customer = fetch_query(
            "SELECT max_users, max_properties FROM customers WHERE customer_id = %s",
            (customer_id,)
        )

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Get actual usage
        user_count = fetch_query(
            "SELECT COUNT(*) as count FROM users WHERE customer_id = %s",
            (customer_id,)
        )[0]['count']

        property_count = fetch_query(
            "SELECT COUNT(*) as count FROM locations WHERE customer_id = %s",
            (customer_id,)
        )[0]['count']

        log_count = fetch_query(
            "SELECT COUNT(*) as count FROM winter_ops_logs WHERE customer_id = %s",
            (customer_id,)
        )[0]['count']

        return {
            "customer_id": customer_id,
            "users": {
                "current": user_count,
                "max": customer[0]['max_users'],
                "percentage": round((user_count / customer[0]['max_users']) * 100, 2)
            },
            "properties": {
                "current": property_count,
                "max": customer[0]['max_properties'],
                "percentage": round((property_count / customer[0]['max_properties']) * 100, 2)
            },
            "logs": {
                "total": log_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching usage stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching usage stats: {str(e)}")
