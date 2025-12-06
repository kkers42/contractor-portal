"""
Winter Events Routes
Handles manual tracking of winter storm events for billing and reporting
Accessible by Managers and Admins only
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from auth import get_current_user
from db import fetch_query, execute_query

router = APIRouter()


class WinterEventCreate(BaseModel):
    event_name: str
    description: Optional[str] = None
    start_date: str  # ISO format datetime


class WinterEventComplete(BaseModel):
    end_date: str  # ISO format datetime


@router.get("/winter-events/")
def get_winter_events(current_user: dict = Depends(get_current_user)):
    """
    Get all winter events
    Accessible by Admins and Managers
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Manager or Admin access required"
        )

    # Get all winter events with stats
    query = """
        SELECT
            we.*,
            u.name as created_by_name,
            (SELECT COUNT(*) FROM winter_ops_logs WHERE winter_event_id = we.id) as log_count,
            (SELECT COUNT(DISTINCT property_id) FROM winter_ops_logs WHERE winter_event_id = we.id) as property_count
        FROM winter_events we
        LEFT JOIN users u ON we.created_by = u.id
        ORDER BY we.start_date DESC
    """

    events = fetch_query(query)
    return events if events else []


@router.get("/winter-events/active")
def get_active_winter_event(current_user: dict = Depends(get_current_user)):
    """
    Get the currently active winter event (if any)
    """
    query = """
        SELECT
            we.*,
            (SELECT COUNT(*) FROM winter_ops_logs WHERE winter_event_id = we.id) as log_count
        FROM winter_events we
        WHERE we.status = 'active'
        LIMIT 1
    """

    event = fetch_query(query)
    return event[0] if event else None


@router.get("/winter-events/{event_id}")
def get_winter_event(
    event_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific winter event by ID
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Manager or Admin access required"
        )

    query = """
        SELECT
            we.*,
            u.full_name as created_by_name,
            (SELECT COUNT(*) FROM winter_ops_logs WHERE winter_event_id = we.id) as log_count,
            (SELECT COUNT(DISTINCT location_id) FROM winter_ops_logs WHERE winter_event_id = we.id) as property_count
        FROM winter_events we
        LEFT JOIN users u ON we.created_by = u.id
        WHERE we.id = %s
    """

    event = fetch_query(query, (event_id,))

    if not event:
        raise HTTPException(status_code=404, detail="Winter event not found")

    return event[0]


@router.post("/winter-events/")
def create_winter_event(
    event_data: WinterEventCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new winter event
    Only one event can be active at a time
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Manager or Admin access required"
        )

    # Check if there's already an active event
    active_check = fetch_query(
        "SELECT id, event_name FROM winter_events WHERE status = 'active'"
    )

    if active_check:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start new event. Event '{active_check[0]['event_name']}' is already active. Please end it first."
        )

    # Create the event
    query = """
        INSERT INTO winter_events (
            event_name, description, start_date,
            status, created_by
        ) VALUES (%s, %s, %s, 'active', %s)
    """

    try:
        event_id = execute_query(
            query,
            (
                event_data.event_name,
                event_data.description,
                event_data.start_date,
                current_user.get("user_id")
            )
        )

        return {
            "message": "Winter event started successfully",
            "event_id": event_id,
            "event_name": event_data.event_name,
            "status": "active"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create winter event: {str(e)}"
        )


@router.post("/winter-events/{event_id}/complete")
def complete_winter_event(
    event_id: int,
    complete_data: WinterEventComplete,
    current_user: dict = Depends(get_current_user)
):
    """
    End/complete a winter event
    Sets the end_date and changes status to 'completed'
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Manager or Admin access required"
        )

    # Check if event exists and is active
    event = fetch_query(
        "SELECT id, event_name, status FROM winter_events WHERE id = %s",
        (event_id,)
    )

    if not event:
        raise HTTPException(status_code=404, detail="Winter event not found")

    if event[0]['status'] != 'active':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete event. Event is already {event[0]['status']}"
        )

    # Update event to completed
    query = """
        UPDATE winter_events
        SET status = 'completed',
            end_date = %s,
            completed_at = NOW()
        WHERE id = %s
    """

    try:
        execute_query(query, (complete_data.end_date, event_id))

        return {
            "message": "Winter event completed successfully",
            "event_id": event_id,
            "event_name": event[0]['event_name']
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete winter event: {str(e)}"
        )


@router.post("/winter-events/{event_id}/cancel")
def cancel_winter_event(
    event_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel a winter event
    Preserves all logs but marks event as cancelled
    """
    if current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Manager or Admin access required"
        )

    # Check if event exists
    event = fetch_query(
        "SELECT id, event_name, status FROM winter_events WHERE id = %s",
        (event_id,)
    )

    if not event:
        raise HTTPException(status_code=404, detail="Winter event not found")

    if event[0]['status'] == 'cancelled':
        raise HTTPException(
            status_code=400,
            detail="Event is already cancelled"
        )

    # Update event to cancelled
    try:
        execute_query(
            "UPDATE winter_events SET status = 'cancelled' WHERE id = %s",
            (event_id,)
        )

        return {
            "message": "Winter event cancelled",
            "event_id": event_id,
            "event_name": event[0]['event_name']
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel winter event: {str(e)}"
        )


@router.delete("/winter-events/{event_id}")
def delete_winter_event(
    event_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a winter event (Admin only)
    This will also remove winter_event_id from associated logs (set to NULL due to ON DELETE SET NULL)
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if event exists
    event = fetch_query(
        "SELECT id, event_name FROM winter_events WHERE id = %s",
        (event_id,)
    )

    if not event:
        raise HTTPException(status_code=404, detail="Winter event not found")

    # Get log count before deletion
    log_count = fetch_query(
        "SELECT COUNT(*) as count FROM winter_ops_logs WHERE winter_event_id = %s",
        (event_id,)
    )[0]['count']

    try:
        execute_query("DELETE FROM winter_events WHERE id = %s", (event_id,))

        return {
            "message": f"Winter event '{event[0]['event_name']}' deleted",
            "logs_orphaned": log_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete winter event: {str(e)}"
        )
