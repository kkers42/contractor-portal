from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import execute_query, fetch_query
from auth import get_current_user

router = APIRouter()

# --- Winter Ops Model ---
class WinterOpsLog(BaseModel):
    property_id: int
    time_in: str
    time_out: str | None = None  # Optional - None when ticket is started, filled when finished

    # Optional fields
    contractor_id: int | None = None
    contractor_name: str | None = None
    worker_name: str | None = None
    equipment: str | None = None
    bulk_salt_qty: float = 0
    bag_salt_qty: float = 0
    calcium_chloride_qty: float = 0
    customer_provided: bool = False
    notes: str | None = None

@router.post("/submit-winter-log/")
def submit_winter_log(log: WinterOpsLog):
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
        (property_id, contractor_id, contractor_name, worker_name, equipment, time_in, time_out, bulk_salt_qty, bag_salt_qty, calcium_chloride_qty, customer_provided, notes, winter_event_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        log.property_id,
        log.contractor_id,
        log.contractor_name,
        log.worker_name,
        log.equipment,
        log.time_in,
        log.time_out,
        log.bulk_salt_qty,
        log.bag_salt_qty,
        log.calcium_chloride_qty,
        log.customer_provided,
        log.notes,
        winter_event_id
    )
    execute_query(query, values)

    return {"message": message, "winter_event_id": winter_event_id}

@router.get("/winter-logs/")
def get_winter_logs():
    query = """
        SELECT
            w.id, l.name AS property_name, w.property_id,
            w.contractor_id, w.contractor_name, w.worker_name, w.equipment,
            w.time_in, w.time_out,
            w.bulk_salt_qty, w.bag_salt_qty, w.calcium_chloride_qty, w.customer_provided, w.notes,
            w.winter_event_id,
            we.event_name AS winter_event_name
        FROM winter_ops_logs w
        JOIN locations l ON w.property_id = l.id
        LEFT JOIN winter_events we ON w.winter_event_id = we.id
        ORDER BY w.time_in DESC
    """
    return fetch_query(query)

@router.put("/winter-logs/{log_id}")
def update_winter_log(log_id: int, log: WinterOpsLog, current_user: dict = Depends(get_current_user)):
    """Update winter ops log (Admin/Manager only) - Auto-assigns to event based on timestamp"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Admins and Managers only!")

    try:
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
                property_id = %s, contractor_id = %s, contractor_name = %s, worker_name = %s,
                equipment = %s, time_in = %s, time_out = %s,
                bulk_salt_qty = %s, bag_salt_qty = %s, calcium_chloride_qty = %s,
                customer_provided = %s, notes = %s, winter_event_id = %s
            WHERE id = %s
        """
        values = (
            log.property_id, log.contractor_id, log.contractor_name, log.worker_name,
            log.equipment, log.time_in, log.time_out,
            log.bulk_salt_qty, log.bag_salt_qty, log.calcium_chloride_qty,
            log.customer_provided, log.notes, winter_event_id, log_id
        )
        execute_query(query, values)

        message = "Winter log updated successfully!"
        if time_based_event:
            message += f" (Auto-assigned to event: '{time_based_event[0]['event_name']}')"

        return {"message": message, "winter_event_id": winter_event_id}
    except Exception as e:
        print(f"[ERROR] Failed to update winter log: {str(e)}")
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
        print(f"[ERROR] Failed to delete winter log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete log: {str(e)}")

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
        update_query = """
            UPDATE winter_ops_logs wol
            LEFT JOIN (
                SELECT
                    we.id as event_id,
                    we.start_date,
                    we.end_date,
                    we.event_name,
                    we.status
                FROM winter_events we
            ) events ON wol.time_in >= events.start_date
                AND (wol.time_in <= events.end_date OR events.end_date IS NULL)
            SET wol.winter_event_id = events.event_id
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
        print(f"[ERROR] Failed to reassign winter events: {str(e)}")
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
        print(f"[ERROR] Failed to update green log: {str(e)}")
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
        print(f"[ERROR] Failed to delete green log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete log: {str(e)}")
