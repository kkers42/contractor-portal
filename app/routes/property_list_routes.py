from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from db import fetch_query, execute_query
from auth import get_current_user

router = APIRouter()

class PropertyListCreate(BaseModel):
    name: str
    is_shared: bool = False
    filters: dict | None = None

class PropertyListUpdate(BaseModel):
    id: int
    name: str
    is_shared: bool = False
    filters: dict | None = None

class AddPropertyToList(BaseModel):
    list_id: int
    property_id: int

@router.get("/property-lists/")
async def get_property_lists(current_user: dict = Depends(get_current_user)):
    """Get all property lists for current user"""
    user_id = int(current_user["sub"])

    # Get lists owned by user or shared lists
    query = """
        SELECT pl.*, u.name as owner_name
        FROM property_lists pl
        JOIN users u ON pl.user_id = u.id
        WHERE pl.user_id = %s OR pl.is_shared = TRUE
        ORDER BY pl.created_at DESC
    """

    lists = fetch_query(query, (user_id,))

    # Get property count for each list
    for lst in lists:
        count_query = "SELECT COUNT(*) as count FROM property_list_items WHERE list_id = %s"
        count_result = fetch_query(count_query, (lst["id"],))
        lst["property_count"] = count_result[0]["count"] if count_result else 0

    return lists

@router.get("/property-lists/{list_id}")
async def get_property_list(list_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific property list with its properties"""
    user_id = int(current_user["sub"])

    # Get list details
    query = """
        SELECT pl.*, u.name as owner_name
        FROM property_lists pl
        JOIN users u ON pl.user_id = u.id
        WHERE pl.id = %s AND (pl.user_id = %s OR pl.is_shared = TRUE)
    """
    lists = fetch_query(query, (list_id, user_id))

    if not lists:
        raise HTTPException(status_code=404, detail="Property list not found")

    property_list = lists[0]

    # Get properties in this list
    properties_query = """
        SELECT l.*, pli.added_at
        FROM locations l
        JOIN property_list_items pli ON l.id = pli.property_id
        WHERE pli.list_id = %s
        ORDER BY pli.added_at DESC
    """
    properties = fetch_query(properties_query, (list_id,))
    property_list["properties"] = properties

    return property_list

@router.post("/property-lists/")
async def create_property_list(
    list_data: PropertyListCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new property list"""
    user_id = int(current_user["sub"])

    # Convert filters dict to JSON string if present
    filters_json = None
    if list_data.filters:
        import json
        filters_json = json.dumps(list_data.filters)

    query = """
        INSERT INTO property_lists (name, user_id, is_shared, filters)
        VALUES (%s, %s, %s, %s)
    """

    list_id = execute_query(query, (
        list_data.name,
        user_id,
        list_data.is_shared,
        filters_json
    ))

    return {
        "message": "Property list created successfully",
        "list_id": list_id
    }

@router.put("/property-lists/")
async def update_property_list(
    list_data: PropertyListUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a property list"""
    user_id = int(current_user["sub"])

    # Verify ownership
    check_query = "SELECT user_id FROM property_lists WHERE id = %s"
    result = fetch_query(check_query, (list_data.id,))

    if not result:
        raise HTTPException(status_code=404, detail="Property list not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this list")

    # Convert filters dict to JSON string if present
    filters_json = None
    if list_data.filters:
        import json
        filters_json = json.dumps(list_data.filters)

    query = """
        UPDATE property_lists
        SET name = %s, is_shared = %s, filters = %s
        WHERE id = %s
    """

    execute_query(query, (
        list_data.name,
        list_data.is_shared,
        filters_json,
        list_data.id
    ))

    return {"message": "Property list updated successfully"}

@router.delete("/property-lists/{list_id}")
async def delete_property_list(list_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a property list"""
    user_id = int(current_user["sub"])

    # Verify ownership
    check_query = "SELECT user_id FROM property_lists WHERE id = %s"
    result = fetch_query(check_query, (list_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Property list not found")

    if result[0]["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this list")

    # Delete the list (cascade will delete items)
    query = "DELETE FROM property_lists WHERE id = %s"
    execute_query(query, (list_id,))

    return {"message": "Property list deleted successfully"}

@router.post("/property-lists/add-property/")
async def add_property_to_list(
    data: AddPropertyToList,
    current_user: dict = Depends(get_current_user)
):
    """Add a property to a list"""
    user_id = int(current_user["sub"])

    # Verify list ownership or shared
    check_query = """
        SELECT user_id, is_shared FROM property_lists WHERE id = %s
    """
    result = fetch_query(check_query, (data.list_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Property list not found")

    if result[0]["user_id"] != user_id and not result[0]["is_shared"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this list")

    # Check if property exists
    prop_check = "SELECT id FROM locations WHERE id = %s"
    prop_result = fetch_query(prop_check, (data.property_id,))

    if not prop_result:
        raise HTTPException(status_code=404, detail="Property not found")

    # Add to list (ignore if already exists)
    query = """
        INSERT IGNORE INTO property_list_items (list_id, property_id)
        VALUES (%s, %s)
    """

    execute_query(query, (data.list_id, data.property_id))

    return {"message": "Property added to list"}

@router.delete("/property-lists/{list_id}/properties/{property_id}")
async def remove_property_from_list(
    list_id: int,
    property_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a property from a list"""
    user_id = int(current_user["sub"])

    # Verify list ownership or shared
    check_query = """
        SELECT user_id, is_shared FROM property_lists WHERE id = %s
    """
    result = fetch_query(check_query, (list_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Property list not found")

    if result[0]["user_id"] != user_id and not result[0]["is_shared"]:
        raise HTTPException(status_code=403, detail="Not authorized to modify this list")

    # Remove from list
    query = "DELETE FROM property_list_items WHERE list_id = %s AND property_id = %s"
    execute_query(query, (list_id, property_id))

    return {"message": "Property removed from list"}
