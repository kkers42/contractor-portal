"""
Jobber Integration Routes
Handles OAuth authentication and data synchronization with Jobber API
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import os
import requests
import secrets
from auth import get_current_user, get_customer_id
from utils.logger import get_logger

logger = get_logger(__name__)
from db import fetch_query, execute_query

router = APIRouter()

# Jobber OAuth Configuration
JOBBER_CLIENT_ID = os.getenv("JOBBER_CLIENT_ID")
JOBBER_CLIENT_SECRET = os.getenv("JOBBER_CLIENT_SECRET")
JOBBER_REDIRECT_URI = os.getenv("JOBBER_REDIRECT_URI", "https://snow-contractor.com/jobber/callback")
JOBBER_AUTH_URL = "https://api.getjobber.com/api/oauth/authorize"
JOBBER_TOKEN_URL = "https://api.getjobber.com/api/oauth/token"
JOBBER_API_URL = "https://api.getjobber.com/api/graphql"

# OAuth state storage (in production, use Redis or database)
oauth_states = {}


# ==================== MODELS ====================

class JobberCredentials(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    account_id: Optional[str] = None
    account_name: Optional[str] = None


class SyncRequest(BaseModel):
    sync_type: str = "full"  # clients, properties, full


class PropertyMappingUpdate(BaseModel):
    jobber_property_id: str
    property_id: Optional[int] = None
    sync_enabled: bool = True


# ==================== OAUTH FLOW ====================

@router.get("/connect")
def connect_jobber(current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """
    Initiate OAuth flow to connect Jobber account
    Admin/Manager only
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admin/Manager can connect Jobber")

    if not JOBBER_CLIENT_ID or not JOBBER_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Jobber API credentials not configured")

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": current_user.get("sub"),
        "customer_id": customer_id,
        "tenant_id": 1,  # Default tenant
        "timestamp": datetime.utcnow()
    }

    # Build authorization URL
    params = {
        "client_id": JOBBER_CLIENT_ID,
        "redirect_uri": JOBBER_REDIRECT_URI,
        "response_type": "code",
        "state": state,
        "scope": "client:read property:read job:read invoice:read"  # Request necessary scopes
    }

    auth_url = f"{JOBBER_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    return {"authorization_url": auth_url}


