from fastapi import APIRouter, HTTPException, Form
from db import fetch_query, execute_query

router = APIRouter()

# --- Winter Products ---
@router.get("/winter-products/")
def get_winter_products():
    return fetch_query("SELECT * FROM winter_products")

@router.post("/winter-products/")
def add_winter_product(name: str = Form(...), unit: str = Form(...)):
    query = "INSERT INTO winter_products (name, unit) VALUES (%s, %s)"
    execute_query(query, (name, unit))
    return {"message": "Winter product added successfully!"}

@router.put("/winter-products/{product_id}")
def update_winter_product(product_id: int, name: str = Form(...), unit: str = Form(...)):
    query = "UPDATE winter_products SET name = %s, unit = %s WHERE id = %s"
    execute_query(query, (name, unit, product_id))
    return {"message": "Winter product updated successfully!"}

@router.delete("/winter-products/{product_id}")
def delete_winter_product(product_id: int):
    query = "DELETE FROM winter_products WHERE id = %s"
    execute_query(query, (product_id,))
    return {"message": "Winter product deleted successfully!"}

# --- Landscape Products ---
@router.get("/landscape-products/")
def get_landscape_products():
    return fetch_query("SELECT * FROM landscape_products")

@router.post("/landscape-products/")
def add_landscape_product(name: str = Form(...), unit: str = Form(...)):
    query = "INSERT INTO landscape_products (name, unit) VALUES (%s, %s)"
    execute_query(query, (name, unit))
    return {"message": "Landscape product added successfully!"}

@router.put("/landscape-products/{product_id}")
def update_landscape_product(product_id: int, name: str = Form(...), unit: str = Form(...)):
    query = "UPDATE landscape_products SET name = %s, unit = %s WHERE id = %s"
    execute_query(query, (name, unit, product_id))
    return {"message": "Landscape product updated successfully!"}

@router.delete("/landscape-products/{product_id}")
def delete_landscape_product(product_id: int):
    query = "DELETE FROM landscape_products WHERE id = %s"
    execute_query(query, (product_id,))
    return {"message": "Landscape product deleted successfully!"}
