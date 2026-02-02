from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from db import fetch_query, execute_query
from auth import get_curre, get_customer_idnt_user

router = APIRouter()

class CheckInRequest(BaseModel):
    winter_event_id: int
    equipment_in_use: Optional[str] = None
    notes: Optional[str] = None

class CheckOutRequest(BaseModel):
    notes: Optional[str] = None

class LocationUpdate(BaseModel):
    lat: float
    lon: float
    current_property_id: Optional[int] = None
    status: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str  # checked_in, working, completed, unavailable
    current_property_id: Optional[int] = None
    notes: Optional[str] = None

@router.post("/events/{event_id}/checkin")
async def check_in(event_id: int, data: CheckInRequest, current_user: dict = Depends(get_current_user)):
    """Check in for an active winter event"""
    user_id = int(current_user["sub"])

    # Verify event exists and is active
    event_query = "SELECT id, status FROM winter_events WHERE id = %s"
    event = fetch_query(event_query, (event_id,))

    if not event:
        raise HTTPException(status_code=404, detail="Winter event not found")

    if event[0]["status"] != "active":
        raise HTTPException(status_code=400, detail="Event is not active")

    # Check if already checked in for this event
    existing_checkin = fetch_query(
        "SELECT id, status FROM event_checkins WHERE winter_event_id = %s AND user_id = %s AND checked_out_at IS NULL",
        (event_id, user_id)
    )

    if existing_checkin:
        # Update existing check-in instead of creating duplicate
        update_query = """
            UPDATE event_checkins
            SET equipment_in_use = %s, notes = %s, status = 'checked_in', updated_at = NOW()
            WHERE id = %s
        """
        execute_query(update_query, (
            data.equipment_in_use or current_user.get("default_equipment"),
            data.notes,
            existing_checkin[0]["id"]
        ))

        return {
            "message": "Check-in updated successfully",
            "checkin_id": existing_checkin[0]["id"],
            "status": "checked_in"
        }

    # Create new check-in
    insert_query = """
        INSERT INTO event_checkins (winter_event_id, user_id, equipment_in_use, notes, status)
        VALUES (%s, %s, %s, %s, 'checked_in')
    """

    checkin_id = execute_query(insert_query, (
        event_id,
        user_id,
        data.equipment_in_use or current_user.get("default_equipment"),
        data.notes
    ))

    return {
        "message": "Checked in successfully",
        "checkin_id": checkin_id,
        "status": "checked_in"
    }

@router.post("/events/{event_id}/checkout")
async def check_out(event_id: int, data: CheckOutRequest, current_user: dict = Depends(get_current_user)):
    """Check out from an event"""
    user_id = int(current_user["sub"])

    # Find active check-in
    checkin = fetch_query(
        "SELECT id FROM event_checkins WHERE winter_event_id = %s AND user_id = %s AND checked_out_at IS NULL",
        (event_id, user_id)
    )

    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found")

    # Update check-out time and status
    update_query = """
        UPDATE event_checkins
        SET checked_out_at = NOW(), status = 'completed', notes = CONCAT(IFNULL(notes, ''), %s)
        WHERE id = %s
    """

    checkout_note = f"\n[Checkout] {data.notes}" if data.notes else ""
    execute_query(update_query, (checkout_note, checkin[0]["id"]))

    return {"message": "Checked out successfully"}

