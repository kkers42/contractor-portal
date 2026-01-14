# Handles add/update/delete/fetch property routes
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from db import fetch_query, execute_query
from auth import get_current_user
from utils.logger import get_logger

logger = get_logger(__name__)
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
    trigger_type: str | None = "two_inch"
    trigger_amount: float | None = 2.0
    contract_tier: str | None = "Standard"
    open_by_time: str | None = None
    billing_type: str | None = "hourly"
    plow_rate: float | None = None
    salt_rate: float | None = None
    sidewalk_deice_rate: float | None = None
    sidewalk_snow_rate: float | None = None

class PropertyUpdate(PropertyData):
    id: int

@router.post("/add-property/")
def add_property(property_data: PropertyData):
    # Check if property with this address already exists
    check_query = "SELECT id, name FROM locations WHERE address = %s"
    existing = fetch_query(check_query, (property_data.address,))

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A property already exists at this address: {existing[0]['name']}"
        )

    query = """
        INSERT INTO locations (name, address, sqft, area_manager, plow, salt, trigger_type, trigger_amount, contract_tier, open_by_time, billing_type, plow_rate, salt_rate, sidewalk_deice_rate, sidewalk_snow_rate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        property_data.name,
        property_data.address,
        property_data.sqft,
        property_data.area_manager,
        property_data.plow,
        property_data.salt,
        property_data.trigger_type,
        property_data.trigger_amount,
        property_data.contract_tier,
        property_data.open_by_time,
        property_data.billing_type,
        property_data.plow_rate,
        property_data.salt_rate,
        property_data.sidewalk_deice_rate,
        property_data.sidewalk_snow_rate
    )
    try:
        execute_query(query, params)
        return {"message": "Property added successfully"}
    except Exception as e:
        logger.error(f"Failed to add property: {str(e)}", exc_info=True)
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
        SET name = %s, address = %s, sqft = %s, area_manager = %s, plow = %s, salt = %s,
            trigger_type = %s, trigger_amount = %s, contract_tier = %s, open_by_time = %s,
            billing_type = %s, plow_rate = %s, salt_rate = %s, sidewalk_deice_rate = %s, sidewalk_snow_rate = %s
        WHERE id = %s
    """
    params = (
        property_data.name,
        property_data.address,
        property_data.sqft,
        property_data.area_manager,
        property_data.plow,
        property_data.salt,
        property_data.trigger_type,
        property_data.trigger_amount,
        property_data.contract_tier,
        property_data.open_by_time,
        property_data.billing_type,
        property_data.plow_rate,
        property_data.salt_rate,
        property_data.sidewalk_deice_rate,
        property_data.sidewalk_snow_rate,
        property_data.id
    )
    try:
        execute_query(query, params)
        return {"message": "Property updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update property: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update property: {str(e)}")

