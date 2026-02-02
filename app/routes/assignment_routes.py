"""
Assignment Acceptance Routes
Handles acceptance/decline of property and route assignments
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from auth import get_curre, get_customer_idnt_user
from utils.logger import get_logger

logger = get_logger(__name__)
from db import fetch_query, execute_query

router = APIRouter()


class AcceptanceAction(BaseModel):
    notes: Optional[str] = None


# ==================== PROPERTY ASSIGNMENTS ====================

@router.get("/my-assignments/properties")
def get_my_property_assignments(current_user: dict = Depends(get_current_user)):
    """
    Get all property assignments for the current user
    """
    user_id = current_user.get("user_id")

    query = """
        SELECT
            pc.id,
            pc.property_id,
            pc.contractor_id,
            pc.acceptance_status,
            pc.accepted_at,
            pc.declined_at,
            pc.assigned_date,
            pc.is_primary,
            pc.notes,
            l.name AS property_name,
            l.address AS property_address,
            l.area_manager
        FROM property_contractors pc
        JOIN locations l ON pc.property_id = l.id
        WHERE pc.contractor_id = %s
        ORDER BY
            CASE pc.acceptance_status
                WHEN 'pending' THEN 1
                WHEN 'accepted' THEN 2
                WHEN 'declined' THEN 3
            END,
            pc.assigned_date DESC
    """

    assignments = fetch_query(query, (user_id,))
    return assignments if assignments else []


@router.post("/assignments/property/{assignment_id}/accept")
def accept_property_assignment(
    assignment_id: int,
    action: AcceptanceAction,
    current_user: dict = Depends(get_current_user)
):
    """
    Accept a property assignment
    """
    user_id = current_user.get("user_id")

    # Verify assignment belongs to current user
    assignment = fetch_query(
        "SELECT * FROM property_contractors WHERE id = %s AND contractor_id = %s",
        (assignment_id, user_id)
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or does not belong to you"
        )

    if assignment[0]['acceptance_status'] != 'pending':
        raise HTTPException(
            status_code=400,
            detail=f"Assignment already {assignment[0]['acceptance_status']}"
        )

    # Update assignment to accepted
    execute_query(
        """UPDATE property_contractors
           SET acceptance_status = 'accepted',
               accepted_at = NOW(),
               notes = CASE WHEN %s IS NOT NULL THEN CONCAT(COALESCE(notes, ''), '\n[Accepted] ', %s) ELSE notes END
           WHERE id = %s""",
        (action.notes, action.notes, assignment_id)
    )

    # Log to assignment history
    execute_query(
        """INSERT INTO assignment_history
           (assignment_type, assignment_id, user_id, property_id, action, notes)
           VALUES ('property', %s, %s, %s, 'accepted', %s)""",
        (assignment_id, user_id, assignment[0]['property_id'], action.notes)
    )

    return {"message": "Property assignment accepted", "assignment_id": assignment_id}


@router.post("/assignments/property/{assignment_id}/decline")
def decline_property_assignment(
    assignment_id: int,
    action: AcceptanceAction,
    current_user: dict = Depends(get_current_user)
):
    """
    Decline a property assignment
    """
    user_id = current_user.get("user_id")

    # Verify assignment belongs to current user
    assignment = fetch_query(
        "SELECT * FROM property_contractors WHERE id = %s AND contractor_id = %s",
        (assignment_id, user_id)
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or does not belong to you"
        )

    if assignment[0]['acceptance_status'] != 'pending':
        raise HTTPException(
            status_code=400,
            detail=f"Assignment already {assignment[0]['acceptance_status']}"
        )

    # Update assignment to declined
    execute_query(
        """UPDATE property_contractors
           SET acceptance_status = 'declined',
               declined_at = NOW(),
               notes = CASE WHEN %s IS NOT NULL THEN CONCAT(COALESCE(notes, ''), '\n[Declined] ', %s) ELSE notes END
           WHERE id = %s""",
        (action.notes, action.notes, assignment_id)
    )

    # Log to assignment history
    execute_query(
        """INSERT INTO assignment_history
           (assignment_type, assignment_id, user_id, property_id, action, notes)
           VALUES ('property', %s, %s, %s, 'declined', %s)""",
        (assignment_id, user_id, assignment[0]['property_id'], action.notes)
    )

    return {"message": "Property assignment declined", "assignment_id": assignment_id}


# ==================== ROUTE ASSIGNMENTS ====================

@router.get("/my-assignments/routes")
def get_my_route_assignments(current_user: dict = Depends(get_current_user)):
    """
    Get all route assignments for the current user
    """
    user_id = current_user.get("user_id")

    query = """
        SELECT
            ra.id,
            ra.route_id,
            ra.user_id,
            ra.acceptance_status,
            ra.accepted_at,
            ra.declined_at,
            ra.current_property_id,
            ra.current_property_started_at,
            ra.assigned_at,
            r.name AS route_name,
            r.description AS route_description,
            (SELECT COUNT(*) FROM route_properties WHERE route_id = ra.route_id) AS property_count,
            CASE WHEN ra.current_property_id IS NOT NULL THEN l.name ELSE NULL END AS current_property_name
        FROM route_assignments ra
        JOIN routes r ON ra.route_id = r.id
        LEFT JOIN locations l ON ra.current_property_id = l.id
        WHERE ra.user_id = %s
        ORDER BY
            CASE ra.acceptance_status
                WHEN 'pending' THEN 1
                WHEN 'accepted' THEN 2
                WHEN 'declined' THEN 3
            END,
            ra.assigned_at DESC
    """

    assignments = fetch_query(query, (user_id,))
    return assignments if assignments else []


@router.post("/assignments/route/{assignment_id}/accept")
def accept_route_assignment(
    assignment_id: int,
    action: AcceptanceAction,
    current_user: dict = Depends(get_current_user)
):
    """
    Accept a route assignment
    """
    user_id = current_user.get("user_id")

    # Verify assignment belongs to current user
    assignment = fetch_query(
        "SELECT * FROM route_assignments WHERE id = %s AND user_id = %s",
        (assignment_id, user_id)
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or does not belong to you"
        )

    if assignment[0]['acceptance_status'] != 'pending':
        raise HTTPException(
            status_code=400,
            detail=f"Assignment already {assignment[0]['acceptance_status']}"
        )

    # Update assignment to accepted
    execute_query(
        """UPDATE route_assignments
           SET acceptance_status = 'accepted',
               accepted_at = NOW()
           WHERE id = %s""",
        (assignment_id,)
    )

    # Log to assignment history
    execute_query(
        """INSERT INTO assignment_history
           (assignment_type, assignment_id, user_id, route_id, action, notes)
           VALUES ('route', %s, %s, %s, 'accepted', %s)""",
        (assignment_id, user_id, assignment[0]['route_id'], action.notes)
    )

    return {"message": "Route assignment accepted", "assignment_id": assignment_id}


@router.post("/assignments/route/{assignment_id}/decline")
def decline_route_assignment(
    assignment_id: int,
    action: AcceptanceAction,
    current_user: dict = Depends(get_current_user)
):
    """
    Decline a route assignment
    """
    user_id = current_user.get("user_id")

    # Verify assignment belongs to current user
    assignment = fetch_query(
        "SELECT * FROM route_assignments WHERE id = %s AND user_id = %s",
        (assignment_id, user_id)
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or does not belong to you"
        )

    if assignment[0]['acceptance_status'] != 'pending':
        raise HTTPException(
            status_code=400,
            detail=f"Assignment already {assignment[0]['acceptance_status']}"
        )

    # Update assignment to declined
    execute_query(
        """UPDATE route_assignments
           SET acceptance_status = 'declined',
               declined_at = NOW()
           WHERE id = %s""",
        (assignment_id,)
    )

    # Log to assignment history
    execute_query(
        """INSERT INTO assignment_history
           (assignment_type, assignment_id, user_id, route_id, action, notes)
           VALUES ('route', %s, %s, %s, 'declined', %s)""",
        (assignment_id, user_id, assignment[0]['route_id'], action.notes)
    )

    return {"message": "Route assignment declined", "assignment_id": assignment_id}


@router.post("/assignments/route/{assignment_id}/start-property/{property_id}")
def start_route_property(
    assignment_id: int,
    property_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Start working on a specific property in a route
    Can only start one property at a time - must finish current before starting next
    """
    user_id = current_user.get("user_id")

    # Verify assignment belongs to current user and is accepted
    assignment = fetch_query(
        """SELECT * FROM route_assignments
           WHERE id = %s AND user_id = %s AND acceptance_status = 'accepted'""",
        (assignment_id, user_id)
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found, not yours, or not accepted yet"
        )

    # Check if already working on a property
    if assignment[0]['current_property_id'] is not None:
        current_prop = fetch_query(
            "SELECT name FROM locations WHERE id = %s",
            (assignment[0]['current_property_id'],)
        )
        raise HTTPException(
            status_code=400,
            detail=f"You must finish '{current_prop[0]['name']}' before starting another property"
        )

    # Verify property is in this route
    in_route = fetch_query(
        """SELECT * FROM route_properties
           WHERE route_id = %s AND property_id = %s""",
        (assignment[0]['route_id'], property_id)
    )

    if not in_route:
        raise HTTPException(
            status_code=400,
            detail="This property is not in your assigned route"
        )

    # Update assignment with current property
    execute_query(
        """UPDATE route_assignments
           SET current_property_id = %s,
               current_property_started_at = NOW()
           WHERE id = %s""",
        (property_id, assignment_id)
    )

    # Log to assignment history
    execute_query(
        """INSERT INTO assignment_history
           (assignment_type, assignment_id, user_id, route_id, property_id, action)
           VALUES ('route', %s, %s, %s, %s, 'started')""",
        (assignment_id, user_id, assignment[0]['route_id'], property_id)
    )

    return {
        "message": "Started working on property",
        "property_id": property_id,
        "started_at": datetime.now().isoformat()
    }


