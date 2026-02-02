from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import execute_query, fetch_query
from auth import get_curre, get_customer_idnt_user
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# --- Winter Ops Model ---
class WinterOpsLog(BaseModel):
    property_id: int
    time_in: str
    time_out: str | None = None  # Optional - None when ticket is started, filled when finished
    status: str = "closed"  # 'open' or 'closed'

    # Optional fields
    contractor_id: int | None = None
    user_id: int | None = None  # Links to users table for current user
    contractor_name: str | None = None
    worker_name: str | None = None
    equipment: str | None = None
    bulk_salt_qty: float = 0
    bag_salt_qty: float = 0
    calcium_chloride_qty: float = 0
    customer_provided: bool = False
    notes: str | None = None

@router.post("/submit-winter-log/")
def submit_winter_log(log: WinterOpsLog, current_user: dict = Depends(get_current_user)):
    # Get authenticated user info from database
    user_id = int(current_user["sub"])
    user_role = current_user.get("role")
    user_info = fetch_query("SELECT name FROM users WHERE id = %s", (user_id,))
    user_name = user_info[0]['name'] if user_info else 'Unknown'

    # Always set user_id to authenticated user (for audit trail)
    log.user_id = user_id

    # Admin/Manager can submit logs for other contractors
    # Only override contractor fields if not already set
    if not log.contractor_id or not log.contractor_name:
        log.contractor_id = user_id
        log.contractor_name = user_name

    # If worker_name not specified, default to contractor name
    if not log.worker_name:
        log.worker_name = log.contractor_name

    # Auto-determine status based on time_out
    # If time_out is None/empty, ticket is still open. If time_out is provided, ticket is closed.
    if log.time_out is None or log.time_out == '':
        log.status = 'open'
    else:
        log.status = 'closed'

    # Determine which winter event this log belongs to based on time_in timestamp
    # Check if time_in falls within any event's date range (start_date to end_date)
    # Priority: 1) Active event if time matches, 2) Any event matching time range, 3) None

    winter_event_id = None
    event_match_type = "none"

    # First, try to find an event whose date range contains the log's time_in
    time_based_event = fetch_query(
        """
        SELECT id, event_name, status
        FROM winter_events
        WHERE %s >= start_date
        AND (%s <= end_date OR end_date IS NULL)
        ORDER BY
            CASE WHEN status = 'active' THEN 1 ELSE 2 END,
            start_date DESC
        LIMIT 1
        """,
        (log.time_in, log.time_in)
    )

    if time_based_event:
        winter_event_id = time_based_event[0]['id']
        event_match_type = "timestamp_match"
        event_status = time_based_event[0]['status']
        message = f"Winter Ops Log submitted successfully! (Auto-assigned to '{time_based_event[0]['event_name']}' based on timestamp)"
    else:
        # No event matches the timestamp - leave winter_event_id as NULL
        message = "Winter Ops Log submitted successfully! (⚠️ No winter event matches this log's timestamp)"

    query = """
        INSERT INTO winter_ops_logs
        (property_id, contractor_id, user_id, contractor_name, worker_name, equipment, time_in, time_out, status, bulk_salt_qty, bag_salt_qty, calcium_chloride_qty, customer_provided, notes, winter_event_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        log.property_id,
        log.contractor_id,
        log.user_id,
        log.contractor_name,
        log.worker_name,
        log.equipment,
        log.time_in,
        log.time_out,
        log.status,
        log.bulk_salt_qty,
        log.bag_salt_qty,
        log.calcium_chloride_qty,
        log.customer_provided,
        log.notes,
        winter_event_id
    )
    result = execute_query(query, values)

    # Get the ID of the inserted log
    log_id = result if result else None

    return {"message": message, "winter_event_id": winter_event_id, "log_id": log_id, "status": log.status}

@router.get("/winter-logs/")
def get_winter_logs():
    query = """
        SELECT
            w.id, l.name AS property_name, w.property_id,
            w.contractor_id, w.user_id, w.contractor_name, w.worker_name, w.equipment,
            w.time_in, w.time_out, w.status,
            w.bulk_salt_qty, w.bag_salt_qty, w.calcium_chloride_qty, w.customer_provided, w.notes,
            w.winter_event_id,
            we.event_name AS winter_event_name
        FROM winter_ops_logs w
        JOIN locations l ON w.property_id = l.id
        LEFT JOIN winter_events we ON w.winter_event_id = we.id
        ORDER BY w.time_in DESC
    """
    return fetch_query(query)

@router.get("/winter-logs/open/")
def get_open_winter_logs(current_user: dict = Depends(get_current_user)):
    """Get all open (in-progress) winter logs for the current user"""
    user_id = int(current_user["sub"])

    query = """
        SELECT
            w.id, l.name AS property_name, l.address AS property_address, w.property_id,
            w.contractor_id, w.user_id, w.contractor_name, w.worker_name, w.equipment,
            w.time_in, w.time_out, w.status,
            w.bulk_salt_qty, w.bag_salt_qty, w.calcium_chloride_qty, w.customer_provided, w.notes,
            w.winter_event_id,
            we.event_name AS winter_event_name
        FROM winter_ops_logs w
        JOIN locations l ON w.property_id = l.id
        LEFT JOIN winter_events we ON w.winter_event_id = we.id
        WHERE w.status = 'open' AND w.user_id = %s
        ORDER BY w.time_in DESC
    """
    return fetch_query(query, (user_id,))

@router.put("/winter-logs/{log_id}/close")
def close_winter_log(log_id: int, time_out: str, current_user: dict = Depends(get_current_user)):
    """Close an open winter log by setting time_out and status"""
    user_id = int(current_user["sub"])

    # Verify this log belongs to the current user and is open
    verify_query = """
        SELECT id, user_id, status FROM winter_ops_logs
        WHERE id = %s
    """
    log = fetch_query(verify_query, (log_id,))

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    if log[0]['user_id'] != user_id and current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="You can only close your own logs")

    if log[0]['status'] != 'open':
        raise HTTPException(status_code=400, detail="Log is already closed")

    # Close the log
    query = """
        UPDATE winter_ops_logs
        SET time_out = %s, status = 'closed'
        WHERE id = %s
    """
    execute_query(query, (time_out, log_id))

    return {"message": "Log closed successfully", "log_id": log_id}

@router.put("/winter-logs/{log_id}")
def update_winter_log(log_id: int, log: WinterOpsLog, current_user: dict = Depends(get_current_user)):
    """Update winter ops log - Users can update their own logs, Admin/Manager can update any"""
    user_id = int(current_user["sub"])
    user_role = current_user["role"]

    # Check if log exists and get its owner
    existing_log = fetch_query("SELECT user_id FROM winter_ops_logs WHERE id = %s", (log_id,))
    if not existing_log:
        raise HTTPException(status_code=404, detail="Log not found")

    log_owner_id = existing_log[0]['user_id']

    # Allow if: user owns the log OR user is Admin/Manager
    if log_owner_id != user_id and user_role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="You can only update your own logs")

    try:
        # Auto-determine status based on time_out
        # If time_out is None/empty, ticket is still open. If time_out is provided, ticket is closed.
        if log.time_out is None or log.time_out == '':
            log.status = 'open'
        else:
            log.status = 'closed'

        # Auto-assign to winter event based on time_in timestamp
        time_based_event = fetch_query(
            """
            SELECT id, event_name
            FROM winter_events
            WHERE %s >= start_date
            AND (%s <= end_date OR end_date IS NULL)
            ORDER BY
                CASE WHEN status = 'active' THEN 1 ELSE 2 END,
                start_date DESC
            LIMIT 1
            """,
            (log.time_in, log.time_in)
        )

        winter_event_id = time_based_event[0]['id'] if time_based_event else None

        query = """
            UPDATE winter_ops_logs SET
                property_id = %s, contractor_id = %s, user_id = %s, contractor_name = %s, worker_name = %s,
                equipment = %s, time_in = %s, time_out = %s, status = %s,
                bulk_salt_qty = %s, bag_salt_qty = %s, calcium_chloride_qty = %s,
                customer_provided = %s, notes = %s, winter_event_id = %s
            WHERE id = %s
        """
        values = (
            log.property_id, log.contractor_id, log.user_id, log.contractor_name, log.worker_name,
            log.equipment, log.time_in, log.time_out, log.status,
            log.bulk_salt_qty, log.bag_salt_qty, log.calcium_chloride_qty,
            log.customer_provided, log.notes, winter_event_id, log_id
        )
        execute_query(query, values)

        message = "Winter log updated successfully!"
        if time_based_event:
            message += f" (Auto-assigned to event: '{time_based_event[0]['event_name']}')"

        return {"message": message, "winter_event_id": winter_event_id}
    except Exception as e:
        logger.error(f"Failed to update winter log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update log: {str(e)}")

@router.delete("/winter-logs/{log_id}")
def delete_winter_log(log_id: int, current_user: dict = Depends(get_current_user)):
    """Delete winter ops log (Admin only)"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")

    try:
        execute_query("DELETE FROM winter_ops_logs WHERE id = %s", (log_id,))
        return {"message": "Winter log deleted successfully!"}
    except Exception as e:
        logger.error(f"Failed to delete winter log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete log: {str(e)}")

