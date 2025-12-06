from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from db import fetch_query, execute_query
from auth import get_current_user

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
async def get_routes(current_user: dict = Depends(get_current_user)):
    """Get all routes for current user"""
    user_id = int(current_user["sub"])

    query = """
        SELECT r.*, u.name as owner_name,
               (SELECT COUNT(*) FROM route_properties WHERE route_id = r.id) as property_count
        FROM routes r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id = %s
        ORDER BY r.created_at DESC
    """

    routes = fetch_query(query, (user_id,))
    return routes

@router.get("/routes/{route_id}")
async def get_route(route_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific route with its properties"""
    user_id = int(current_user["sub"])

    # Get route details
    query = """
        SELECT r.*, u.name as owner_name
        FROM routes r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = %s AND r.user_id = %s
    """
    routes = fetch_query(query, (route_id, user_id))

    if not routes:
        raise HTTPException(status_code=404, detail="Route not found")

    route = routes[0]

    # Get properties in this route
    properties_query = """
        SELECT l.*, rp.sequence_order, rp.estimated_time_minutes, rp.notes
        FROM locations l
        JOIN route_properties rp ON l.id = rp.property_id
        WHERE rp.route_id = %s
        ORDER BY rp.sequence_order ASC
    """
    properties = fetch_query(properties_query, (route_id,))
    route["properties"] = properties

    return route

@router.post("/routes/")
async def create_route(
    route_data: RouteCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new route"""
    user_id = int(current_user["sub"])

    query = """
        INSERT INTO routes (name, description, user_id, is_template)
        VALUES (%s, %s, %s, %s)
    """

    route_id = execute_query(query, (
        route_data.name,
        route_data.description,
        user_id,
        route_data.is_template
    ))

    return {
        "message": "Route created successfully",
        "route_id": route_id
    }

@router.put("/routes/")
async def update_route(
    route_data: RouteUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a route"""
    user_id = int(current_user["sub"])

    # Verify ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s"
    result = fetch_query(check_query, (route_data.id,))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this route")

    query = """
        UPDATE routes
        SET name = %s, description = %s, is_template = %s
        WHERE id = %s
    """

    execute_query(query, (
        route_data.name,
        route_data.description,
        route_data.is_template,
        route_data.id
    ))

    return {"message": "Route updated successfully"}

@router.delete("/routes/{route_id}")
async def delete_route(route_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a route"""
    user_id = int(current_user["sub"])

    # Verify ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s"
    result = fetch_query(check_query, (route_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this route")

    # Delete the route (cascade will delete route_properties)
    query = "DELETE FROM routes WHERE id = %s"
    execute_query(query, (route_id,))

    return {"message": "Route deleted successfully"}

@router.post("/routes/add-property/")
async def add_property_to_route(
    data: RoutePropertyAdd,
    current_user: dict = Depends(get_current_user)
):
    """Add a property to a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s"
    result = fetch_query(check_query, (data.route_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Route not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this route")

    # Check if property exists
    prop_check = "SELECT id FROM locations WHERE id = %s"
    prop_result = fetch_query(prop_check, (data.property_id,))

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
    current_user: dict = Depends(get_current_user)
):
    """Remove a property from a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s"
    result = fetch_query(check_query, (route_id,))

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
    current_user: dict = Depends(get_current_user)
):
    """Reorder properties in a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s"
    result = fetch_query(check_query, (data.route_id,))

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
    current_user: dict = Depends(get_current_user)
):
    """Assign users to a route"""
    user_id = int(current_user["sub"])

    # Verify route ownership
    check_query = "SELECT user_id FROM routes WHERE id = %s"
    result = fetch_query(check_query, (data.route_id,))

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
