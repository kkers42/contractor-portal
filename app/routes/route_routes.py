from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from db import fetch_query, execute_query
from auth import get_current_user, get_customer_id

router = APIRouter()

class RouteCreate(BaseModel):
    name: str
    description: str | None = None
    is_template: bool = False

class RouteUpdate(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_template: bool = False

class RoutePropertyAdd(BaseModel):
    route_id: int
    property_id: int
    sequence_order: int
    estimated_time_minutes: int | None = None
    notes: str | None = None

class RoutePropertyReorder(BaseModel):
    route_id: int
    property_orders: List[dict]  # [{"property_id": 1, "sequence_order": 1}, ...]

class RouteAssignUsers(BaseModel):
    route_id: int
    user_ids: List[int]

@router.get("/routes/")
async def get_routes(
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Get all routes for current user"""
    user_id = int(current_user["sub"])

    query = """
        SELECT r.*, u.name as owner_name,
               (SELECT COUNT(*) FROM route_properties WHERE route_id = r.id) as property_count
        FROM routes r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id = %s AND r.customer_id = %s
        ORDER BY r.created_at DESC
    """

    routes = fetch_query(query, (user_id, customer_id))
    return routes

@router.get("/routes/{route_id}")
async def get_route(
    route_id: int,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Get a specific route with its properties"""
    user_id = int(current_user["sub"])

    # Get route details
    query = """
        SELECT r.*, u.name as owner_name
        FROM routes r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = %s AND r.user_id = %s AND r.customer_id = %s
    """
    routes = fetch_query(query, (route_id, user_id, customer_id))

    if not routes:
        raise HTTPException(status_code=404, detail="Route not found")

    route = routes[0]

    # Get properties in this route
    properties_query = """
        SELECT l.*, rp.sequence_order, rp.estimated_time_minutes, rp.notes
        FROM locations l
        JOIN route_properties rp ON l.id = rp.property_id
        WHERE rp.route_id = %s AND l.customer_id = %s
        ORDER BY rp.sequence_order ASC
    """
    properties = fetch_query(properties_query, (route_id, customer_id))
    route["properties"] = properties

    return route

@router.post("/routes/")
async def create_route(
    route_data: RouteCreate,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Create a new route"""
    user_id = int(current_user["sub"])

    query = """
        INSERT INTO routes (name, description, user_id, is_template, customer_id)
        VALUES (%s, %s, %s, %s, %s)
    """

    route_id = execute_query(query, (
        route_data.name,
        route_data.description,
        user_id,
        route_data.is_template,
        customer_id
    ))

    return {
        "message": "Route created successfully",
        "route_id": route_id
    }

@router.put("/routes/")
async def update_route(
    route_data: RouteUpdate,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Update a route"""
    user_id = int(current_user["sub"])

    # Verify ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s AND customer_id = %s"
    result = fetch_query(check_query, (route_data.id, customer_id))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this route")

    query = """
        UPDATE routes
        SET name = %s, description = %s, is_template = %s
        WHERE id = %s AND customer_id = %s
    """

    execute_query(query, (
        route_data.name,
        route_data.description,
        route_data.is_template,
        route_data.id,
        customer_id
    ))

    return {"message": "Route updated successfully"}

@router.delete("/routes/{route_id}")
async def delete_route(
    route_id: int,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Delete a route"""
    user_id = int(current_user["sub"])

    # Verify ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s AND customer_id = %s"
    result = fetch_query(check_query, (route_id, customer_id))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this route")

    # Delete the route (cascade will delete route_properties)
    query = "DELETE FROM routes WHERE id = %s AND customer_id = %s"
    execute_query(query, (route_id, customer_id))

    return {"message": "Route deleted successfully"}

@router.post("/routes/add-property/")
async def add_property_to_route(
    data: RoutePropertyAdd,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Add a property to a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s AND customer_id = %s"
    result = fetch_query(check_query, (data.route_id, customer_id))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this route")

    # Check if property exists
    prop_check = "SELECT id FROM locations WHERE id = %s AND customer_id = %s"
    prop_result = fetch_query(prop_check, (data.property_id, customer_id))

    if not prop_result:
        raise HTTPException(status_code=404, detail="Property not found")

    # Add to route (or update if exists)
    query = """
        INSERT INTO route_properties (route_id, property_id, sequence_order, estimated_time_minutes, notes)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sequence_order = VALUES(sequence_order),
            estimated_time_minutes = VALUES(estimated_time_minutes),
            notes = VALUES(notes)
    """

    execute_query(query, (
        data.route_id,
        data.property_id,
        data.sequence_order,
        data.estimated_time_minutes,
        data.notes
    ))

    return {"message": "Property added to route"}

@router.delete("/routes/{route_id}/properties/{property_id}")
async def remove_property_from_route(
    route_id: int,
    property_id: int,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Remove a property from a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s AND customer_id = %s"
    result = fetch_query(check_query, (route_id, customer_id))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this route")

    # Remove from route
    query = "DELETE FROM route_properties WHERE route_id = %s AND property_id = %s"
    execute_query(query, (route_id, property_id))

    return {"message": "Property removed from route"}

@router.put("/routes/reorder/")
async def reorder_route_properties(
    data: RoutePropertyReorder,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Reorder properties in a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s AND customer_id = %s"
    result = fetch_query(check_query, (data.route_id, customer_id))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this route")

    # Update sequence orders
    for item in data.property_orders:
        query = """
            UPDATE route_properties
            SET sequence_order = %s
            WHERE route_id = %s AND property_id = %s
        """
        execute_query(query, (
            item["sequence_order"],
            data.route_id,
            item["property_id"]
        ))

    return {"message": "Route properties reordered successfully"}

@router.post("/routes/assign-users/")
async def assign_users_to_route(
    data: RouteAssignUsers,
    current_user: dict = Depends(get_current_user),
    customer_id: str = Depends(get_customer_id)
):
    """Assign users to a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s AND customer_id = %s"
    result = fetch_query(check_query, (data.route_id, customer_id))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this route")

    # First, remove all existing assignments for this route
    delete_query = "DELETE FROM route_assignments WHERE route_id = %s"
    execute_query(delete_query, (data.route_id,))

    # Then add new assignments
    for assigned_user_id in data.user_ids:
        insert_query = """
            INSERT INTO route_assignments (route_id, user_id)
            VALUES (%s, %s)
        """
        execute_query(insert_query, (data.route_id, assigned_user_id))

    return {"message": f"Route assigned to {len(data.user_ids)} user(s)"}

@router.get("/routes/{route_id}/assigned-users/")
async def get_route_assigned_users(
    route_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get users assigned to a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership or assignment
    check_query = """
        SELECT user_id FROM routes WHERE id = %s
    """
    result = fetch_query(check_query, (route_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    # Get assigned users
    query = """
        SELECT u.id, u.name, u.email, u.role
        FROM users u
        JOIN route_assignments ra ON u.id = ra.user_id
        WHERE ra.route_id = %s
    """
    assigned_users = fetch_query(query, (route_id,))

    return assigned_users if assigned_users else []


# ==================== ROUTE ACTIVATION ====================

class RouteActivation(BaseModel):
    route_id: int
    winter_event_id: int
    assigned_user_id: int  # Which contractor to assign this route to

@router.post("/routes/complete-property/")
async def complete_route_property(
    log_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark a property in a route as complete
    Automatically activates the next property in sequence
    """
    user_id = int(current_user["sub"])

    # Get current log entry
    log_entry = fetch_query(
        """SELECT id, property_id, user_id, winter_event_id, route_id, route_sequence, route_status
           FROM winter_ops_logs
           WHERE id = %s""",
        (log_id,)
    )

    if not log_entry:
        raise HTTPException(status_code=404, detail="Log entry not found")

    log_entry = log_entry[0]

    # Verify user owns this log or is admin/manager
    if log_entry["user_id"] != user_id and current_user.get("role") not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Not authorized to complete this log")

    if not log_entry["route_id"]:
        raise HTTPException(status_code=400, detail="This log is not part of a route")

    # Mark current as complete
    execute_query(
        """UPDATE winter_ops_logs
           SET route_status = 'complete', status = 'closed', time_out = NOW()
           WHERE id = %s""",
        (log_id,)
    )

    # Find next property in route
    next_property = fetch_query(
        """SELECT id, property_id
           FROM winter_ops_logs
           WHERE route_id = %s
           AND winter_event_id = %s
           AND user_id = %s
           AND route_sequence > %s
           AND route_status = 'queued'
           ORDER BY route_sequence ASC
           LIMIT 1""",
        (log_entry["route_id"], log_entry["winter_event_id"],
         log_entry["user_id"], log_entry["route_sequence"])
    )

    next_property_name = None

    if next_property:
        # Activate next property and set time_in and status to 'open'
        execute_query(
            """UPDATE winter_ops_logs
               SET route_status = 'active', status = 'open', time_in = NOW()
               WHERE id = %s""",
            (next_property[0]["id"],)
        )

        # Get property name
        prop_info = fetch_query("SELECT name FROM locations WHERE id = %s", (next_property[0]["property_id"],))
        if prop_info:
            next_property_name = prop_info[0]["name"]

    # Get route progress
    progress = fetch_query(
        """SELECT
             COUNT(*) as total,
             SUM(CASE WHEN route_status = 'complete' THEN 1 ELSE 0 END) as completed,
             SUM(CASE WHEN route_status = 'active' THEN 1 ELSE 0 END) as active,
             SUM(CASE WHEN route_status = 'queued' THEN 1 ELSE 0 END) as queued
           FROM winter_ops_logs
           WHERE route_id = %s AND winter_event_id = %s AND user_id = %s""",
        (log_entry["route_id"], log_entry["winter_event_id"], log_entry["user_id"])
    )

    progress_info = progress[0] if progress else {"total": 0, "completed": 0, "active": 0, "queued": 0}

    return {
        "ok": True,
        "message": "Property marked complete",
        "next_property": next_property_name,
        "route_complete": progress_info["completed"] == progress_info["total"],
        "progress": progress_info
    }


@router.get("/routes/{route_id}/progress/")
async def get_route_progress(
    route_id: int,
    winter_event_id: int,
    user_id_param: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get progress for a route in a specific winter event
    """
    user_id = int(current_user["sub"])

    # If no user specified, use current user
    if not user_id_param:
        user_id_param = user_id

    # Get all log entries for this route
    logs = fetch_query(
        """SELECT w.id, w.property_id, w.route_sequence, w.route_status, w.status,
                  w.time_in, w.time_out, w.estimated_minutes,
                  l.name as property_name, l.address as property_address
           FROM winter_ops_logs w
           JOIN locations l ON w.property_id = l.id
           WHERE w.route_id = %s AND w.winter_event_id = %s AND w.user_id = %s
           ORDER BY w.route_sequence ASC""",
        (route_id, winter_event_id, user_id_param)
    )

    # Calculate stats
    total = len(logs)
    completed = sum(1 for log in logs if log["route_status"] == "complete")
    active = sum(1 for log in logs if log["route_status"] == "active")
    queued = sum(1 for log in logs if log["route_status"] == "queued")

    return {
        "route_id": route_id,
        "winter_event_id": winter_event_id,
        "user_id": user_id_param,
        "total_properties": total,
        "completed": completed,
        "active": active,
        "queued": queued,
        "percent_complete": round((completed / total * 100) if total > 0 else 0, 1),
        "properties": logs
    }