@router.put("/winter-logs/{log_id}/assign-event")
def assign_log_to_event(log_id: int, event_data: dict, current_user: dict = Depends(get_current_user)):
    """Manually assign a winter log to a specific event (Admin/Manager only)"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")

    winter_event_id = event_data.get("winter_event_id")

    if not winter_event_id:
        raise HTTPException(status_code=400, detail="winter_event_id is required")

    try:
        # Verify the event exists
        event = fetch_query("SELECT id, event_name FROM winter_events WHERE id = %s", (winter_event_id,))
        if not event:
            raise HTTPException(status_code=404, detail="Winter event not found")

        # Update the log
        execute_query(
            "UPDATE winter_ops_logs SET winter_event_id = %s WHERE id = %s",
            (winter_event_id, log_id)
        )

        return {
            "message": f"Log successfully assigned to event '{event[0]['event_name']}'",
            "winter_event_id": winter_event_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign log to event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to assign log: {str(e)}")

@router.post("/winter-logs/reassign-events/")
def reassign_winter_events(current_user: dict = Depends(get_current_user)):
    """
    Retroactively assign winter logs to events based on their time_in timestamps
    This fixes logs that were created before/after an event but have timestamps within the event's date range
    Admin/Manager only
    """
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Admin or Manager access required")

    try:
        # Update all logs to have correct winter_event_id based on their time_in
        # Use a subquery to find the best matching event for each log
        update_query = """
            UPDATE winter_ops_logs wol
            SET wol.winter_event_id = (
                SELECT we.id
                FROM winter_events we
                WHERE wol.time_in >= we.start_date
                  AND (wol.time_in <= we.end_date OR we.end_date IS NULL)
                ORDER BY
                    CASE WHEN we.status = 'active' THEN 1 ELSE 2 END,
                    we.start_date DESC
                LIMIT 1
            )
        """

        execute_query(update_query)

        # Get statistics
        stats = fetch_query("""
            SELECT
                COUNT(*) as total_logs,
                SUM(CASE WHEN winter_event_id IS NOT NULL THEN 1 ELSE 0 END) as assigned_logs,
                SUM(CASE WHEN winter_event_id IS NULL THEN 1 ELSE 0 END) as unassigned_logs
            FROM winter_ops_logs
        """)

        return {
            "message": "Winter logs reassigned to events based on timestamps",
            "total_logs": stats[0]['total_logs'],
            "assigned_to_events": stats[0]['assigned_logs'],
            "unassigned": stats[0]['unassigned_logs']
        }

    except Exception as e:
        logger.error(f"Failed to reassign winter events: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reassign events: {str(e)}")

# --- Green Ops Model ---
class GreenOpsLog(BaseModel):
    property_id: int
    contractor_id: int
    contractor_name: str
    worker_name: str  # The subcontractor/worker (Last, First)
    time_in: str
    time_out: str
    service_type: str
    products_used: str
    quantity_used: float
    notes: str

@router.post("/submit-green-log/")
def submit_green_log(log: GreenOpsLog):
    query = """
        INSERT INTO green_services_logs
        (property_id, contractor_id, contractor_name, worker_name, time_in, time_out, service_type, products_used, quantity_used, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        log.property_id,
        log.contractor_id,
        log.contractor_name,
        log.worker_name,
        log.time_in,
        log.time_out,
        log.service_type,
        log.products_used,
        log.quantity_used,
        log.notes
    )
    execute_query(query, values)
    return {"message": "Green Services Log submitted successfully!"}

