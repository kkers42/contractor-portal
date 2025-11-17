from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import execute_query, fetch_query
from auth import get_current_user

router = APIRouter()

class EquipmentRate(BaseModel):
    equipment_name: str
    hourly_rate: float
    description: str = None

@router.get("/equipment-rates/")
def get_equipment_rates(current_user: dict = Depends(get_current_user)):
    """Get all equipment with their hourly rates (pricing hidden for Subcontractors)"""
    query = "SELECT id, equipment_name, hourly_rate, description FROM equipment_rates ORDER BY equipment_name"
    rates = fetch_query(query)
    
    # Hide pricing information for Subcontractors and Users
    if rates and current_user["role"] in ["Subcontractor", "User"]:
        for rate in rates:
            rate["hourly_rate"] = None
    
    return rates if rates else []

@router.post("/equipment-rates/")
def add_equipment_rate(equipment: EquipmentRate, current_user: dict = Depends(get_current_user)):
    """Add new equipment with hourly rate (Manager/Admin only)"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Managers and Admins only!")

    try:
        query = "INSERT INTO equipment_rates (equipment_name, hourly_rate, description) VALUES (%s, %s, %s)"
        execute_query(query, (equipment.equipment_name, equipment.hourly_rate, equipment.description))
        return {"message": "Equipment rate added successfully!"}
    except Exception as e:
        print(f"[ERROR] Failed to add equipment rate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add equipment rate: {str(e)}")

@router.put("/equipment-rates/{equipment_id}")
def update_equipment_rate(equipment_id: int, equipment: EquipmentRate, current_user: dict = Depends(get_current_user)):
    """Update equipment hourly rate (Manager/Admin only)"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Managers and Admins only!")

    try:
        query = "UPDATE equipment_rates SET equipment_name = %s, hourly_rate = %s, description = %s WHERE id = %s"
        execute_query(query, (equipment.equipment_name, equipment.hourly_rate, equipment.description, equipment_id))
        return {"message": "Equipment rate updated successfully!"}
    except Exception as e:
        print(f"[ERROR] Failed to update equipment rate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update equipment rate: {str(e)}")

@router.delete("/equipment-rates/{equipment_id}")
def delete_equipment_rate(equipment_id: int, current_user: dict = Depends(get_current_user)):
    """Delete equipment rate (Admin only)"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")

    try:
        execute_query("DELETE FROM equipment_rates WHERE id = %s", (equipment_id,))
        return {"message": "Equipment rate deleted successfully!"}
    except Exception as e:
        print(f"[ERROR] Failed to delete equipment rate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete equipment rate: {str(e)}")

@router.get("/equipment-usage-report/")
def get_equipment_usage_report(
    start_date: str = None,
    end_date: str = None,
    contractor_id: int = None,
    property_id: int = None,
    equipment_name: str = None
):
    """Get equipment usage report with hours and costs"""
    where_parts = []
    params = []

    if start_date and end_date:
        where_parts.append("w.time_in BETWEEN %s AND %s")
        params += [start_date, end_date]

    if contractor_id:
        where_parts.append("w.contractor_id = %s")
        params.append(contractor_id)

    if property_id:
        where_parts.append("w.property_id = %s")
        params.append(property_id)

    if equipment_name:
        where_parts.append("w.equipment = %s")
        params.append(equipment_name)

    where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

    query = f"""
        SELECT
            w.equipment,
            e.hourly_rate,
            COUNT(w.id) as total_uses,
            SUM(TIMESTAMPDIFF(SECOND, w.time_in, w.time_out) / 3600) as total_hours,
            SUM(TIMESTAMPDIFF(SECOND, w.time_in, w.time_out) / 3600 * e.hourly_rate) as total_cost
        FROM winter_ops_logs w
        LEFT JOIN equipment_rates e ON w.equipment = e.equipment_name
        {where_clause}
        GROUP BY w.equipment, e.hourly_rate
        ORDER BY total_hours DESC
    """

    results = fetch_query(query, params if params else None)
    return results if results else []
