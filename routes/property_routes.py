# Handles add/update/delete/fetch property routes
from fastapi import APIRouter
router = APIRouter()
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import insert_location, fetch_query, execute_query

router = APIRouter()

class PropertyData(BaseModel):
    name: str
    address: str
    sqft: int
    area_manager: str
    plow: bool
    salt: bool

class PropertyUpdate(PropertyData):
    id: int

@router.post("/add-property/")
def add_property(property_data: PropertyData):
    success = insert_location(
        property_data.name,
        property_data.address,
        property_data.sqft,
        property_data.area_manager,
        property_data.plow,
        property_data.salt
    )
    if success:
        return {"message": "Property added successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add property")

@router.get("/properties/")
def get_properties():
    properties = fetch_query("SELECT * FROM locations")
    if properties:
        return properties
    else:
        raise HTTPException(status_code=404, detail="No properties found")

@router.put("/update-property/")
def update_property(property_data: PropertyUpdate):
    query = """
        UPDATE locations 
        SET name = %s, address = %s, sqft = %s, area_manager = %s, plow = %s, salt = %s
        WHERE id = %s
    """
    params = (
        property_data.name,
        property_data.address,
        property_data.sqft,
        property_data.area_manager,
        property_data.plow,
        property_data.salt,
        property_data.id
    )
    success = execute_query(query, params)
    if success:
        return {"message": "Property updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update property")

@router.delete("/delete-property/{property_id}")
def delete_property(property_id: int):
    query = "DELETE FROM locations WHERE id = %s"
    success = execute_query(query, (property_id,))
    if success:
        return {"message": "Property deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete property")
