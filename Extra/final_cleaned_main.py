from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import insert_location
from db import fetch_query, insert_location, execute_query
from auth import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from auth import SECRET_KEY, ALGORITHM
from auth import hash_password, verify_password, create_access_token, get_current_user, SECRET_KEY, ALGORITHM
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import os


app = FastAPI()

# mount static folder
# app.mount("/", StaticFiles(directory="static", html=True), name="static")
# NEW
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


# Root URL
@app.get("/")
def serve_home():
	return FileResponse("static/Home.html")

print("🚀 FastAPI is launching!")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)
	allow_origins=["*"],  # Change "*" to a specific domain if needed
	allow_credentials=True,
	allow_methods=["*"],  # Allows all HTTP methods (GET, POST, OPTIONS, etc.)
	allow_headers=["*"],  # Allows all headers
)

class PropertyData(BaseModel):
	name: str
	address: str
	sqft: int
	area_manager: str
	plow: bool
	salt: bool

class PropertyUpdate(BaseModel):
	id: int
	name: str
	address: str
	sqft: int
	area_manager: str
	plow: bool
	salt: bool

@app.post("/add-property/")
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
	else:
		raise HTTPException(status_code=500, detail="Failed to add property")
		return {"message": "Property added successfully"}
	else:
		raise HTTPException(status_code=500, detail="Failed to add property")

@app.get("/properties/")
def get_properties():
	"""Fetch all properties from the database"""
	properties = fetch_query("SELECT * FROM locations")
	if properties:
		return properties
	else:
		raise HTTPException(status_code=404, detail="No properties found")

@app.put("/update-property/")
def update_property(property_data: PropertyUpdate):
	"""Update a property in the database"""
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

@app.delete("/delete-property/{property_id}")
def delete_property(property_id: int):
	print(f"🔍 Received DELETE request for property ID: {property_id}")

	query = "DELETE FROM locations WHERE id = %s"
	success = execute_query(query, (property_id,))

	if success:
		return {"message": "Property deleted successfully"}
	else:
		raise HTTPException(status_code=500, detail="Failed to delete property")

# --- Product Models ---
class Product(BaseModel):
	name: str
	unit: str
	description: str = None

class ProductUpdate(Product):
	id: int

# --- Product Endpoints ---
@app.get("/products/")
def get_products():
	query = "SELECT * FROM landscape_products"
	products = fetch_query(query)
	return products

@app.post("/add-product/")
def add_product(product: Product):
	query = "INSERT INTO landscape_products (name, unit, description) VALUES (%s, %s, %s)"
	params = (product.name, product.unit, product.description)
	success = execute_query(query, params)
	
	if success:
		return {"message": "Product added successfully"}
	raise HTTPException(status_code=500, detail="Failed to add product")

@app.put("/update-product/{product_id}")
def update_product(product_id: int, product: Product):
	query = """
		UPDATE landscape_products
		SET name = %s, unit = %s, description = %s
		WHERE id = %s
	"""
	params = (product.name, product.unit, product.description, product_id)
	success = execute_query(query, params)
	
	if success:
		return {"message": "Product updated successfully"}
	raise HTTPException(status_code=500, detail="Failed to update product")

@app.delete("/delete-product/{product_id}")
def delete_product(product_id: int):
	query = "DELETE FROM landscape_products WHERE id = %s"
	success = execute_query(query, (product_id,))
	
	if success:
		return {"message": "Product deleted successfully"}
	raise HTTPException(status_code=500, detail="Failed to delete product")

# --- Green Service Models ---
class GreenService(BaseModel):
	property_id: int
	subcontractor_id: int = None  # Optional, if tracking subs
	service_type: str
	product_used: int = None
	product_quantity: int = 0
	service_date: str
	time_in: str = None
	time_out: str = None
	notes: str = None

# --- Green Service Endpoints ---
@app.get("/green-services/")
def get_green_services():
	query = """
		SELECT gs.*, lp.name AS product_name
		FROM green_services gs
		LEFT JOIN landscape_products lp ON gs.product_used = lp.id
	"""
	services = fetch_query(query)
	return services