@router.get("/events/{event_id}/checkins")
async def get_event_checkins(event_id: int, current_user: dict = Depends(get_current_user)):
    """Get all check-ins for an event (Admin/Manager only)"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Admin/Manager access required")

    query = """
        SELECT
            ec.*,
            u.name as user_name,
            u.role as user_role,
            l.name as current_property_name,
            TIMESTAMPDIFF(HOUR, ec.checked_in_at, COALESCE(ec.checked_out_at, NOW())) as hours_active
        FROM event_checkins ec
        JOIN users u ON ec.user_id = u.id
        LEFT JOIN locations l ON ec.current_property_id = l.id
        WHERE ec.winter_event_id = %s
        ORDER BY ec.checked_in_at DESC
    """

    checkins = fetch_query(query, (event_id,))
    return checkins

@router.get("/events/{event_id}/checkins/active")
async def get_active_checkins(event_id: int, current_user: dict = Depends(get_current_user)):
    """Get currently checked-in crews for an event"""
    query = """
        SELECT
            ec.*,
            u.name as user_name,
            u.role as user_role,
            u.default_equipment,
            l.name as current_property_name,
            l.address as current_property_address,
            TIMESTAMPDIFF(MINUTE, ec.checked_in_at, NOW()) as minutes_active
        FROM event_checkins ec
        JOIN users u ON ec.user_id = u.id
        LEFT JOIN locations l ON ec.current_property_id = l.id
        WHERE ec.winter_event_id = %s
        AND ec.checked_out_at IS NULL
        AND ec.status IN ('checked_in', 'working')
        ORDER BY ec.status DESC, ec.checked_in_at ASC
    """

    checkins = fetch_query(query, (event_id,))
    return checkins

@router.get("/events/{event_id}/available-crews")
async def get_available_crews(event_id: int, current_user: dict = Depends(get_current_user)):
    """Get crews available for assignment (checked in but not currently working)"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Admin/Manager access required")

    query = """
        SELECT
            ec.*,
            u.name as user_name,
            u.role as user_role,
            u.phone as user_phone,
            TIMESTAMPDIFF(MINUTE, ec.last_location_update, NOW()) as minutes_since_location_update
        FROM event_checkins ec
        JOIN users u ON ec.user_id = u.id
        WHERE ec.winter_event_id = %s
        AND ec.checked_out_at IS NULL
        AND ec.status = 'checked_in'
        AND ec.current_property_id IS NULL
        ORDER BY ec.checked_in_at ASC
    """

    crews = fetch_query(query, (event_id,))
    return crews

@router.put("/events/{event_id}/checkin/location")
async def update_location(event_id: int, data: LocationUpdate, current_user: dict = Depends(get_current_user)):
    """Update current location and property"""
    user_id = int(current_user["sub"])

    # Find active check-in
    checkin = fetch_query(
        "SELECT id FROM event_checkins WHERE winter_event_id = %s AND user_id = %s AND checked_out_at IS NULL",
        (event_id, user_id)
    )

    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found")

    # Update location
    update_query = """
        UPDATE event_checkins
        SET last_location_lat = %s,
            last_location_lon = %s,
            last_location_update = NOW(),
            current_property_id = %s,
            status = COALESCE(%s, status)
        WHERE id = %s
    """

    execute_query(update_query, (
        data.lat,
        data.lon,
        data.current_property_id,
        data.status,
        checkin[0]["id"]
    ))

    return {"message": "Location updated successfully"}

@router.put("/events/{event_id}/checkin/status")
async def update_status(event_id: int, data: StatusUpdate, current_user: dict = Depends(get_current_user)):
    """Update check-in status (working, completed, unavailable)"""
    user_id = int(current_user["sub"])

    # Validate status
    valid_statuses = ["checked_in", "working", "completed", "unavailable"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    # Find active check-in
    checkin = fetch_query(
        "SELECT id FROM event_checkins WHERE winter_event_id = %s AND user_id = %s AND checked_out_at IS NULL",
        (event_id, user_id)
    )

    if not checkin:
        raise HTTPException(status_code=404, detail="No active check-in found")

    # Update status
    update_query = """
        UPDATE event_checkins
        SET status = %s,
            current_property_id = COALESCE(%s, current_property_id),
            notes = CONCAT(IFNULL(notes, ''), %s)
        WHERE id = %s
    """

    status_note = f"\n[{datetime.now().strftime('%H:%M')}] Status: {data.status}" + (f" - {data.notes}" if data.notes else "")

    execute_query(update_query, (
        data.status,
        data.current_property_id,
        status_note,
        checkin[0]["id"]
    ))

    return {"message": "Status updated successfully", "status": data.status}

@router.get("/my-checkin/{event_id}")
async def get_my_checkin(event_id: int, current_user: dict = Depends(get_current_user)):
    """Get current user's check-in status for an event"""
    user_id = int(current_user["sub"])

    query = """
        SELECT
            ec.*,
            l.name as current_property_name,
            TIMESTAMPDIFF(MINUTE, ec.checked_in_at, NOW()) as minutes_active
        FROM event_checkins ec
        LEFT JOIN locations l ON ec.current_property_id = l.id
        WHERE ec.winter_event_id = %s AND ec.user_id = %s AND ec.checked_out_at IS NULL
        ORDER BY ec.checked_in_at DESC
        LIMIT 1
    """

    checkin = fetch_query(query, (event_id, user_id))

    if not checkin:
        return {"checked_in": False}

    return {
        "checked_in": True,
        "checkin": checkin[0]
    }