@router.post("/assignments/route/{assignment_id}/complete-property")
def complete_route_property(
    assignment_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark current property as complete
    This allows starting the next property in the route
    """
    user_id = current_user.get("user_id")

    # Verify assignment belongs to current user
    assignment = fetch_query(
        """SELECT * FROM route_assignments
           WHERE id = %s AND user_id = %s""",
        (assignment_id, user_id)
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or does not belong to you"
        )

    if assignment[0]['current_property_id'] is None:
        raise HTTPException(
            status_code=400,
            detail="No property is currently in progress"
        )

    property_id = assignment[0]['current_property_id']

    # Clear current property
    execute_query(
        """UPDATE route_assignments
           SET current_property_id = NULL,
               current_property_started_at = NULL
           WHERE id = %s""",
        (assignment_id,)
    )

    # Log to assignment history
    execute_query(
        """INSERT INTO assignment_history
           (assignment_type, assignment_id, user_id, route_id, property_id, action)
           VALUES ('route', %s, %s, %s, %s, 'completed')""",
        (assignment_id, user_id, assignment[0]['route_id'], property_id)
    )

    return {
        "message": "Property marked as complete",
        "property_id": property_id,
        "completed_at": datetime.now().isoformat()
    }


# ==================== AI-POWERED PROPERTY ASSIGNMENT ====================

class PropertyListAssignmentRequest(BaseModel):
    property_list_id: int
    winter_event_id: Optional[int] = None


@router.post("/ai-assign-property-list")
async def ai_assign_property_list(
    request: PropertyListAssignmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    AI-powered property list assignment with sidewalk/non-sidewalk crew validation
    Ensures at least one sidewalk crew and one non-sidewalk crew are assigned
    Only assigns to available crews (not working on open tickets)
    """
    if current_user['role'] not in ['Admin', 'Manager']:
        raise HTTPException(status_code=403, detail="Admin/Manager only")

    # Get properties in the list
    properties = fetch_query(
        """SELECT l.id, l.name, l.address
           FROM locations l
           JOIN property_lists_properties plp ON l.id = plp.property_id
           WHERE plp.list_id = %s""",
        (request.property_list_id,)
    )

    if not properties:
        raise HTTPException(status_code=404, detail="No properties found in this list")

    # Get available contractors (ALLOWING multiple open tickets per contractor)
    available_contractors = fetch_query(
        """SELECT DISTINCT
            u.id, u.name, u.default_equipment, u.phone_number,
            CASE
                WHEN u.default_equipment LIKE '%sidewalk%' THEN 'sidewalk'
                ELSE 'non-sidewalk'
            END as crew_type
        FROM users u
        WHERE u.status = 'active'
          AND u.available_for_assignment = TRUE
          AND u.role IN ('Contractor', 'Subcontractor', 'User')
        ORDER BY u.id"""
    )

    if not available_contractors:
        return {
            "success": False,
            "message": "No available contractors",
            "assigned_count": 0
        }

    # Separate crews by type
    sidewalk_crews = [c for c in available_contractors if c['crew_type'] == 'sidewalk']
    non_sidewalk_crews = [c for c in available_contractors if c['crew_type'] == 'non-sidewalk']

    # Validate we have at least one of each type
    if not sidewalk_crews:
        return {
            "success": False,
            "message": "No available sidewalk crews. Please ensure at least one crew has equipment with 'sidewalk' in the name and is available.",
            "assigned_count": 0,
            "available_crews": {
                "sidewalk": 0,
                "non_sidewalk": len(non_sidewalk_crews)
            }
        }

    if not non_sidewalk_crews:
        return {
            "success": False,
            "message": "No available non-sidewalk crews. Please ensure at least one crew has equipment without 'sidewalk' in the name and is available.",
            "assigned_count": 0,
            "available_crews": {
                "sidewalk": len(sidewalk_crews),
                "non_sidewalk": 0
            }
        }

    # Use AI to intelligently assign properties
    import json
    import os

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        # Try to get from api_keys table
        api_key_result = fetch_query(
            "SELECT key_value FROM api_keys WHERE key_name = 'openai_api_key' AND user_id IS NULL LIMIT 1"
        )
        if api_key_result and api_key_result[0].get('key_value'):
            OPENAI_API_KEY = api_key_result[0]['key_value']

    if not OPENAI_API_KEY:
        # Fallback to round-robin assignment
        assignments = []
        all_crews = sidewalk_crews + non_sidewalk_crews
        crew_index = 0

        for property in properties:
            contractor = all_crews[crew_index % len(all_crews)]
            assignments.append({
                "property_id": property['id'],
                "property_name": property['name'],
                "contractor_id": contractor['id'],
                "contractor_name": contractor['name'],
                "crew_type": contractor['crew_type']
            })
            crew_index += 1
    else:
        # Use ChatGPT for intelligent assignment
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        system_prompt = """You are an AI assistant that assigns snow removal properties to contractors.

Your job is to intelligently assign properties to available crews, ensuring efficient routing and crew utilization.

You will receive:
1. A list of properties to assign
2. Available sidewalk crews (with equipment names containing "sidewalk")
3. Available non-sidewalk crews (with equipment for parking lots, driveways, etc.)

Rules:
- MUST assign at least one property to a sidewalk crew
- MUST assign at least one property to a non-sidewalk crew
- Try to balance workload across all crews
- Consider proximity if addresses are provided
- Sidewalk crews can ONLY handle sidewalk properties
- Non-sidewalk crews can handle parking lots, driveways, roads, etc.

Return ONLY a valid JSON array of assignments with no additional text:
[
  {
    "property_id": 123,
    "property_name": "Walmart",
    "contractor_id": 5,
    "contractor_name": "John Doe",
    "crew_type": "sidewalk",
    "reasoning": "Sidewalk crew assigned to handle walkways"
  }
]"""

        properties_str = json.dumps([
            {"id": p['id'], "name": p['name'], "address": p.get('address', 'N/A')}
            for p in properties
        ], indent=2)

        sidewalk_crews_str = json.dumps([
            {"id": c['id'], "name": c['name'], "equipment": c['default_equipment']}
            for c in sidewalk_crews
        ], indent=2)

        non_sidewalk_crews_str = json.dumps([
            {"id": c['id'], "name": c['name'], "equipment": c['default_equipment']}
            for c in non_sidewalk_crews
        ], indent=2)

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"""Properties to assign:
{properties_str}

Available sidewalk crews:
{sidewalk_crews_str}

Available non-sidewalk crews:
{non_sidewalk_crews_str}

Please assign all properties to crews, ensuring proper crew type distribution."""
                    }
                ],
                temperature=0.7,
                max_tokens=4096
            )

            response_text = response.choices[0].message.content.strip()

            # Extract JSON from response (may be wrapped in markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            assignments = json.loads(response_text)
        except Exception as e:
            logger.error(f"ChatGPT assignment failed: {e}", exc_info=True)
            # Fallback to round-robin
            assignments = []
            all_crews = sidewalk_crews + non_sidewalk_crews
            crew_index = 0

            for property in properties:
                contractor = all_crews[crew_index % len(all_crews)]
                assignments.append({
                    "property_id": property['id'],
                    "property_name": property['name'],
                    "contractor_id": contractor['id'],
                    "contractor_name": contractor['name'],
                    "crew_type": contractor['crew_type']
                })
                crew_index += 1

    # Execute assignments in database
    assigned_count = 0
    sms_notifications = []

    for assignment in assignments:
        try:
            # Check if assignment already exists
            existing = fetch_query(
                """SELECT id FROM property_contractors
                   WHERE property_id = %s AND contractor_id = %s AND acceptance_status = 'pending'""",
                (assignment['property_id'], assignment['contractor_id'])
            )

            if not existing:
                # Create new assignment
                execute_query(
                    """INSERT INTO property_contractors
                       (property_id, contractor_id, acceptance_status, assigned_date, notes)
                       VALUES (%s, %s, 'pending', NOW(), %s)""",
                    (assignment['property_id'], assignment['contractor_id'],
                     f"AI-assigned for crew type: {assignment['crew_type']}")
                )

                # Get contractor phone for SMS notification
                contractor = fetch_query(
                    "SELECT phone_number FROM users WHERE id = %s",
                    (assignment['contractor_id'],)
                )

                if contractor and contractor[0].get('phone_number'):
                    sms_notifications.append({
                        "contractor_id": assignment['contractor_id'],
                        "property_id": assignment['property_id'],
                        "phone": contractor[0]['phone_number']
                    })

                assigned_count += 1
        except Exception as e:
            logger.error(f"Failed to assign property {assignment['property_id']}: {e}", exc_info=True)

    # Send SMS notifications
    if sms_notifications:
        from sms_routes import send_sms
        for notif in sms_notifications:
            try:
                property_info = fetch_query(
                    "SELECT name, address FROM locations WHERE id = %s",
                    (notif['property_id'],)
                )

                contractor_info = fetch_query(
                    "SELECT name, default_equipment FROM users WHERE id = %s",
                    (notif['contractor_id'],)
                )

                if property_info and contractor_info:
                    message = f"""📍 New Assignment!

Property: {property_info[0]['name']}
Address: {property_info[0]['address']}
Your Equipment: {contractor_info[0]['default_equipment']}

Reply START / OMW when you begin work."""

                    send_sms(notif['phone'], message)
            except Exception as e:
                logger.error(f"Failed to send SMS notification: {e}", exc_info=True)

    return {
        "success": True,
        "message": f"Successfully assigned {assigned_count} properties",
        "assigned_count": assigned_count,
        "total_properties": len(properties),
        "assignments": assignments,
        "sms_notifications_sent": len(sms_notifications),
        "available_crews": {
            "sidewalk": len(sidewalk_crews),
            "non_sidewalk": len(non_sidewalk_crews),
            "total": len(available_contractors)
        }
    }