@router.delete("/delete-property/{property_id}")
def delete_property(property_id: int):
    query = "DELETE FROM locations WHERE id = %s"
    try:
        execute_query(query, (property_id,))
        return {"message": "Property deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete property: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete property: {str(e)}")

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
        skipped_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Parse PLOW/SALT field
                plow_salt = str(row['PLOW/SALT']).strip().lower()
                plow = 'yes' in plow_salt.split('/')[0] if '/' in plow_salt else False
                salt = 'yes' in plow_salt.split('/')[1] if '/' in plow_salt and len(plow_salt.split('/')) > 1 else False

                # Convert sqft to integer
                sqft = int(row['Lot Sq Ft'])

                address = str(row['Address']).strip()

                # Check if property with this address already exists
                check_query = "SELECT id FROM locations WHERE address = %s"
                existing = fetch_query(check_query, (address,))

                if existing:
                    # Property already exists, skip it
                    skipped_count += 1
                    continue

                # Insert property
                query = """
                    INSERT INTO locations (name, address, sqft, area_manager, plow, salt)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    str(row['Property Name']).strip(),
                    address,
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
        if skipped_count > 0:
            message += f", skipped {skipped_count} duplicates"
        if errors:
            message += f". {len(errors)} errors occurred."
            return {
                "message": message,
                "count": imported_count,
                "skipped": skipped_count,
                "errors": errors[:10]  # Limit to first 10 errors
            }

        return {
            "message": message,
            "count": imported_count,
            "skipped": skipped_count
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

# ===== PROPERTY-CONTRACTOR ASSIGNMENT ROUTES (KANBAN BOARD) =====

@router.get("/properties/board/")
def get_property_board(current_user: dict = Depends(get_current_user)):
    """
    Get all properties with their assigned contractors for Kanban board view.
    Returns properties with nested contractor lists.
    """
    try:
        # Get all properties
        properties_query = """
            SELECT id, name, address, sqft, area_manager, plow, salt,
                   trigger_type, trigger_amount, contract_tier, open_by_time
            FROM locations
            ORDER BY name
        """
        properties = fetch_query(properties_query)

        if not properties:
            return []

        # Get all contractor assignments grouped by property
        assignments_query = """
            SELECT
                pc.property_id,
                pc.contractor_id,
                pc.is_primary,
                pc.assigned_date,
                pc.acceptance_status,
                pc.accepted_at,
                pc.declined_at,
                u.name as contractor_name,
                u.email as contractor_email,
                u.role as contractor_role,
                u.phone as contractor_phone
            FROM property_contractors pc
            JOIN users u ON pc.contractor_id = u.id
            WHERE u.status = 'active'
            ORDER BY pc.is_primary DESC, u.name
        """
        assignments = fetch_query(assignments_query)

        # Group contractors by property
        contractors_by_property = {}
        if assignments:
            for assignment in assignments:
                prop_id = assignment['property_id']
                if prop_id not in contractors_by_property:
                    contractors_by_property[prop_id] = []
                contractors_by_property[prop_id].append({
                    'contractor_id': assignment['contractor_id'],
                    'name': assignment['contractor_name'],
                    'email': assignment['contractor_email'],
                    'role': assignment['contractor_role'],
                    'phone': assignment['contractor_phone'],
                    'is_primary': assignment['is_primary'],
                    'assigned_date': assignment['assigned_date'].isoformat() if assignment['assigned_date'] else None,
                    'acceptance_status': assignment['acceptance_status'],
                    'accepted_at': assignment['accepted_at'].isoformat() if assignment['accepted_at'] else None,
                    'declined_at': assignment['declined_at'].isoformat() if assignment['declined_at'] else None
                })

        # Attach contractors to each property
        for prop in properties:
            prop['contractors'] = contractors_by_property.get(prop['id'], [])

        return properties
    except Exception as e:
        logger.error(f"Failed to fetch property board: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch property board: {str(e)}")

@router.get("/properties/{property_id}/contractors/")
def get_property_contractors(property_id: int, current_user: dict = Depends(get_current_user)):
    """Get all contractors assigned to a specific property"""
    query = """
        SELECT
            pc.id as assignment_id,
            pc.contractor_id,
            pc.is_primary,
            pc.assigned_date,
            u.name,
            u.email,
            u.role,
            u.phone
        FROM property_contractors pc
        JOIN users u ON pc.contractor_id = u.id
        WHERE pc.property_id = %s AND u.status = 'active'
        ORDER BY pc.is_primary DESC, u.name
    """
    try:
        contractors = fetch_query(query, (property_id,))
        return contractors if contractors else []
    except Exception as e:
        logger.error(f"Failed to fetch contractors for property: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch contractors: {str(e)}")

class PropertyContractorAssignment(BaseModel):
    contractor_id: int
    is_primary: bool = False

@router.post("/properties/{property_id}/contractors/")
def assign_contractor_to_property(
    property_id: int,
    assignment: PropertyContractorAssignment,
    current_user: dict = Depends(get_current_user)
):
    """Assign a contractor to a property"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admins and Managers can assign contractors")

    # Check if property exists
    prop_check = fetch_query("SELECT id FROM locations WHERE id = %s", (property_id,))
    if not prop_check:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check if contractor exists and is active
    contractor_check = fetch_query(
        "SELECT id, role FROM users WHERE id = %s AND status = 'active'",
        (assignment.contractor_id,)
    )
    if not contractor_check:
        raise HTTPException(status_code=404, detail="Contractor not found or inactive")

    # Allow any active user to be assigned (in a snowstorm, anyone can plow)

    # Check if assignment already exists
    existing = fetch_query(
        "SELECT id FROM property_contractors WHERE property_id = %s AND contractor_id = %s",
        (property_id, assignment.contractor_id)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Contractor is already assigned to this property")

    # Insert assignment
    query = """
        INSERT INTO property_contractors (property_id, contractor_id, is_primary)
        VALUES (%s, %s, %s)
    """
    try:
        execute_query(query, (property_id, assignment.contractor_id, assignment.is_primary))
        return {"message": "Contractor assigned successfully"}
    except Exception as e:
        logger.error(f"Failed to assign contractor: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to assign contractor: {str(e)}")

@router.delete("/properties/{property_id}/contractors/{contractor_id}")
def remove_contractor_from_property(
    property_id: int,
    contractor_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a contractor assignment from a property"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admins and Managers can remove contractors")

    query = "DELETE FROM property_contractors WHERE property_id = %s AND contractor_id = %s"
    try:
        execute_query(query, (property_id, contractor_id))
        return {"message": "Contractor removed from property"}
    except Exception as e:
        logger.error(f"Failed to remove contractor: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to remove contractor: {str(e)}")

@router.put("/properties/{property_id}/contractors/{contractor_id}/primary")
def set_primary_contractor(
    property_id: int,
    contractor_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Set a contractor as the primary contractor for a property"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admins and Managers can set primary contractors")

    try:
        # First, unset all primary contractors for this property
        execute_query(
            "UPDATE property_contractors SET is_primary = FALSE WHERE property_id = %s",
            (property_id,)
        )

        # Then set this contractor as primary
        execute_query(
            "UPDATE property_contractors SET is_primary = TRUE WHERE property_id = %s AND contractor_id = %s",
            (property_id, contractor_id)
        )

        return {"message": "Primary contractor updated"}
    except Exception as e:
        logger.error(f"Failed to set primary contractor: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set primary contractor: {str(e)}")

@router.get("/my-properties/")
def get_my_assigned_properties(current_user: dict = Depends(get_current_user)):
    """Get all properties assigned to the current user"""
    user_id = int(current_user["sub"])

    query = """
        SELECT
            l.id, l.name, l.address, l.sqft, l.area_manager, l.plow, l.salt,
            pc.is_primary,
            (SELECT COUNT(*) FROM winter_ops_logs w
             WHERE w.property_id = l.id
             AND w.user_id = %s
             AND w.time_out IS NULL
             AND DATE(w.time_in) = CURDATE()) as has_active_ticket
        FROM locations l
        INNER JOIN property_contractors pc ON l.id = pc.property_id
        WHERE pc.contractor_id = %s
        ORDER BY pc.is_primary DESC, l.name ASC
    """

    try:
        properties = fetch_query(query, (user_id, user_id))
        return properties if properties else []
    except Exception as e:
        logger.error(f"Failed to get user's properties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get properties: {str(e)}")
