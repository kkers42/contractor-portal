from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import execute_query, fetch_query
from auth import get_current_user

router = APIRouter()

# --- Winter Ops Model ---
class WinterOpsLog(BaseModel):
    property_id: int
    contractor_id: int
    contractor_name: str
    worker_name: str  # The subcontractor/worker (Last, First)
    equipment: str
    time_in: str
    time_out: str
    bulk_salt_qty: float
    bag_salt_qty: float
    calcium_chloride_qty: float
    customer_provided: bool
    notes: str

@router.post("/submit-winter-log/")
def submit_winter_log(log: WinterOpsLog):
    query = """
        INSERT INTO winter_ops_logs
        (property_id, contractor_id, contractor_name, worker_name, equipment, time_in, time_out, bulk_salt_qty, bag_salt_qty, calcium_chloride_qty, customer_provided, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        log.notes
    )
    execute_query(query, values)
    return {"message": "Winter Ops Log submitted successfully!"}

@router.get("/winter-logs/")
def get_winter_logs():
    query = """
        SELECT
            w.id, l.name AS property_name, w.property_id,
            w.contractor_id, w.contractor_name, w.worker_name, w.equipment,
            w.time_in, w.time_out,
            w.bulk_salt_qty, w.bag_salt_qty, w.calcium_chloride_qty, w.customer_provided, w.notes
        FROM winter_ops_logs w
        JOIN locations l ON w.property_id = l.id
        ORDER BY w.time_in DESC
    """
    return fetch_query(query)

@router.put("/winter-logs/{log_id}")
def update_winter_log(log_id: int, log: WinterOpsLog, current_user: dict = Depends(get_current_user)):
    """Update winter ops log (Admin/Manager only)"""
    if current_user["role"] not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Admins and Managers only!")

    try:
        query = """
            UPDATE winter_ops_logs SET
                property_id = %s, contractor_id = %s, contractor_name = %s, worker_name = %s,
                equipment = %s, time_in = %s, time_out = %s,
                bulk_salt_qty = %s, bag_salt_qty = %s, calcium_chloride_qty = %s,
                customer_provided = %s, notes = %s
            WHERE id = %s
        """
        values = (
            log.property_id, log.contractor_id, log.contractor_name, log.worker_name,
            log.equipment, log.time_in, log.time_out,
            log.bulk_salt_qty, log.bag_salt_qty, log.calcium_chloride_qty,
            log.customer_provided, log.notes, log_id
        )
        execute_query(query, values)
        return {"message": "Winter log updated successfully!"}
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
