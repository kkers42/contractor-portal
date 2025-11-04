from fastapi import APIRouter
from pydantic import BaseModel
from db import execute_query, fetch_query

router = APIRouter()

# --- Winter Ops Model ---
class WinterOpsLog(BaseModel):
    property_id: int
    subcontractor_name: str
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
        (property_id, subcontractor_name, equipment, time_in, time_out, bulk_salt_qty, bag_salt_qty, calcium_chloride_qty, customer_provided, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        log.property_id,
        log.subcontractor_name,
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
            w.id, l.name AS property_name, w.subcontractor_name, w.equipment,
            w.time_in, w.time_out,
            w.bulk_salt_qty, w.bag_salt_qty, w.calcium_chloride_qty, w.customer_provided, w.notes
        FROM winter_ops_logs w
        JOIN locations l ON w.property_id = l.id
        ORDER BY w.time_in DESC
    """
    return fetch_query(query)

# --- Green Ops Model ---
class GreenOpsLog(BaseModel):
    property_id: int
    subcontractor_name: str
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
        (property_id, subcontractor_name, time_in, time_out, service_type, products_used, quantity_used, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        log.property_id,
        log.subcontractor_name,
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
            g.id, l.name AS property_name, g.subcontractor_name,
            g.time_in, g.time_out, g.service_type, g.products_used,
            g.quantity_used, g.notes
        FROM green_services_logs g
        JOIN locations l ON g.property_id = l.id
        ORDER BY g.time_in DESC
    """
    return fetch_query(query)
