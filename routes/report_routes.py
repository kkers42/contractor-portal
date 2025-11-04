from fastapi import APIRouter, Body, Response, HTTPException
from fastapi.responses import StreamingResponse
from db import fetch_query
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import pandas as pd
from io import BytesIO

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
            SUM(TIMESTAMPDIFF(SECOND, w.time_in, w.time_out) / 3600) AS winter_hours,
            SUM(TIMESTAMPDIFF(SECOND, g.time_in, g.time_out) / 3600) AS green_hours,
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
            SUM(TIMESTAMPDIFF(SECOND, w.time_in, w.time_out) / 3600) AS winter_hours,
            SUM(TIMESTAMPDIFF(SECOND, g.time_in, g.time_out) / 3600) AS green_hours,
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

@router.post("/export/contractor-timesheets/")
def export_contractor_timesheets(filters: ReportFilters):
    """
    Export contractor timesheets in Excel format
    Similar to the format: Date/Contractor name with timesheet details
    """
    start = filters.start_date
    end = filters.end_date

    # Fetch winter logs
    where_parts = []
    params = []

    if start and end:
        where_parts.append("time_in BETWEEN %s AND %s")
        params += [start, end]

    where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

    query = f"""
        SELECT
            w.id,
            w.subcontractor_name,
            DATE(w.time_in) as work_date,
            w.time_in,
            w.time_out,
            TIMESTAMPDIFF(MINUTE, w.time_in, w.time_out) as total_minutes,
            TIMESTAMPDIFF(SECOND, w.time_in, w.time_out) / 3600 as hours,
            l.name as site,
            w.bulk_salt_qty,
            w.bag_salt_qty,
            w.calcium_chloride_qty,
            w.notes
        FROM winter_ops_logs w
        JOIN locations l ON w.property_id = l.id
        {where_clause}
        ORDER BY w.subcontractor_name, w.time_in
    """

    logs = fetch_query(query, params if params else None)

    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for the specified filters")

    # Create Excel workbook with pandas
    output = BytesIO()

    # Group by contractor and date
    df = pd.DataFrame(logs)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for contractor in df['subcontractor_name'].unique():
            contractor_logs = df[df['subcontractor_name'] == contractor]

            for work_date in contractor_logs['work_date'].unique():
                date_logs = contractor_logs[contractor_logs['work_date'] == work_date]

                # Calculate totals
                total_hours = date_logs['hours'].sum()
                total_minutes = date_logs['total_minutes'].sum()

                # Format sheet name (date_contractor)
                sheet_name = f"{work_date.strftime('%m%d%Y')}_{contractor}"[:31]  # Excel limit

                # Create formatted dataframe
                export_data = []
                export_data.append(['Truck Rate $135/hr', '', '', '', f'Total Time {total_hours:.2f}'])
                export_data.append(['Start Time', 'End Time', 'Total Min', 'HRS', 'Site', 'Qty Salt (yrd)'])

                for _, row in date_logs.iterrows():
                    start_time = pd.to_datetime(row['time_in']).strftime('%H%M')
                    end_time = pd.to_datetime(row['time_out']).strftime('%H%M')
                    export_data.append([
                        start_time,
                        end_time,
                        int(row['total_minutes']),
                        round(row['hours'], 2),
                        row['site'],
                        row['bulk_salt_qty'] if row['bulk_salt_qty'] else ''
                    ])

                # Create DataFrame and write to sheet
                sheet_df = pd.DataFrame(export_data)
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

    output.seek(0)

    # Generate filename
    filename = f"contractor_timesheets_{start}_{end}.xlsx" if start and end else "contractor_timesheets.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/export/property-logs/")
def export_property_logs(filters: ReportFilters):
    """
    Export property-based logs in Excel format
    One sheet per property with all contractor visits
    """
    start = filters.start_date
    end = filters.end_date
    property_id = filters.property_id

    where_parts = []
    params = []

    if start and end:
        where_parts.append("time_in BETWEEN %s AND %s")
        params += [start, end]

    if property_id:
        where_parts.append("w.property_id = %s")
        params.append(property_id)

    where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""

    query = f"""
        SELECT
            l.name as property_name,
            w.subcontractor_name,
            DATE(w.time_in) as work_date,
            w.time_in,
            w.time_out,
            TIMESTAMPDIFF(MINUTE, w.time_in, w.time_out) as total_minutes,
            TIMESTAMPDIFF(SECOND, w.time_in, w.time_out) / 3600 as hours,
            w.bulk_salt_qty,
            w.bag_salt_qty,
            w.calcium_chloride_qty,
            w.notes
        FROM winter_ops_logs w
        JOIN locations l ON w.property_id = l.id
        {where_clause}
        ORDER BY l.name, w.time_in
    """

    logs = fetch_query(query, params if params else None)

    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for the specified filters")

    output = BytesIO()
    df = pd.DataFrame(logs)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for property_name in df['property_name'].unique():
            property_logs = df[df['property_name'] == property_name]

            # Calculate totals
            total_hours = property_logs['hours'].sum()
            total_salt = property_logs['bulk_salt_qty'].sum()

            # Format sheet name
            sheet_name = property_name[:31]  # Excel limit

            # Create formatted dataframe
            export_data = []
            export_data.append([f'Property: {property_name}', '', '', '', f'Total Hours: {total_hours:.2f}', f'Total Salt: {total_salt:.2f} yrd'])
            export_data.append(['Date', 'Contractor', 'Start Time', 'End Time', 'Hours', 'Bulk Salt (yrd)', 'Bag Salt', 'Calcium', 'Notes'])

            for _, row in property_logs.iterrows():
                work_date = pd.to_datetime(row['work_date']).strftime('%m/%d/%Y')
                start_time = pd.to_datetime(row['time_in']).strftime('%H:%M')
                end_time = pd.to_datetime(row['time_out']).strftime('%H:%M')
                export_data.append([
                    work_date,
                    row['subcontractor_name'],
                    start_time,
                    end_time,
                    round(row['hours'], 2),
                    row['bulk_salt_qty'] if row['bulk_salt_qty'] else '',
                    row['bag_salt_qty'] if row['bag_salt_qty'] else '',
                    row['calcium_chloride_qty'] if row['calcium_chloride_qty'] else '',
                    row['notes'] if row['notes'] else ''
                ])

            sheet_df = pd.DataFrame(export_data)
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

    output.seek(0)

    filename = f"property_logs_{start}_{end}.xlsx" if start and end else "property_logs.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
