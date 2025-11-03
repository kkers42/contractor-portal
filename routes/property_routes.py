# Handles add/update/delete/fetch property routes
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from db import fetch_query, execute_query
from auth import get_current_user
import pandas as pd
from io import BytesIO

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
    query = """
        INSERT INTO locations (name, address, sqft, area_manager, plow, salt)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        property_data.name,
        property_data.address,
        property_data.sqft,
        property_data.area_manager,
        property_data.plow,
        property_data.salt
    )
    try:
        execute_query(query, params)
        return {"message": "Property added successfully"}
    except Exception as e:
        print(f"[ERROR] Failed to add property: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add property: {str(e)}")

@router.get("/properties/")
def get_properties():
    properties = fetch_query("SELECT * FROM locations")
    # Return empty array instead of 404 if no properties exist
    return properties if properties else []

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

@router.post("/bulk-import-properties/")
async def bulk_import_properties(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Bulk import properties from Excel file.
    Expected Excel structure (from 'locations' sheet):
    - Property Name
    - Address
    - trigger (ignored)
    - area manager
    - Lot Sq Ft
    - PLOW/SALT (format: "Yes/Yes", "Yes/No", etc.)
    """
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admins and Managers can import properties")

    # Validate file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), sheet_name='locations')

        # Clean up column names (remove leading/trailing spaces)
        df.columns = df.columns.str.strip()

        # Validate required columns
        required_columns = ['Property Name', 'Address', 'area manager', 'Lot Sq Ft', 'PLOW/SALT']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        # Filter out rows where Property Name is null (like index rows)
        df = df[df['Property Name'].notna()]

        imported_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Parse PLOW/SALT field
                plow_salt = str(row['PLOW/SALT']).strip().lower()
                plow = 'yes' in plow_salt.split('/')[0] if '/' in plow_salt else False
                salt = 'yes' in plow_salt.split('/')[1] if '/' in plow_salt and len(plow_salt.split('/')) > 1 else False

                # Convert sqft to integer
                sqft = int(row['Lot Sq Ft'])

                # Insert property
                query = """
                    INSERT INTO locations (name, address, sqft, area_manager, plow, salt)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    str(row['Property Name']).strip(),
                    str(row['Address']).strip(),
                    sqft,
                    str(row['area manager']).strip(),
                    plow,
                    salt
                )
                execute_query(query, params)
                imported_count += 1

            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")

        # Prepare response
        message = f"Successfully imported {imported_count} properties"
        if errors:
            message += f". {len(errors)} errors occurred."
            return {
                "message": message,
                "count": imported_count,
                "errors": errors[:10]  # Limit to first 10 errors
            }

        return {
            "message": message,
            "count": imported_count
        }

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Excel file is empty")
    except ValueError as e:
        if "Worksheet named 'locations' not found" in str(e):
            raise HTTPException(
                status_code=400,
                detail="Excel file must contain a sheet named 'locations'"
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import properties: {str(e)}")