@app.post("/add-green-service/")
def add_green_service(service: GreenService):
	query = """
		INSERT INTO green_services 
		(property_id, subcontractor_id, service_type, product_used, product_quantity, service_date, time_in, time_out, notes)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
	"""
	params = (
		service.property_id,
		service.subcontractor_id,
		service.service_type,
		service.product_used,
		service.product_quantity,
		service.service_date,
		service.time_in,
		service.time_out,
		service.notes
	)
	success = execute_query(query, params)
	
	if success:
		return {"message": "Green service logged successfully"}
	raise HTTPException(status_code=500, detail="Failed to log green service")

from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
from db import insert_location  # reusing your existing insert function!

@app.post("/bulk-import-properties/")
async def bulk_import_properties(file: UploadFile = File(...)):
	if not file.filename.endswith('.xlsx'):
		raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

	try:
		df = pd.read_excel(file.file)
		required_columns = ['Property Name', 'Address']

		# Validate columns
		for col in required_columns:
			if col not in df.columns:
				raise HTTPException(status_code=400, detail=f"Missing column: {col}")

		# Process each row
		for _, row in df.iterrows():
			insert_location(
				row['Property Name'],
				row['Address'],
				row.get('Sq Ft', 0),           # default 0 if not present
				row.get('Area Manager', 'N/A'),
				True,  # default plow
				True   # default salt
			)

		return {"message": "Bulk import successful"}

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
		
from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
from db import insert_location  # Reusing existing insert_location
from db import execute_query  # For direct SQL if needed

		raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

	try:
		df = pd.read_excel(file.file)
		required_columns = ['Property Name', 'Address', 'Sq Ft', 'Area Manager', 'Plow', 'Salt', 'Notes']

		# Validate all required columns
		for col in required_columns:
			if col not in df.columns:
				raise HTTPException(status_code=400, detail=f"Missing column: {col}")

		# Process each row
		for _, row in df.iterrows():
			# Insert directly using execute_query to handle Notes (if insert_location doesn't support Notes yet)
			query = """
				INSERT INTO locations (name, address, sqft, area_manager, plow, salt, notes)
				VALUES (%s, %s, %s, %s, %s, %s, %s)
			"""
			values = (
				row['Property Name'],
				row['Address'],
				int(row['Sq Ft']) if not pd.isna(row['Sq Ft']) else 0,
				row['Area Manager'] or '',
				bool(row['Plow']),
				bool(row['Salt']),
				row['Notes'] or ''
			)
			execute_query(query, values)

		return {"message": "Bulk import successful"}

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from db import execute_query

class WinterOpsLog(BaseModel):
	property_id: int
	subcontractor_name: str
	time_in: str
	time_out: str
	bulk_salt_qty: float
	bag_salt_qty: float
	calcium_chloride_qty: float
	customer_provided: bool
	notes: str

