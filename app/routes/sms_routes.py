"""
SMS Routes for Ticket Management via Text Messages
Handles Twilio webhooks and AI-powered SMS conversation management
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime
from auth import get_current_user
from utils.logger import get_logger

logger = get_logger(__name__)
from db import fetch_query, execute_query
from openai import OpenAI

router = APIRouter()

def get_api_key(key_name: str, user_id: int = None) -> str:
    """Get API key from database or environment variable"""
    # First try database (user-specific or system-wide)
    if user_id:
        query = """
            SELECT key_value FROM api_keys
            WHERE key_name = %s AND (user_id = %s OR user_id IS NULL)
            ORDER BY user_id DESC
            LIMIT 1
        """
        result = fetch_query(query, (key_name, user_id))
    else:
        query = """
            SELECT key_value FROM api_keys
            WHERE key_name = %s AND user_id IS NULL
            LIMIT 1
        """
        result = fetch_query(query, (key_name,))

    if result and result[0]["key_value"]:
        return result[0]["key_value"]

    # Fallback to environment variable
    env_map = {
        'twilio_account_sid': 'TWILIO_ACCOUNT_SID',
        'twilio_auth_token': 'TWILIO_AUTH_TOKEN',
        'twilio_phone_number': 'TWILIO_PHONE_NUMBER',
        'openai_api_key': 'OPENAI_API_KEY'
    }
    env_var = env_map.get(key_name)
    if env_var:
        return os.getenv(env_var, "")
    return ""

def send_sms(to_phone: str, message: str, conversation_id: int = None):
    """Send SMS via Twilio"""
    try:
        from twilio.rest import Client

        # Get Twilio credentials from database or environment
        account_sid = get_api_key('twilio_account_sid')
        auth_token = get_api_key('twilio_auth_token')
        phone_number = get_api_key('twilio_phone_number')

        if not account_sid or not auth_token or not phone_number:
            raise Exception("Twilio credentials not configured")

        client = Client(account_sid, auth_token)

        message_obj = client.messages.create(
            body=message,
            from_=phone_number,
            to=to_phone
        )

        # Log outbound message
        execute_query(
            """INSERT INTO sms_messages
               (conversation_id, phone_number, direction, message_body, twilio_sid, twilio_status)
               VALUES (%s, %s, 'outbound', %s, %s, %s)""",
            (conversation_id, to_phone, message, message_obj.sid, message_obj.status)
        )

        return message_obj
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}", exc_info=True)
        return None


def get_ai_interpretation(user_message: str, conversation_context: dict):
    """Use ChatGPT to interpret SMS message and extract ticket data"""

    # Get OpenAI API key from database or environment
    api_key = get_api_key('openai_api_key')
    if not api_key:
        raise Exception("OpenAI API key not configured")

    client = OpenAI(api_key=api_key)

    system_prompt = """You are an AI assistant helping contractors manage winter service tickets via SMS.

Your job is to interpret natural language text messages and extract structured ticket information.

User messages may include:
- Equipment used: "plow truck", "skid steer", "loader", "salt truck", etc.
- Salt quantities: "3 yards bulk salt", "5 bags", "2 bags calcium"
- Addresses: "123 Main St", "the walmart", "home depot parking lot"
- Times: "started at 2am", "finished at 3:30", "2 hours"
- Status updates: "START", "DONE", "FINISHED", "ON MY WAY"
- Notes: "parking lot had ice", "salted twice", "customer requested extra"

Extract the following information as JSON:
{
  "intent": "start_ticket" | "update_ticket" | "complete_ticket" | "query_address" | "provide_details" | "unknown",
  "equipment": "equipment name or null",
  "bulk_salt_qty": number or null,
  "bag_salt_qty": number or null,
  "calcium_chloride_qty": number or null,
  "address": "extracted address or null",
  "notes": "any additional notes or null",
  "time_in": "extracted start time or null",
  "time_out": "extracted end time or null",
  "confidence": "high" | "medium" | "low"
}

Examples:
User: "START" → {"intent": "start_ticket", "confidence": "high"}
User: "Plow truck 3 yards salt" → {"intent": "provide_details", "equipment": "Plow Truck", "bulk_salt_qty": 3, "confidence": "high"}
User: "DONE 5 bags" → {"intent": "complete_ticket", "bag_salt_qty": 5, "confidence": "high"}
User: "123 main street" → {"intent": "query_address", "address": "123 main street", "confidence": "medium"}
User: "Salted Walmart lot twice, icy conditions" → {"intent": "provide_details", "notes": "Salted Walmart lot twice, icy conditions", "confidence": "high"}

