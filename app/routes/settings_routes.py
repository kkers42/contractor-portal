from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import fetch_query, execute_query
from auth import get_current_user, get_customer_id
from typing import Optional

router = APIRouter()

class APIKeySetting(BaseModel):
    key_name: str  # 'openai_api_key', 'openweather_api_key', 'mapbox_token', etc.
    key_value: str
    user_id: Optional[int] = None  # None = system-wide (admin only)

class APIKeyUpdate(BaseModel):
    key_name: str
    key_value: str

@router.get("/settings/api-keys/")
async def get_api_keys(current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """Get all API keys for current user (masked)"""
    user_id = int(current_user["sub"])
    user_role = current_user["role"]

    # Admins can see system-wide keys, others see only their own
    if user_role == "Admin":
        query = """
            SELECT key_name,
                   CASE
                       WHEN key_value IS NOT NULL AND key_value != ''
                       THEN CONCAT(LEFT(key_value, 4), '...', RIGHT(key_value, 4))
                       ELSE NULL
                   END as masked_value,
                   CASE WHEN key_value IS NOT NULL AND key_value != '' THEN TRUE ELSE FALSE END as is_configured,
                   user_id,
                   updated_at
            FROM api_keys
            WHERE customer_id = %s AND (user_id IS NULL OR user_id = %s)
            ORDER BY key_name
        """
        keys = fetch_query(query, (customer_id, user_id))
    else:
        query = """
            SELECT key_name,
                   CASE
                       WHEN key_value IS NOT NULL AND key_value != ''
                       THEN CONCAT(LEFT(key_value, 4), '...', RIGHT(key_value, 4))
                       ELSE NULL
                   END as masked_value,
                   CASE WHEN key_value IS NOT NULL AND key_value != '' THEN TRUE ELSE FALSE END as is_configured,
                   user_id,
                   updated_at
            FROM api_keys
            WHERE customer_id = %s AND user_id = %s
            ORDER BY key_name
        """
        keys = fetch_query(query, (customer_id, user_id))

    return keys if keys else []

@router.get("/settings/api-keys/{key_name}")
async def get_api_key(key_name: str, current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """Get a specific API key (returns actual value - use with caution)"""
    user_id = int(current_user["sub"])
    user_role = current_user["role"]

    # Try to get user-specific key first, then system-wide
    query = """
        SELECT key_value
        FROM api_keys
        WHERE customer_id = %s AND key_name = %s AND (user_id = %s OR (user_id IS NULL AND %s = 'Admin'))
        ORDER BY user_id DESC
        LIMIT 1
    """

    result = fetch_query(query, (customer_id, key_name, user_id, user_role))

    if not result or not result[0]["key_value"]:
        return {"key_value": None, "is_configured": False}

    return {"key_value": result[0]["key_value"], "is_configured": True}

@router.post("/settings/api-keys/")
async def set_api_key(setting: APIKeySetting, current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """Set an API key"""
    user_id = int(current_user["sub"])
    user_role = current_user["role"]

    # Only admins can set system-wide keys
    if setting.user_id is None and user_role != "Admin":
        raise HTTPException(status_code=403, detail="Only admins can set system-wide API keys")

    # If not admin, force user_id to current user
    target_user_id = setting.user_id if user_role == "Admin" else user_id

    # Check if key exists
    check_query = """
        SELECT id FROM api_keys
        WHERE customer_id = %s AND key_name = %s AND user_id <=> %s
    """
    existing = fetch_query(check_query, (customer_id, setting.key_name, target_user_id))

    if existing:
        # Update existing key
        update_query = """
            UPDATE api_keys
            SET key_value = %s, updated_at = NOW()
            WHERE customer_id = %s AND key_name = %s AND user_id <=> %s
        """
        execute_query(update_query, (setting.key_value, customer_id, setting.key_name, target_user_id))
        message = f"API key '{setting.key_name}' updated successfully"
    else:
        # Insert new key
        insert_query = """
            INSERT INTO api_keys (key_name, key_value, user_id, customer_id, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        execute_query(insert_query, (setting.key_name, setting.key_value, target_user_id, customer_id))
        message = f"API key '{setting.key_name}' added successfully"

    return {"message": message, "key_name": setting.key_name}

@router.delete("/settings/api-keys/{key_name}")
async def delete_api_key(key_name: str, current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """Delete an API key"""
    user_id = int(current_user["sub"])
    user_role = current_user["role"]

    # Users can only delete their own keys, admins can delete any
    if user_role == "Admin":
        query = "DELETE FROM api_keys WHERE customer_id = %s AND key_name = %s"
        execute_query(query, (customer_id, key_name))
    else:
        query = "DELETE FROM api_keys WHERE customer_id = %s AND key_name = %s AND user_id = %s"
        execute_query(query, (customer_id, key_name, user_id))

    return {"message": f"API key '{key_name}' deleted successfully"}

@router.get("/settings/available-integrations/")
async def get_available_integrations(current_user: dict = Depends(get_current_user), customer_id: str = Depends(get_customer_id)):
    """Get list of available integrations and their configuration status"""

    user_id = int(current_user["sub"])

    integrations = [
        {
            "name": "OpenAI",
            "key_name": "openai_api_key",
            "description": "AI-powered chat assistant and weather summaries",
            "cost": "~$5-20/month",
            "signup_url": "https://platform.openai.com/api-keys",
            "icon": "🤖"
        },
        {
            "name": "Anthropic (Claude)",
            "key_name": "anthropic_api_key",
            "description": "AI monitoring agent for system health, self-healing, and diagnostics",
            "cost": "~$3-5/month",
            "signup_url": "https://console.anthropic.com/settings/keys",
            "icon": "🔍"
        },
        {
            "name": "OpenWeatherMap",
            "key_name": "openweather_api_key",
            "description": "Weather forecasts and snow predictions",
            "cost": "Free (1000 calls/day)",
            "signup_url": "https://openweathermap.org/api",
            "icon": "🌨️"
        },
        {
            "name": "Mapbox",
            "key_name": "mapbox_token",
            "description": "Interactive property maps (geocoding uses free Nominatim)",
            "cost": "Free (50k loads/month)",
            "signup_url": "https://account.mapbox.com/access-tokens/",
            "icon": "🗺️"
        },
        {
            "name": "Twilio Account SID",
            "key_name": "twilio_account_sid",
            "description": "Twilio Account SID (starts with AC...) - SMS alerts for weather and open-by times",
            "cost": "$0.0075 per SMS",
            "signup_url": "https://www.twilio.com/console",
            "icon": "📱"
        },
        {
            "name": "Twilio Auth Token",
            "key_name": "twilio_auth_token",
            "description": "Twilio Auth Token from account dashboard - Required for SMS functionality",
            "cost": "$0.0075 per SMS",
            "signup_url": "https://www.twilio.com/console",
            "icon": "🔑"
        },
        {
            "name": "Twilio Phone Number",
            "key_name": "twilio_phone_number",
            "description": "Twilio phone number (format: +12345678901) - The FROM number for SMS",
            "cost": "$0.0075 per SMS",
            "signup_url": "https://www.twilio.com/console",
            "icon": "☎️"
        },
        {
            "name": "QuickBooks Client ID",
            "key_name": "quickbooks_client_id",
            "description": "QuickBooks Online integration - Client ID from Intuit Developer Portal",
            "cost": "Free (requires QuickBooks Online subscription)",
            "signup_url": "https://developer.intuit.com/app/developer/qbo/docs/get-started",
            "icon": "💰"
        },
        {
            "name": "QuickBooks Client Secret",
            "key_name": "quickbooks_client_secret",
            "description": "QuickBooks Online integration - Client Secret from Intuit Developer Portal",
            "cost": "Free (requires QuickBooks Online subscription)",
            "signup_url": "https://developer.intuit.com/app/developer/qbo/docs/get-started",
            "icon": "🔐"
        },
        {
            "name": "Gmail Address",
            "key_name": "gmail_address",
            "description": "Gmail email address for sending notifications (e.g., alerts@yourcompany.com)",
            "cost": "Free (requires Gmail account)",
            "signup_url": "https://support.google.com/mail/answer/185833",
            "icon": "📧"
        },
        {
            "name": "Gmail App Password",
            "key_name": "gmail_app_password",
            "description": "Gmail App Password (NOT your regular password - generate at Google Account settings)",
            "cost": "Free (requires 2FA enabled)",
            "signup_url": "https://support.google.com/accounts/answer/185833",
            "icon": "🔑"
        }
    ]

    # Check which ones are configured
    configured_keys = await get_api_keys(current_user, customer_id)
    configured_names = {k["key_name"] for k in configured_keys if k["is_configured"]}

    for integration in integrations:
        integration["is_configured"] = integration["key_name"] in configured_names

    return integrations
