from fastapi import APIRouter, Body
from db import fetch_query
from pydantic import BaseModel
from typing import Optional
from datetime import date

router = APIRouter()

class ReportFilters(BaseModel):
    """Filters for generating reports"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    property_id: Optional[int] = None
    user_id: Optional[int] = None

@router.post("/report/by-product/")
def report_by_product(filters: ReportFilters):
    start = filters.start_date
    end = filters.end_date
    property_id = filters.property_id
    user_id = filters.user_id

    where_clauses = []
    params = []

    if start and end:
        where_clauses.append("(gs.service_date BETWEEN %s AND %s OR wl.time_in BETWEEN %s AND %s)")
        params += [start, end, start, end]

    if property_id:
        where_clauses.append("(gs.property_id = %s OR wl.property_id = %s)")
        params += [property_id, property_id]

    if user_id:
        where_clauses.append("(gs.subcontractor_id = %s OR wl.subcontractor_name = (SELECT name FROM users WHERE id = %s))")
        params += [user_id, user_id]

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    query = f"""
        SELECT product_name, SUM(quantity) AS total_used FROM (
            SELECT lp.name AS product_name, gs.product_quantity AS quantity
            FROM green_services gs
            JOIN landscape_products lp ON gs.product_used = lp.id
            {where_sql}
            UNION ALL
            SELECT 'Bulk Salt', wl.bulk_salt_qty FROM winter_ops_logs wl {where_sql}
            UNION ALL
            SELECT 'Bag Salt', wl.bag_salt_qty FROM winter_ops_logs wl {where_sql}
            UNION ALL
            SELECT 'Calcium Chloride', wl.calcium_chloride_qty FROM winter_ops_logs wl {where_sql}
        ) AS combined
        GROUP BY product_name
        ORDER BY total_used DESC;
    """
    return fetch_query(query, params)

@router.post("/report/by-property/")
def report_by_property(filters: ReportFilters):
    start = filters.start_date
    end = filters.end_date
    property_id = filters.property_id
    user_id = filters.user_id

    conditions = []
    params = []

    if start and end:
        conditions.append("(w.time_in BETWEEN %s AND %s OR g.time_in BETWEEN %s AND %s)")
        params += [start, end, start, end]
    if property_id:
        conditions.append("l.id = %s")
        params.append(property_id)
    if user_id:
        conditions.append("(w.subcontractor_name = (SELECT name FROM users WHERE id = %s) OR g.subcontractor_name = (SELECT name FROM users WHERE id = %s))")
        params += [user_id, user_id]

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            l.name AS property,
            COUNT(DISTINCT w.id) AS winter_logs,
            COUNT(DISTINCT g.id) AS green_logs,
            SUM(EXTRACT(EPOCH FROM (w.time_out - w.time_in)) / 3600) AS winter_hours,
            SUM(EXTRACT(EPOCH FROM (g.time_out - g.time_in)) / 3600) AS green_hours,
            SUM(w.bulk_salt_qty) AS bulk_salt,
            SUM(w.bag_salt_qty) AS bag_salt,
            SUM(w.calcium_chloride_qty) AS calcium_chloride,
            SUM(g.quantity_used) AS green_products_used
        FROM locations l
        LEFT JOIN winter_ops_logs w ON w.property_id = l.id
        LEFT JOIN green_services_logs g ON g.property_id = l.id
        {where_clause}
        GROUP BY l.name
        ORDER BY l.name;
    """
    return fetch_query(query, params)

@router.post("/report/by-user/")
def report_by_user(filters: ReportFilters):
    start = filters.start_date
    end = filters.end_date
    property_id = filters.property_id
    user_id = filters.user_id

    conditions = []
    params = []

    if start and end:
        conditions.append("(w.time_in BETWEEN %s AND %s OR g.time_in BETWEEN %s AND %s)")
        params += [start, end, start, end]
    if property_id:
        conditions.append("(w.property_id = %s OR g.property_id = %s)")
        params += [property_id, property_id]
    if user_id:
        conditions.append("(w.subcontractor_name = (SELECT name FROM users WHERE id = %s) OR g.subcontractor_name = (SELECT name FROM users WHERE id = %s))")
        params += [user_id, user_id]

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            COALESCE(w.subcontractor_name, g.subcontractor_name) AS subcontractor,
            COUNT(DISTINCT w.id) AS winter_logs,
            COUNT(DISTINCT g.id) AS green_logs,
            SUM(EXTRACT(EPOCH FROM (w.time_out - w.time_in)) / 3600) AS winter_hours,
            SUM(EXTRACT(EPOCH FROM (g.time_out - g.time_in)) / 3600) AS green_hours,
            SUM(w.bulk_salt_qty) AS bulk_salt,
            SUM(w.bag_salt_qty) AS bag_salt,
            SUM(w.calcium_chloride_qty) AS calcium_chloride,
            SUM(g.quantity_used) AS green_products_used
        FROM users u
        LEFT JOIN winter_ops_logs w ON w.subcontractor_name = u.name
        LEFT JOIN green_services_logs g ON g.subcontractor_name = u.name
        {where_clause}
        GROUP BY subcontractor
        ORDER BY subcontractor;
    """
    return fetch_query(query, params)