Respond ONLY with valid JSON, no other text."""

    context_info = f"Conversation state: {conversation_context.get('state', 'idle')}\n"
    if conversation_context.get('property_name'):
        context_info += f"Current property: {conversation_context['property_name']}\n"
    if conversation_context.get('partial_data'):
        context_info += f"Partial ticket data: {json.dumps(conversation_context['partial_data'])}\n"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"{context_info}\nUser message: {user_message}"
                }
            ],
            temperature=0.3,
            max_tokens=500
        )

        response_text = response.choices[0].message.content.strip()
        # Parse JSON from response
        interpretation = json.loads(response_text)
        return interpretation

    except Exception as e:
        logger.error(f"AI interpretation failed: {e}", exc_info=True)
        return {
            "intent": "unknown",
            "confidence": "low",
            "error": str(e)
        }


def get_or_create_conversation(phone_number: str, user_id: int = None):
    """Get existing conversation or create new one"""

    # Try to find existing conversation
    conv = fetch_query(
        "SELECT * FROM sms_conversations WHERE phone_number = %s ORDER BY last_message_at DESC LIMIT 1",
        (phone_number,)
    )

    if conv:
        return conv[0]

    # Find user by phone number if user_id not provided
    if not user_id:
        user = fetch_query(
            "SELECT id FROM users WHERE phone_number = %s LIMIT 1",
            (phone_number,)
        )
        if user:
            user_id = user[0]['id']
        else:
            # Unknown phone number
            return None

    # Create new conversation
    execute_query(
        """INSERT INTO sms_conversations (user_id, phone_number, conversation_state)
           VALUES (%s, %s, 'idle')""",
        (user_id, phone_number)
    )

    conv = fetch_query(
        "SELECT * FROM sms_conversations WHERE phone_number = %s ORDER BY id DESC LIMIT 1",
        (phone_number,)
    )
    return conv[0] if conv else None


@router.post("/sms/webhook")
async def sms_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    """
    Twilio webhook endpoint for incoming SMS messages
    This endpoint receives SMS from contractors and processes them with AI
    """

    phone_number = From
    message_body = Body.strip()

    print(f"[SMS] Received from {phone_number}: {message_body}")

    # Get or create conversation
    conversation = get_or_create_conversation(phone_number)

    if not conversation:
        # Unknown phone number - send registration message
        send_sms(
            phone_number,
            "📱 Welcome! Your phone number is not registered. Please contact your administrator to add your phone number to your account."
        )
        return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")

    # Log inbound message
    execute_query(
        """INSERT INTO sms_messages
           (conversation_id, phone_number, direction, message_body, twilio_sid)
           VALUES (%s, %s, 'inbound', %s, %s)""",
        (conversation['id'], phone_number, message_body, MessageSid)
    )

    # Get conversation context
    context_data = json.loads(conversation['context_data']) if conversation['context_data'] else {}

    # Check if this is a response to N8N self-healing system
    if message_body.upper().strip() in ['1', '2', '3', 'FIX', 'IGNORE', 'CUSTOM'] or 'ERROR ID:' in context_data.get('last_message', ''):
        # Forward to N8N webhook
        try:
            import requests
            n8n_url = "http://localhost:5678/webhook/human-decision"
            payload = {
                "body": {
                    "error_id": context_data.get('error_id', 'unknown'),
                    "message": message_body,
                    "phone": phone_number,
                    "timestamp": datetime.now().isoformat()
                }
            }
            requests.post(n8n_url, json=payload, timeout=10)

            # Send confirmation
            send_sms(phone_number, f"✅ Decision received: {message_body}\\n\\nProcessing your request...")
            return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")
        except Exception as e:
            print(f"[SMS] Failed to forward to N8N: {e}")

    # Use AI to interpret the message
    interpretation = get_ai_interpretation(message_body, {
        'state': conversation['conversation_state'],
        'property_name': context_data.get('property_name'),
        'partial_data': context_data.get('partial_data')
    })

    # Log AI interpretation
    execute_query(
        """UPDATE sms_messages
           SET ai_processed = TRUE, ai_interpretation = %s
           WHERE twilio_sid = %s""",
        (json.dumps(interpretation), MessageSid)
    )

    # Process based on intent
    response_message = await process_sms_intent(
        conversation=conversation,
        interpretation=interpretation,
        message_body=message_body
    )

    # Send response
    if response_message:
        send_sms(phone_number, response_message, conversation['id'])

    # Return empty TwiML response
    return Response(content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>", media_type="application/xml")


async def process_sms_intent(conversation: dict, interpretation: dict, message_body: str):
    """Process the AI interpretation and manage conversation state"""

    intent = interpretation.get('intent')
    user_id = conversation['user_id']
    phone_number = conversation['phone_number']
    context_data = json.loads(conversation['context_data']) if conversation['context_data'] else {}

    # Get user info
    user = fetch_query("SELECT name, role FROM users WHERE id = %s", (user_id,))
    user_name = user[0]['name'] if user else 'Unknown'

    # START TICKET (also triggered by "OMW" or "ON MY WAY")
    if intent == 'start_ticket' or message_body.lower() in ['omw', 'on my way']:
        # Check if user has assigned properties
        assigned = fetch_query(
            """SELECT l.id, l.name, l.address
               FROM locations l
               JOIN property_contractors pc ON l.id = pc.property_id
               WHERE pc.contractor_id = %s AND pc.acceptance_status = 'accepted'
               LIMIT 5""",
            (user_id,)
        )

        if not assigned:
            return "❌ You don't have any assigned properties. Please contact your manager."

        if len(assigned) == 1:
            # Only one property - auto-select it
            property_id = assigned[0]['id']
            property_name = assigned[0]['name']

            # Create ticket
            ticket_id = create_ticket_from_sms(user_id, user_name, property_id)

            # Update conversation state
            context_data['active_ticket_id'] = ticket_id
            context_data['property_id'] = property_id
            context_data['property_name'] = property_name

            execute_query(
                """UPDATE sms_conversations
                   SET conversation_state = 'collecting_ticket_details',
                       active_ticket_id = %s,
                       active_property_id = %s,
                       context_data = %s,
                       last_message_at = NOW()
                   WHERE id = %s""",
                (ticket_id, property_id, json.dumps(context_data), conversation['id'])
            )

            return f"✅ Ticket started for {property_name}!\n\nPlease reply with:\n- Equipment used\n- Salt quantities\n- Any notes\n\nExample: Plow truck, 3 yards bulk salt, parking lot clear"

        else:
            # Multiple properties - ask which one
            props_list = "\n".join([f"{i+1}. {p['name']} - {p['address']}" for i, p in enumerate(assigned)])
            context_data['available_properties'] = [{'id': p['id'], 'name': p['name']} for p in assigned]

            execute_query(
                """UPDATE sms_conversations
                   SET conversation_state = 'awaiting_start_confirmation',
                       context_data = %s,
                       last_message_at = NOW()
                   WHERE id = %s""",
                (json.dumps(context_data), conversation['id'])
            )

            return f"📍 Which property?\n\n{props_list}\n\nReply with the number or property name."

    # AWAITING START CONFIRMATION (user selecting property)
    elif conversation['conversation_state'] == 'awaiting_start_confirmation':
        available_props = context_data.get('available_properties', [])

        # Try to match property
        selected_property = None

        # Check if it's a number
        if message_body.isdigit():
            idx = int(message_body) - 1
            if 0 <= idx < len(available_props):
                selected_property = available_props[idx]
        else:
            # Try to match by name
            for prop in available_props:
                if message_body.lower() in prop['name'].lower():
                    selected_property = prop
                    break

        if not selected_property:
            return "❌ Invalid selection. Please reply with the property number (1, 2, 3...) or property name."

        # Create ticket
        ticket_id = create_ticket_from_sms(user_id, user_name, selected_property['id'])

        context_data['active_ticket_id'] = ticket_id
        context_data['property_id'] = selected_property['id']
        context_data['property_name'] = selected_property['name']

        execute_query(
            """UPDATE sms_conversations
               SET conversation_state = 'collecting_ticket_details',
                   active_ticket_id = %s,
                   active_property_id = %s,
                   context_data = %s,
                   last_message_at = NOW()
               WHERE id = %s""",
            (ticket_id, selected_property['id'], json.dumps(context_data), conversation['id'])
        )

        return f"✅ Ticket started for {selected_property['name']}!\n\nPlease reply with:\n- Equipment used\n- Salt quantities\n- Any notes\n\nExample: Plow truck, 3 yards bulk salt"

    # COLLECTING TICKET DETAILS
    elif intent == 'provide_details' or conversation['conversation_state'] == 'collecting_ticket_details':
        # Update ticket with provided details
        ticket_id = conversation['active_ticket_id']

        if not ticket_id:
            return "❌ No active ticket. Reply START to begin a new ticket."

        # Extract data from interpretation
        updates = []
        params = []

        if interpretation.get('equipment'):
            updates.append("equipment = %s")
            params.append(interpretation['equipment'])
            context_data['equipment'] = interpretation['equipment']

        if interpretation.get('bulk_salt_qty') is not None:
            updates.append("bulk_salt_qty = %s")
            params.append(interpretation['bulk_salt_qty'])
            context_data['bulk_salt_qty'] = interpretation['bulk_salt_qty']

        if interpretation.get('bag_salt_qty') is not None:
            updates.append("bag_salt_qty = %s")
            params.append(interpretation['bag_salt_qty'])
            context_data['bag_salt_qty'] = interpretation['bag_salt_qty']

        if interpretation.get('calcium_chloride_qty') is not None:
            updates.append("calcium_chloride_qty = %s")
            params.append(interpretation['calcium_chloride_qty'])
            context_data['calcium_chloride_qty'] = interpretation['calcium_chloride_qty']

        if interpretation.get('notes'):
            updates.append("notes = CONCAT(COALESCE(notes, ''), %s)")
            params.append(f"\n{interpretation['notes']}")
            context_data['notes'] = interpretation['notes']

        if updates:
            query = f"UPDATE winter_ops_logs SET {', '.join(updates)} WHERE id = %s"
            params.append(ticket_id)
            execute_query(query, tuple(params))

            # Update conversation context
            execute_query(
                "UPDATE sms_conversations SET context_data = %s, last_message_at = NOW() WHERE id = %s",
                (json.dumps(context_data), conversation['id'])
            )

            return "✅ Ticket updated!\n\nReply DONE when finished, or send more details to update."
        else:
            return "🤔 I didn't quite catch that. Please send:\n- Equipment name\n- Salt quantities (yards/bags)\n- Notes\n\nOr reply DONE to finish."

    # COMPLETE TICKET
    elif intent == 'complete_ticket':
        ticket_id = conversation['active_ticket_id']

        if not ticket_id:
            return "❌ No active ticket to complete."

        # Update ticket with time_out and any final details
        from ops_routes import snap_to_15_minutes

        now = datetime.now()
        time_out_raw = now.strftime('%Y-%m-%d %H:%M:%S')

        # Snap time to 15 minutes
        time_out = snap_to_15_minutes(time_out_raw)

        updates = ["time_out = %s", "status = 'closed'"]
        params = [time_out]

        if interpretation.get('bag_salt_qty') is not None:
            updates.append("bag_salt_qty = %s")
            params.append(interpretation['bag_salt_qty'])

        if interpretation.get('bulk_salt_qty') is not None:
            updates.append("bulk_salt_qty = %s")
            params.append(interpretation['bulk_salt_qty'])

        if interpretation.get('notes'):
            updates.append("notes = CONCAT(COALESCE(notes, ''), %s)")
            params.append(f"\n[Completed] {interpretation['notes']}")

        query = f"UPDATE winter_ops_logs SET {', '.join(updates)} WHERE id = %s"
        params.append(ticket_id)
        execute_query(query, tuple(params))

        # Reset conversation state
        execute_query(
            """UPDATE sms_conversations
               SET conversation_state = 'idle',
                   active_ticket_id = NULL,
                   active_property_id = NULL,
                   context_data = '{}',
                   last_message_at = NOW()
               WHERE id = %s""",
            (conversation['id'],)
        )

        property_name = context_data.get('property_name', 'Property')
        return f"✅ Ticket completed for {property_name}!\n\nThank you. Reply START when you begin the next job."

    # STATUS UPDATE COMMAND - Update check-in status
    elif message_body.lower() in ['working', 'busy', 'on site', 'servicing']:
        # Get active check-in
        active_checkin = fetch_query(
            """SELECT ec.id, we.event_name
               FROM event_checkins ec
               JOIN winter_events we ON ec.winter_event_id = we.id
               WHERE ec.user_id = %s AND ec.checked_out_at IS NULL
               LIMIT 1""",
            (user_id,)
        )

        if not active_checkin:
            return "❌ You're not checked in. Reply READY to check in for the active event first."

        # Update status to working
        execute_query(
            """UPDATE event_checkins
               SET status = 'working', updated_at = NOW()
               WHERE id = %s""",
            (active_checkin[0]['id'],)
        )

        return f"✅ Status updated to WORKING for {active_checkin[0]['event_name']}.\n\nReply READY when available for new assignments, or HOME when finished."

    # CHECK-IN COMMAND - Check in for active event
    elif message_body.lower() in ['ready', 'checkin', 'check in', 'check-in', 'available']:
        # Get active winter event
        active_event = fetch_query(
            "SELECT id, event_name FROM winter_events WHERE status = 'active' LIMIT 1"
        )

        if not active_event:
            return "❌ No active snow event. Check-in is only available during active events."

        event_id = active_event[0]['id']
        event_name = active_event[0]['event_name']

        # Get user's default equipment
        user_info = fetch_query(
            "SELECT default_equipment FROM users WHERE id = %s",
            (user_id,)
        )
        default_equipment = user_info[0].get('default_equipment') if user_info else None

        # Check if already checked in
        existing_checkin = fetch_query(
            "SELECT id, status FROM event_checkins WHERE winter_event_id = %s AND user_id = %s AND checked_out_at IS NULL",
            (event_id, user_id)
        )

        if existing_checkin:
            # Update existing check-in
            execute_query(
                """UPDATE event_checkins
                   SET status = 'checked_in', equipment_in_use = %s, updated_at = NOW()
                   WHERE id = %s""",
                (default_equipment, existing_checkin[0]['id'])
            )
            return f"✅ You're already checked in for {event_name}!\n\nStatus updated to READY. You may receive assignments soon.\n\nReply WORKING when servicing a property, or HOME when finished."
        else:
            # Create new check-in
            execute_query(
                """INSERT INTO event_checkins (winter_event_id, user_id, equipment_in_use, status, notes)
                   VALUES (%s, %s, %s, 'checked_in', 'Checked in via SMS')""",
                (event_id, user_id, default_equipment)
            )
            return f"✅ Checked in for {event_name}!\n\nEquipment: {default_equipment or 'Not specified'}\n\nYou may receive assignments soon.\n\nReply:\n- WORKING when servicing\n- HOME when finished"

    # HOME COMMAND - Check out and mark user as unavailable
    elif message_body.lower() in ['home', 'off', 'offline']:
        # Check out from any active events
        active_checkin = fetch_query(
            """SELECT ec.id, we.event_name
               FROM event_checkins ec
               JOIN winter_events we ON ec.winter_event_id = we.id
               WHERE ec.user_id = %s AND ec.checked_out_at IS NULL
               LIMIT 1""",
            (user_id,)
        )

        if active_checkin:
            execute_query(
                """UPDATE event_checkins
                   SET checked_out_at = NOW(), status = 'completed'
                   WHERE id = %s""",
                (active_checkin[0]['id'],)
            )

        # Mark user as unavailable for auto-assignment
        execute_query(
            "UPDATE users SET available_for_assignment = FALSE WHERE id = %s",
            (user_id,)
        )

        # Close any open tickets
        execute_query(
            """UPDATE winter_ops_logs
               SET status = 'closed', time_out = NOW(), notes = CONCAT(COALESCE(notes, ''), '\n[User went home - auto-closed]')
               WHERE user_id = %s AND status = 'open'""",
            (user_id,)
        )

        # Reset conversation
        execute_query(
            """UPDATE sms_conversations
               SET conversation_state = 'idle',
                   active_ticket_id = NULL,
                   active_property_id = NULL,
                   context_data = '{}',
                   last_message_at = NOW()
               WHERE id = %s""",
            (conversation['id'],)
        )

        return "🏠 You're marked as HOME. Checked out and any open tickets have been closed. You won't receive new assignments until a manager re-enables you. Drive safe!"

    # UNKNOWN / HELP
    else:
        if 'help' in message_body.lower():
            return """📱 SMS Commands:

🔔 EVENT CHECK-IN:
READY / CHECKIN - Check in for active event
WORKING - Update status to working
HOME / OFF - Check out and go offline

🎫 TICKET MANAGEMENT:
START / OMW - Begin a new ticket
DONE / COMPLETE - Complete current ticket

While working, just text:
- Equipment used
- Salt quantities
- Notes

Example: "Plow truck 3 yards bulk salt parking lot clear"

Need help? Call dispatch."""
        else:
            return "🤔 I didn't understand that. Reply:\n- READY to check in\n- START to begin ticket\n- DONE to finish ticket\n- HOME to go offline\n- HELP for commands"


def create_ticket_from_sms(user_id: int, user_name: str, property_id: int):
    """Create a new winter ops log ticket from SMS with 15-min snapped time and default equipment"""

    from ops_routes import snap_to_15_minutes

    now = datetime.now()
    time_in_raw = now.strftime('%Y-%m-%d %H:%M:%S')

    # Snap time to 15 minutes
    time_in = snap_to_15_minutes(time_in_raw)

    # Get user's default equipment
    user_info = fetch_query(
        "SELECT default_equipment FROM users WHERE id = %s",
        (user_id,)
    )
    default_equipment = user_info[0]['default_equipment'] if user_info and user_info[0].get('default_equipment') else 'Not specified'

    # Get active winter event
    active_event = fetch_query(
        "SELECT id FROM winter_events WHERE status = 'active' LIMIT 1"
    )
    winter_event_id = active_event[0]['id'] if active_event else None

    execute_query(
        """INSERT INTO winter_ops_logs
           (property_id, user_id, contractor_id, contractor_name, worker_name, equipment,
            time_in, time_out, status, bulk_salt_qty, bag_salt_qty, calcium_chloride_qty,
            customer_provided, notes, winter_event_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, 'open', 0, 0, 0, FALSE, %s, %s)""",
        (property_id, user_id, user_id, user_name, user_name, default_equipment,
         time_in, f'Ticket started via SMS at {now.strftime("%I:%M %p")}', winter_event_id)
    )

    # Get the created ticket ID
    ticket = fetch_query(
        "SELECT id FROM winter_ops_logs WHERE user_id = %s ORDER BY id DESC LIMIT 1",
        (user_id,)
    )

    return ticket[0]['id'] if ticket else None


# ==================== ADMIN ENDPOINTS ====================

@router.post("/sms/notify-assignment")
async def notify_assignment(
    property_id: int,
    contractor_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Send SMS notification when property is assigned to contractor"""

    if current_user['role'] not in ['Admin', 'Manager']:
        raise HTTPException(status_code=403, detail="Admin/Manager only")

    # Get contractor phone number and default equipment
    contractor = fetch_query(
        "SELECT phone_number, name, default_equipment FROM users WHERE id = %s",
        (contractor_id,)
    )

    if not contractor or not contractor[0]['phone_number']:
        return {"message": "Contractor has no phone number"}

    # Get property info
    property_info = fetch_query(
        "SELECT name, address FROM locations WHERE id = %s",
        (property_id,)
    )

    if not property_info:
        raise HTTPException(status_code=404, detail="Property not found")

    # Build SMS message with default equipment
    default_equipment = contractor[0].get('default_equipment', 'Not set')

    message = f"""📍 New Assignment!

Property: {property_info[0]['name']}
Address: {property_info[0]['address']}
Default Equipment: {default_equipment}

Reply START / OMW / ON MY WAY when you begin work.
Reply HELP for commands."""

    send_sms(contractor[0]['phone_number'], message)

    return {"message": "SMS notification sent", "phone": contractor[0]['phone_number']}