@router.get("/green-logs/")
def get_green_logs():
    query = """
        SELECT
            g.id, l.name AS property_name, g.property_id,
            g.contractor_id, g.contractor_name, g.worker_name,
            g.time_in, g.time_out, g.service_type, g.products_used,
            g.quantity_used, g.notes
        FROM green_services_logs g
        JOIN locations l ON g.property_id = l.id
        ORDER BY g.time_in DESC
    """
    return fetch_query(query)

@router.put("/green-logs/{log_id}")
def update_green_log(log_id: int, log: GreenOpsLog, current_user: dict = Depends(get_current_user)):
    """Update green services log (Admin/Manager only)"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Admins and Managers only!")

    try:
        query = """
            UPDATE green_services_logs SET
                property_id = %s, contractor_id = %s, contractor_name = %s, worker_name = %s,
                time_in = %s, time_out = %s, service_type = %s,
                products_used = %s, quantity_used = %s, notes = %s
            WHERE id = %s
        """
        values = (
            log.property_id, log.contractor_id, log.contractor_name, log.worker_name,
            log.time_in, log.time_out, log.service_type,
            log.products_used, log.quantity_used, log.notes, log_id
        )
        execute_query(query, values)
        return {"message": "Green services log updated successfully!"}
    except Exception as e:
        logger.error(f"Failed to update green log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update log: {str(e)}")

@router.delete("/green-logs/{log_id}")
def delete_green_log(log_id: int, current_user: dict = Depends(get_current_user)):
    """Delete green services log (Admin only)"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")

    try:
        execute_query("DELETE FROM green_services_logs WHERE id = %s", (log_id,))
        return {"message": "Green services log deleted successfully!"}
    except Exception as e:
        logger.error(f"Failed to delete green log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete log: {str(e)}")