@router.get("/callback")
async def jobber_callback(code: str, state: str):
    """
    OAuth callback endpoint - receives authorization code from Jobber
    """
    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    oauth_data = oauth_states.pop(state)

    # Check state age (5 minutes max)
    if datetime.utcnow() - oauth_data["timestamp"] > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="State expired")

    # Exchange code for access token
    token_data = {
        "client_id": JOBBER_CLIENT_ID,
        "client_secret": JOBBER_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": JOBBER_REDIRECT_URI
    }

    try:
        response = requests.post(JOBBER_TOKEN_URL, data=token_data)
        response.raise_for_status()
        tokens = response.json()
    except Exception as e:
        logger.error(f"Failed to exchange Jobber code for token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to obtain access token from Jobber")

    # Calculate token expiry
    expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))

    # Store credentials in database
    tenant_id = oauth_data["tenant_id"]
    customer_id = oauth_data["customer_id"]

    # Check if credentials already exist
    existing = fetch_query("SELECT id FROM jobber_credentials WHERE tenant_id = %s AND customer_id = %s", (tenant_id, customer_id))

    if existing:
        # Update existing
        execute_query(
            """UPDATE jobber_credentials
               SET access_token = %s, refresh_token = %s, token_expires_at = %s,
                   scope = %s, updated_at = NOW()
               WHERE tenant_id = %s AND customer_id = %s""",
            (tokens["access_token"], tokens["refresh_token"], expires_at,
             tokens.get("scope"), tenant_id, customer_id)
        )
    else:
        # Insert new
        execute_query(
            """INSERT INTO jobber_credentials
               (tenant_id, customer_id, access_token, refresh_token, token_expires_at, scope)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (tenant_id, customer_id, tokens["access_token"], tokens["refresh_token"],
             expires_at, tokens.get("scope"))
        )

    # Redirect to integration page
    return RedirectResponse(url="/static/JobberIntegration.html?connected=true")


@router.post("/disconnect")
def disconnect_jobber(current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """
    Disconnect Jobber integration
    Admin/Manager only
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admin/Manager can disconnect Jobber")

    tenant_id = 1  # Default tenant

    execute_query("DELETE FROM jobber_credentials WHERE tenant_id = %s AND customer_id = %s", (tenant_id, customer_id))

    return {"ok": True, "message": "Jobber disconnected successfully"}


# ==================== TOKEN MANAGEMENT ====================

def get_jobber_access_token(tenant_id: int = 1, customer_id: str = None) -> str:
    """
    Get valid access token, refreshing if necessary
    """
    creds = fetch_query(
        "SELECT access_token, refresh_token, token_expires_at FROM jobber_credentials WHERE tenant_id = %s AND customer_id = %s",
        (tenant_id, customer_id)
    )

    if not creds:
        raise HTTPException(status_code=404, detail="Jobber not connected")

    cred = creds[0]

    # Check if token is expired or about to expire (within 5 minutes)
    expires_at = cred["token_expires_at"]
    if datetime.utcnow() >= expires_at - timedelta(minutes=5):
        # Refresh token
        token_data = {
            "client_id": JOBBER_CLIENT_ID,
            "client_secret": JOBBER_CLIENT_SECRET,
            "refresh_token": cred["refresh_token"],
            "grant_type": "refresh_token"
        }

        try:
            response = requests.post(JOBBER_TOKEN_URL, data=token_data)
            response.raise_for_status()
            tokens = response.json()

            # Update database
            new_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
            execute_query(
                """UPDATE jobber_credentials
                   SET access_token = %s, refresh_token = %s, token_expires_at = %s, updated_at = NOW()
                   WHERE tenant_id = %s AND customer_id = %s""",
                (tokens["access_token"], tokens.get("refresh_token", cred["refresh_token"]),
                 new_expires_at, tenant_id, customer_id)
            )

            return tokens["access_token"]
        except Exception as e:
            logger.error(f"Failed to refresh Jobber token: {e}", exc_info=True)
            raise HTTPException(status_code=401, detail="Jobber token expired, please reconnect")

    return cred["access_token"]


# ==================== GRAPHQL QUERIES ====================

def execute_jobber_query(query: str, variables: dict = None, tenant_id: int = 1, customer_id: str = None) -> dict:
    """
    Execute a GraphQL query against Jobber API
    """
    access_token = get_jobber_access_token(tenant_id, customer_id)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-JOBBER-GRAPHQL-VERSION": "2024-01-10"  # Use latest stable version
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(JOBBER_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            logger.error(f"Jobber GraphQL errors: {result['errors']}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Jobber API error: {result['errors'][0]['message']}")

        return result.get("data", {})
    except requests.exceptions.RequestException as e:
        logger.error(f"Jobber API request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to communicate with Jobber API")


# ==================== DATA SYNC ====================

@router.get("/status")
def get_jobber_status(current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """
    Get Jobber connection status and sync statistics
    """
    tenant_id = 1

    # Check if connected
    creds = fetch_query("SELECT account_name, token_expires_at FROM jobber_credentials WHERE tenant_id = %s AND customer_id = %s", (tenant_id, customer_id))

    if not creds:
        return {
            "connected": False,
            "account_name": None,
            "last_sync": None,
            "total_clients": 0,
            "total_properties": 0,
            "mapped_properties": 0
        }

    # Get sync stats
    last_sync = fetch_query(
        """SELECT sync_type, status, completed_at, items_created, items_updated
           FROM jobber_sync_logs
           WHERE tenant_id = %s AND customer_id = %s AND status = 'completed'
           ORDER BY completed_at DESC LIMIT 1""",
        (tenant_id, customer_id)
    )

    total_clients = fetch_query(
        "SELECT COUNT(*) as count FROM jobber_client_mapping WHERE tenant_id = %s AND customer_id = %s",
        (tenant_id, customer_id)
    )

    total_properties = fetch_query(
        "SELECT COUNT(*) as count FROM jobber_property_mapping WHERE tenant_id = %s AND customer_id = %s",
        (tenant_id, customer_id)
    )

    mapped_properties = fetch_query(
        "SELECT COUNT(*) as count FROM jobber_property_mapping WHERE tenant_id = %s AND customer_id = %s AND property_id IS NOT NULL",
        (tenant_id, customer_id)
    )

    return {
        "connected": True,
        "account_name": creds[0].get("account_name"),
        "token_expires_at": creds[0].get("token_expires_at"),
        "last_sync": last_sync[0] if last_sync else None,
        "total_clients": total_clients[0]["count"] if total_clients else 0,
        "total_properties": total_properties[0]["count"] if total_properties else 0,
        "mapped_properties": mapped_properties[0]["count"] if mapped_properties else 0
    }


@router.post("/sync")
async def sync_from_jobber(
    request: SyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Sync clients and properties from Jobber
    Admin/Manager only
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admin/Manager can sync from Jobber")

    tenant_id = 1
    sync_type = request.sync_type

    # Create sync log
    log_id = execute_query(
        """INSERT INTO jobber_sync_logs (tenant_id, sync_type, status, started_at)
           VALUES (%s, %s, 'started', NOW())""",
        (tenant_id, sync_type)
    )

    items_created = 0
    items_updated = 0
    items_skipped = 0
    error_message = None

    try:
        if sync_type in ["clients", "full"]:
            # Sync clients
            result = await sync_jobber_clients(tenant_id)
            items_created += result["created"]
            items_updated += result["updated"]
            items_skipped += result["skipped"]

        if sync_type in ["properties", "full"]:
            # Sync properties
            result = await sync_jobber_properties(tenant_id)
            items_created += result["created"]
            items_updated += result["updated"]
            items_skipped += result["skipped"]

        # Update sync log
        execute_query(
            """UPDATE jobber_sync_logs
               SET status = 'completed', completed_at = NOW(),
                   items_processed = %s, items_created = %s, items_updated = %s, items_skipped = %s
               WHERE id = %s""",
            (items_created + items_updated + items_skipped, items_created, items_updated, items_skipped, log_id)
        )

        return {
            "ok": True,
            "message": "Sync completed successfully",
            "stats": {
                "created": items_created,
                "updated": items_updated,
                "skipped": items_skipped
            }
        }

    except Exception as e:
        error_message = str(e)
        logger.error(f"Jobber sync failed: {e}", exc_info=True)

        # Update sync log
        execute_query(
            """UPDATE jobber_sync_logs
               SET status = 'failed', completed_at = NOW(), error_message = %s
               WHERE id = %s""",
            (error_message, log_id)
        )

        raise HTTPException(status_code=500, detail=f"Sync failed: {error_message}")


async def sync_jobber_clients(tenant_id: int) -> dict:
    """
    Sync clients from Jobber to client mapping table
    """
    query = """
    query GetClients($cursor: String) {
        clients(first: 50, after: $cursor) {
            nodes {
                id
                name
                companyName
                billingAddress {
                    street1
                    street2
                    city
                    province
                    postalCode
                    country
                }
                properties {
                    nodes {
                        id
                        address {
                            street1
                            street2
                            city
                            province
                            postalCode
                            country
                        }
                    }
                }
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    created = 0
    updated = 0
    skipped = 0
    has_next_page = True
    cursor = None

    while has_next_page:
        variables = {"cursor": cursor} if cursor else {}
        data = execute_jobber_query(query, variables, tenant_id)

        clients = data.get("clients", {}).get("nodes", [])
        page_info = data.get("clients", {}).get("pageInfo", {})

        for client in clients:
            jobber_client_id = client["id"]
            client_name = client.get("companyName") or client.get("name")

            # Check if client exists
            existing = fetch_query(
                "SELECT id FROM jobber_client_mapping WHERE tenant_id = %s AND jobber_client_id = %s",
                (tenant_id, jobber_client_id)
            )

            if existing:
                # Update
                execute_query(
                    """UPDATE jobber_client_mapping
                       SET jobber_client_name = %s, last_synced_at = NOW(), updated_at = NOW()
                       WHERE tenant_id = %s AND jobber_client_id = %s""",
                    (client_name, tenant_id, jobber_client_id)
                )
                updated += 1
            else:
                # Create
                execute_query(
                    """INSERT INTO jobber_client_mapping
                       (tenant_id, jobber_client_id, jobber_client_name, last_synced_at)
                       VALUES (%s, %s, %s, NOW())""",
                    (tenant_id, jobber_client_id, client_name)
                )
                created += 1

        has_next_page = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

    return {"created": created, "updated": updated, "skipped": skipped}


async def sync_jobber_properties(tenant_id: int) -> dict:
    """
    Sync properties from Jobber and optionally auto-create in our system
    """
    query = """
    query GetProperties($cursor: String) {
        clients(first: 50, after: $cursor) {
            nodes {
                id
                properties {
                    nodes {
                        id
                        address {
                            street1
                            street2
                            city
                            province
                            postalCode
                            country
                        }
                    }
                }
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    created = 0
    updated = 0
    skipped = 0
    has_next_page = True
    cursor = None

    while has_next_page:
        variables = {"cursor": cursor} if cursor else {}
        data = execute_jobber_query(query, variables, tenant_id)

        clients = data.get("clients", {}).get("nodes", [])
        page_info = data.get("clients", {}).get("pageInfo", {})

        for client in clients:
            jobber_client_id = client["id"]

            for prop in client.get("properties", {}).get("nodes", []):
                jobber_property_id = prop["id"]
                address = prop.get("address", {})

                if not address:
                    skipped += 1
                    continue

                # Format address
                address_parts = [
                    address.get("street1"),
                    address.get("street2"),
                    address.get("city"),
                    address.get("province"),
                    address.get("postalCode")
                ]
                full_address = ", ".join(filter(None, address_parts))

                # Check if property mapping exists
                existing = fetch_query(
                    "SELECT id, auto_create_property FROM jobber_property_mapping WHERE tenant_id = %s AND jobber_property_id = %s",
                    (tenant_id, jobber_property_id)
                )

                if existing:
                    # Update address
                    execute_query(
                        """UPDATE jobber_property_mapping
                           SET jobber_property_address = %s, last_synced_at = NOW(), updated_at = NOW()
                           WHERE tenant_id = %s AND jobber_property_id = %s""",
                        (full_address, tenant_id, jobber_property_id)
                    )
                    updated += 1
                else:
                    # Create mapping
                    execute_query(
                        """INSERT INTO jobber_property_mapping
                           (tenant_id, jobber_client_id, jobber_property_id, jobber_property_address, last_synced_at)
                           VALUES (%s, %s, %s, %s, NOW())""",
                        (tenant_id, jobber_client_id, jobber_property_id, full_address)
                    )
                    created += 1

                    # TODO: Auto-create property in locations table if auto_create_property is enabled
                    # This would involve checking if address already exists and creating if not

        has_next_page = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

    return {"created": created, "updated": updated, "skipped": skipped}


# ==================== PROPERTY MAPPING ====================

@router.get("/properties")
def get_jobber_properties(current_user: dict = Depends(get_current_user)):
    """
    Get list of Jobber properties and their mappings
    """
    tenant_id = 1

    properties = fetch_query(
        """SELECT jp.id, jp.jobber_property_id, jp.jobber_property_address,
                  jp.property_id, jp.sync_enabled, jp.last_synced_at,
                  l.name as property_name,
                  jc.jobber_client_name
           FROM jobber_property_mapping jp
           LEFT JOIN locations l ON jp.property_id = l.id
           LEFT JOIN jobber_client_mapping jc ON jp.jobber_client_id = jc.jobber_client_id AND jp.tenant_id = jc.tenant_id
           WHERE jp.tenant_id = %s
           ORDER BY jp.jobber_property_address""",
        (tenant_id,)
    )

    return {"properties": properties}


@router.put("/properties/{jobber_property_id}/map")
def map_jobber_property(
    jobber_property_id: str,
    mapping: PropertyMappingUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Map a Jobber property to a property in our system
    Admin/Manager only
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admin/Manager can map properties")

    tenant_id = 1

    execute_query(
        """UPDATE jobber_property_mapping
           SET property_id = %s, sync_enabled = %s, updated_at = NOW()
           WHERE tenant_id = %s AND jobber_property_id = %s""",
        (mapping.property_id, mapping.sync_enabled, tenant_id, jobber_property_id)
    )

    return {"ok": True, "message": "Property mapping updated"}


@router.get("/sync-logs")
def get_sync_logs(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent sync logs
    """
    tenant_id = 1

    logs = fetch_query(
        """SELECT id, sync_type, status, items_processed, items_created, items_updated,
                  items_skipped, error_message, started_at, completed_at
           FROM jobber_sync_logs
           WHERE tenant_id = %s
           ORDER BY started_at DESC
           LIMIT %s""",
        (tenant_id, limit)
    )

    return {"logs": logs}