@app.post("/submit-winter-log/")
def submit_winter_log(log: WinterOpsLog):
	query = """
		INSERT INTO winter_ops_logs
		(property_id, subcontractor_name, time_in, time_out, bulk_salt_qty, bag_salt_qty, calcium_chloride_qty, customer_provided, notes)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
	"""
	values = (
		log.property_id,
		log.subcontractor_name,
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


@app.get("/winter-logs/")
def get_winter_logs():
	query = """
		SELECT 
			w.id, l.name AS property_name, w.subcontractor_name,
			w.time_in, w.time_out,
			w.bulk_salt_qty, w.bag_salt_qty, w.calcium_chloride_qty, w.customer_provided, w.notes
		FROM winter_ops_logs w
		JOIN locations l ON w.property_id = l.id
		ORDER BY w.time_in DESC
	"""
	logs = fetch_query(query)
	return logs

class GreenOpsLog(BaseModel):
	property_id: int
	subcontractor_name: str
	time_in: str
	time_out: str
	service_type: str
	products_used: str
	quantity_used: float
	notes: str

@app.post("/submit-green-log/")
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

@app.get("/green-logs/")
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
	logs = fetch_query(query)
	return logs

class User(BaseModel):
	name: str
	phone: str
	email: str
	role: str  # Should be: Admin / Manager / Subcontractor
	password: str  # Optional (cleartext for now, hash later)

#protect endpoints by role
@app.get("/users/")
def get_users(current_user: dict = Depends(get_current_user)):
	if current_user["role"] != "Admin":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")
	query = "SELECT id, name, phone, email, role FROM users"
	return fetch_query(query)

@app.post("/add-user/")
def add_user(user: User):
	hashed_pw = hash_password(user.password)

	query = """
		INSERT INTO users (name, phone, email, role, password)
		VALUES (%s, %s, %s, %s, %s)
	"""
	values = (
		user.name,
		user.phone,
		user.email,
		user.role,
		hashed_pw
	)
	execute_query(query, values)
	return {"message": "User added successfully!"}



@app.put("/update-user/{user_id}")
def update_user(user_id: int, user: User, current_user: dict = Depends(get_current_user)):
	if current_user["role"] != "Admin":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")

	hashed_pw = hash_password(user.password)

	query = """
		UPDATE users
		SET name = %s, phone = %s, email = %s, role = %s, password = %s
		WHERE id = %s
	"""
	values = (
		user.name,
		user.phone,
		user.email,
		user.role,
		hashed_pw,
		user_id
	)
	execute_query(query, values)
	return {"message": "User updated successfully!"}


@app.delete("/delete-user/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
	if current_user["role"] != "Admin":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")

	query = "DELETE FROM users WHERE id = %s"
	execute_query(query, (user_id,))
	return {"message": "User deleted successfully!"}


@app.post("/api/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
	email = form_data.username
	password = form_data.password

	# Find user by email
	query = "SELECT * FROM users WHERE email = %s"
	user = fetch_query(query, (email,))
	
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	user = user[0]  # Because fetch_query returns a list of dicts

	if not verify_password(password, user['password']):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

	# Create JWT token with role included
	token_data = {
		"sub": user['email'],
		"role": user['role']
	}
	access_token = create_access_token(data=token_data)

	return {"access_token": access_token, "token_type": "bearer"}

from fastapi import Form
import smtplib
from email.mime.text import MIMEText

# Request User

@app.post("/request-user/")
def request_user(
	name: str = Form(...),
	phone: str = Form(...),
	email: str = Form(...),
	role: str = Form(...)
):
	admin_email = get_admin_email()

	# Insert signup request into DB
	query = """
		INSERT INTO signup_requests (name, phone, email, role)
		VALUES (%s, %s, %s, %s)
	"""
	values = (name, phone, email, role)
	execute_query(query, values)

	# Compose email content
	subject = "New User Signup Request"
	body = f"""
	A new user signup request was submitted.

	Name: {name}
	Phone: {phone}
	Email: {email}
	Role: {role}

	Please review and add this user manually in the Admin Dashboard.
	"""

	send_email(admin_email, subject, body)

	return {"message": "Signup request sent and saved to DB!"}

# Reports by product
from fastapi import Body

@app.post("/report/by-product/")
def report_by_product(filters: dict = Body(...)):
	start = filters.get("start_date")
	end = filters.get("end_date")
	property_id = filters.get("property_id")
	user_id = filters.get("user_id")

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
			SELECT 
				lp.name AS product_name, 
				gs.product_quantity AS quantity
			FROM green_services gs
			JOIN landscape_products lp ON gs.product_used = lp.id
			{where_sql}

			UNION ALL

			SELECT 'Bulk Salt' AS product_name, wl.bulk_salt_qty FROM winter_ops_logs wl {where_sql}
			UNION ALL
			SELECT 'Bag Salt', wl.bag_salt_qty FROM winter_ops_logs wl {where_sql}
			UNION ALL
			SELECT 'Calcium Chloride', wl.calcium_chloride_qty FROM winter_ops_logs wl {where_sql}
		) AS combined
		GROUP BY product_name
		ORDER BY total_used DESC;
	"""

	return fetch_query(query, params)

# Reports by Property
@app.post("/report/by-property/")
def report_by_property(filters: dict = Body(...)):
	start = filters.get("start_date")
	end = filters.get("end_date")
	property_id = filters.get("property_id")
	user_id = filters.get("user_id")

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

# Reports by user
@app.post("/report/by-user/")
def report_by_user(filters: dict = Body(...)):
	start = filters.get("start_date")
	end = filters.get("end_date")
	property_id = filters.get("property_id")
	user_id = filters.get("user_id")

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


# ➤ Fetch Admin Email from Database
def get_admin_email():
	query = "SELECT value FROM admin_settings WHERE setting = 'signup_notification_email'"
	result = fetch_query(query)
	if result and len(result) > 0:
		return result[0]['value']
	return 'contractorappdev@gmail.com'  # You can default this to your admin email

# def send_email(to_address, subject, body):
def send_email(to_address, subject, body):
	from_address = os.getenv("EMAIL_USER")
	password = os.getenv("EMAIL_PASSWORD")

	msg = MIMEText(body)
	msg["Subject"] = subject
	msg["From"] = from_address
	msg["To"] = to_address

	try:
		with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
			server.login(from_address, password)
			server.send_message(msg)
		print(f"✅ Email sent successfully to {to_address}")
	except Exception as e:
		print(f"❌ Failed to send email to {to_address}: {e}")
		

# # Allow Admin to Update Signup Email
@app.put("/update-signup-email/")
def update_signup_email(new_email: str = Form(...)):
	query = "UPDATE admin_settings SET value = %s WHERE setting = 'signup_notification_email'"
	execute_query(query, (new_email,))
	return {"message": f"Admin signup email updated to {new_email}"}

# Adding Signup Requests
@app.get("/signup-requests/")
def get_signup_requests(current_user: dict = Depends(get_current_user)):
	if current_user["role"] != "Admin":
		raise HTTPException(status_code=403, detail="Admins only!")

	query = "SELECT * FROM signup_requests ORDER BY request_date DESC"
	return fetch_query(query)

# User Signup Approval
@app.post("/approve-signup-requests/")
def approve_signup_requests(request_ids: list[int], current_user: dict = Depends(get_current_user)):
	if current_user["role"] != "Admin":
		raise HTTPException(status_code=403, detail="Admins only!")

	if not request_ids:
		raise HTTPException(status_code=400, detail="No request IDs provided")

	placeholders = ','.join(['%s'] * len(request_ids))
	query_fetch = f"SELECT * FROM signup_requests WHERE id IN ({placeholders})"
	requests = fetch_query(query_fetch, request_ids)

	if not requests:
		raise HTTPException(status_code=404, detail="No matching requests found")

	# Bulk insert users
	for req in requests:
		hashed_pw = hash_password("TempPassword123")  # You can later trigger password resets
		insert_query = """
			INSERT INTO users (name, phone, email, role, password)
			VALUES (%s, %s, %s, %s, %s)
		"""
		insert_values = (req['name'], req['phone'], req['email'], req['role'], hashed_pw)
		execute_query(insert_query, insert_values)

	# Clean up processed requests
	query_delete = f"DELETE FROM signup_requests WHERE id IN ({placeholders})"
	execute_query(query_delete, request_ids)

	return {"message": f"{len(request_ids)} signup requests approved and users created!"}

# Winter Products Endpoints
@app.get("/winter-products/")
def get_winter_products():
	return fetch_query("SELECT * FROM winter_products")

@app.post("/winter-products/")
def add_winter_product(name: str = Form(...), unit: str = Form(...)):
	query = "INSERT INTO winter_products (name, unit) VALUES (%s, %s)"
	execute_query(query, (name, unit))
	return {"message": "Winter product added successfully!"}


	execute_query(query, (name, unit))
	return {"message": "Winter product added successfully!"}

@app.put("/winter-products/{product_id}")
def update_winter_product(product_id: int, name: str = Form(...), unit: str = Form(...)):
	query = "UPDATE winter_products SET name = %s, unit = %s WHERE id = %s"
	execute_query(query, (name, unit, product_id))
	return {"message": "Winter product updated successfully!"}

@app.delete("/winter-products/{product_id}")
def delete_winter_product(product_id: int):
	query = "DELETE FROM winter_products WHERE id = %s"
	execute_query(query, (product_id,))
	return {"message": "Winter product deleted successfully!"}

# Landscape Products Endpoints 
@app.get("/landscape-products/")
def get_landscape_products():
	return fetch_query("SELECT * FROM landscape_products")

@app.post("/landscape-products/")
def add_landscape_product(name: str = Form(...), unit: str = Form(...)):
	query = "INSERT INTO landscape_products (name, unit) VALUES (%s, %s)"
	execute_query(query, (name, unit))
	return {"message": "Landscape product added successfully!"}


	execute_query(query, (name, unit))
	return {"message": "Landscape product added successfully!"}

@app.put("/landscape-products/{product_id}")
def update_landscape_product(product_id: int, name: str = Form(...), unit: str = Form(...)):
	query = "UPDATE landscape_products SET name = %s, unit = %s WHERE id = %s"
	execute_query(query, (name, unit, product_id))
	return {"message": "Landscape product updated successfully!"}

@app.delete("/landscape-products/{product_id}")
def delete_landscape_product(product_id: int):
	query = "DELETE FROM landscape_products WHERE id = %s"
	execute_query(query, (product_id,))
	return {"message": "Landscape product deleted successfully!"}

# Reset Password Endpoints
from fastapi import Form

@app.put("/reset-password/")
def reset_password(email: str = Form(...), new_password: str = Form(...), current_user: dict = Depends(get_current_user)):
	if current_user["role"] != "Admin":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")

	hashed_pw = hash_password(new_password)
	query = "UPDATE users SET password = %s WHERE email = %s"
	success = execute_query(query, (hashed_pw, email))

	if success:
		return {"message": "Password reset successful"}
	else:
		raise HTTPException(status_code=500, detail="Failed to reset password")


print("🔥 Uvicorn is starting...")
if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

from fastapi import Form

@app.post("/signup-request/")
def signup_request(
	name: str = Form(...),
	email: str = Form(...),
	phone: str = Form(...),
	role: str = Form(...),
	password: str = Form(...)
):
	try:
		msg = MIMEText(f"""
New signup request:

Name: {name}
Email: {email}
Phone: {phone}
Role: {role}
		""")
		msg["Subject"] = "New Signup Request"
		msg["From"] = EMAIL_USER
		msg["To"] = EMAIL_USER

		server = smtplib.SMTP("smtp.gmail.com", 587)
		server.starttls()
		server.login(EMAIL_USER, EMAIL_PASSWORD)
		server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
		server.quit()

		return {"message": "✅ Signup request sent!"}
	except Exception as e:
		return {"message": f"❌ Failed to send signup request: {str(e)}"}

from fastapi import Form

@app.post("/admin/create-user/")
def admin_create_user(
	name: str = Form(...),
	email: str = Form(...),
	phone: str = Form(...),
	role: str = Form(...),
	password: str = Form(...),
	current_user: dict = Depends(get_current_user)
):
	if current_user["role"] != "Admin":
		raise HTTPException(status_code=403, detail="Not authorized")

	hashed_pw = hash_password(password)

	try:
		execute_query("""
			INSERT INTO users (name, phone, email, role, password)
			VALUES (%s, %s, %s, %s, %s)
		""", (name, phone, email, role, hashed_pw))

		return {"ok": True, "message": "✅ User created successfully"}
	except Exception as e:
		return {"ok": False, "message": f"❌ Failed to create user: {str(e)}"}