@router.post("/sms/send-test")
async def send_test_sms(
    phone_number: str,
    current_user: dict = Depends(get_current_user)
):
    """Send a test SMS to verify Twilio integration (Admin/Manager only)"""

    if current_user['role'] not in ['Admin', 'Manager']:
        raise HTTPException(status_code=403, detail="Admin/Manager only")

    message = """🧪 This is a test message from Snow Contractor Portal.

Your SMS integration is working correctly!

Please respond with 'hi' to confirm two-way messaging."""

    try:
        send_sms(phone_number, message)
        return {"message": "Test SMS sent successfully", "phone": phone_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test SMS: {str(e)}")


@router.get("/sms/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    """Get SMS conversations (Admin/Manager only)"""

    if current_user['role'] not in ['Admin', 'Manager']:
        raise HTTPException(status_code=403, detail="Admin/Manager only")

    conversations = fetch_query(
        """SELECT
            c.id, c.phone_number, c.conversation_state,
            c.active_ticket_id, c.last_message_at,
            u.name as user_name,
            l.name as property_name
        FROM sms_conversations c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN locations l ON c.active_property_id = l.id
        ORDER BY c.last_message_at DESC
        LIMIT 50"""
    )

    return conversations if conversations else []


@router.get("/sms/messages/{conversation_id}")
async def get_conversation_messages(
    conversation_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get messages for a conversation (Admin/Manager only)"""

    if current_user['role'] not in ['Admin', 'Manager']:
        raise HTTPException(status_code=403, detail="Admin/Manager only")

    messages = fetch_query(
        """SELECT id, direction, message_body, ai_interpretation, created_at
        FROM sms_messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC""",
        (conversation_id,)
    )

    return messages if messages else []
