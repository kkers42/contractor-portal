"""
Assignment Acceptance Routes
Handles acceptance/decline of property and route assignments
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from auth import get_current_user
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