# Helper function to snap time to nearest 15 minutes
def snap_to_15_minutes(dt_str: str) -> str:
    """
    Snap a datetime string to the nearest 15-minute interval
    Example: 2024-01-15 13:02:00 -> 2024-01-15 13:00:00
             2024-01-15 13:13:00 -> 2024-01-15 13:15:00
    """
    from datetime import datetime, timedelta

    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

    # Round to nearest 15 minutes
    minute = dt.minute
    if minute < 8:
        new_minute = 0
    elif minute < 23:
        new_minute = 15
    elif minute < 38:
        new_minute = 30
    elif minute < 53:
        new_minute = 45
    else:
        # Round up to next hour
        dt += timedelta(hours=1)
        new_minute = 0

    dt = dt.replace(minute=new_minute, second=0, microsecond=0)
    return dt.isoformat()

@router.get("/suggested-log-time/")
def get_suggested_log_time(current_user: dict = Depends(get_current_user)):
    """
    Get suggested start time for new log based on:
    1. Previous log's time_out (snapped to 15min)
    2. Current active winter event start time (snapped to 15min)
    3. Current time (snapped to 15min)

    Also returns user's default equipment
    """
    from datetime import datetime

    user_id = int(current_user["sub"])
    suggested_time = None
    source = "current_time"

    # Get user's default equipment
    user_query = "SELECT default_equipment FROM users WHERE id = %s"
    user_result = fetch_query(user_query, (user_id,))
    default_equipment = user_result[0]['default_equipment'] if user_result and user_result[0].get('default_equipment') else None

    # Try to get most recent log for this user
    last_log_query = """
        SELECT time_out
        FROM winter_ops_logs
        WHERE user_id = %s AND time_out IS NOT NULL
        ORDER BY time_out DESC
        LIMIT 1
    """
    last_log = fetch_query(last_log_query, (user_id,))

    if last_log and last_log[0]['time_out']:
        # Use previous log's end time
        suggested_time = str(last_log[0]['time_out'])
        source = "previous_log_end"
    else:
        # Try to get active winter event start time
        event_query = """
            SELECT start_date
            FROM winter_events
            WHERE status = 'active'
            ORDER BY start_date DESC
            LIMIT 1
        """
        event = fetch_query(event_query)

        if event and event[0]['start_date']:
            suggested_time = str(event[0]['start_date'])
            source = "winter_event_start"
        else:
            # Use current time
            suggested_time = datetime.now().isoformat()
            source = "current_time"

    # Snap to 15 minutes
    snapped_time = snap_to_15_minutes(suggested_time)

    return {
        "suggested_time": snapped_time,
        "source": source,
        "default_equipment": default_equipment
    }

@router.post("/snap-time/")
def snap_time_endpoint(time_str: str):
    """Utility endpoint to snap any time to 15-minute intervals"""
    return {"original": time_str, "snapped": snap_to_15_minutes(time_str)}
