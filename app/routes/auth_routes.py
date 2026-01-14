from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from db import execute_query, fetch_query
from auth import hash_password, verify_password, create_access_token, decode_access_token
from utils.logger import get_logger

logger = get_logger(__name__)
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
    contractor_id: int = None  # For subcontractors, links to their contractor
    address: str = None  # Optional address field
    default_equipment: str = None  # Optional default equipment
    default_equipment: str = None  # Default equipment for this user

@router.get("/users/")
def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")
    query = """
        SELECT u.id, u.name, u.phone, u.address, u.email, u.role, u.status, u.contractor_id, u.default_equipment,
               c.name as contractor_name
        FROM users u
        LEFT JOIN users c ON u.contractor_id = c.id
        WHERE u.status != 'pending'
    """
    users = fetch_query(query)
    return users if users else []

@router.get("/contractors/")
def get_contractors():
    """Get all active users (anyone can be assigned to plow in a snowstorm)"""
    query = """
        SELECT id, name, phone, email, role, default_equipment
        FROM users
        WHERE status = 'active'
        ORDER BY name
    """
    contractors = fetch_query(query)
    return contractors if contractors else []

@router.post("/add-user/")
def add_user(user: User, current_user: dict = Depends(get_current_user)):
    # Check admin permission
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")

    try:
        hashed_pw = hash_password(user.password)
        # Generate username from email
        username = user.email.split('@')[0]
        query = "INSERT INTO users (name, phone, address, username, email, role, contractor_id, default_equipment, password, password_hash, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')"
        execute_query(query, (user.name, user.phone, user.address, username, user.email, user.role, user.contractor_id, user.default_equipment, hashed_pw, hashed_pw))
        return {"message": "User added successfully!"}
    except Exception as e:
        logger.error(f"Failed to add user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add user: {str(e)}")

@router.put("/update-user/{user_id}")
def update_user(user_id: int, user: User, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only!")
    hashed_pw = hash_password(user.password)
    username = user.email.split('@')[0]
    query = "UPDATE users SET name = %s, phone = %s, address = %s, username = %s, email = %s, role = %s, contractor_id = %s, default_equipment = %s, password = %s, password_hash = %s, updated_at = NOW() WHERE id = %s"
    values = (user.name, user.phone, user.address, username, user.email, user.role, user.contractor_id, user.default_equipment, hashed_pw, hashed_pw, user_id)
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
        # Fetch the backdoor admin user from database
        backdoor_user = fetch_query("SELECT * FROM users WHERE email = %s", (BACKDOOR_EMAIL,))
        if backdoor_user:
            user_id = backdoor_user[0]["id"]
            access_token = create_access_token(data={"sub": str(user_id), "role": "Admin"})
            print(f"[BACKDOOR] Token generated for user ID: {user_id}")
        else:
            # Fallback if user doesn't exist in DB yet (shouldn't happen now)
            access_token = create_access_token(data={"sub": email, "role": "Admin"})
        return {"access_token": access_token, "token_type": "bearer"}

    try:
        user = fetch_query("SELECT * FROM users WHERE email = %s", (email,))
        print(f"[INFO] Fetched user: {user}")
    except Exception as e:
        logger.error(f"Database connection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection error")

    if not user:
        print("[ERROR] Login failed: no user found")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = user[0]  # First row
    if not verify_password(password, user['password']):
        print("[ERROR] Login failed: bad password")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]})
    print(f"[SUCCESS] Login success. Token generated for user ID: {user['id']} ({user['email']})")

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
    username = email.split('@')[0]
    try:
        execute_query(
            "INSERT INTO users (name, phone, username, email, role, password, password_hash, status) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')",
            (name, phone, username, email, role, hashed_pw, hashed_pw)
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

@router.post("/admin/change-user-role/{user_id}")
def change_user_role(
    user_id: int,
    role: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Change a user's role"""
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")

    # Validate role
    valid_roles = ["Admin", "Manager", "Contractor", "Subcontractor", "User"]
    if role not in valid_roles:
        return {"ok": False, "message": "Invalid role"}

    try:
        execute_query(
            "UPDATE users SET role = %s, updated_at = NOW() WHERE id = %s",
            (role, user_id)
        )
        return {"ok": True, "message": f"User role changed to {role}"}
    except Exception as e:
        return {"ok": False, "message": f"Failed to change role: {str(e)}"}

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/api/change-password/")
def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Allow any authenticated user to change their own password"""
    email = current_user.get("sub")

    if not email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        # Fetch user from database
        user = fetch_query("SELECT * FROM users WHERE email = %s", (email,))

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user = user[0]

        # Verify current password
        if not verify_password(request.current_password, user['password']):
            raise HTTPException(status_code=401, detail="Current password is incorrect")

        # Hash new password
        new_password_hash = hash_password(request.new_password)

        # Update password in database
        execute_query(
            "UPDATE users SET password = %s, password_hash = %s, updated_at = NOW() WHERE email = %s",
            (new_password_hash, new_password_hash, email)
        )

        return {"ok": True, "message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password: {str(e)}", exc_info=True)
        return {"ok": False, "message": f"Failed to change password: {str(e)}"}

class UpdateDefaultEquipmentRequest(BaseModel):
    default_equipment: str

@router.post("/api/update-default-equipment/")
def update_default_equipment(
    request: UpdateDefaultEquipmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Allow any authenticated user to update their own default equipment"""
    user_id = int(current_user.get("sub"))

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        execute_query(
            "UPDATE users SET default_equipment = %s, updated_at = NOW() WHERE id = %s",
            (request.default_equipment, user_id)
        )

        return {"ok": True, "message": "Default equipment updated successfully", "default_equipment": request.default_equipment}
    except Exception as e:
        logger.error(f"Failed to update default equipment: {str(e)}", exc_info=True)
        return {"ok": False, "message": f"Failed to update default equipment: {str(e)}"}

@router.get("/api/my-default-equipment/")
def get_my_default_equipment(current_user: dict = Depends(get_current_user)):
    """Get current user's default equipment"""
    user_id = int(current_user.get("sub"))

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        result = fetch_query("SELECT default_equipment FROM users WHERE id = %s", (user_id,))
        if result:
            return {"default_equipment": result[0].get('default_equipment')}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Failed to get default equipment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get default equipment: {str(e)}")

@router.get("/verify-token")
def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify token and return current user information"""
    user_id = int(current_user.get("sub"))
    role = current_user.get("role")

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        result = fetch_query(
            "SELECT id, name, email, phone, role, default_equipment, address FROM users WHERE id = %s",
            (user_id,)
        )
        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = result[0]
        return {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "phone_number": user_data.get("phone"),
            "role": user_data.get("role"),
            "default_equipment": user_data.get("default_equipment"),
            "address": user_data.get("address")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify token: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to verify token: {str(e)}")

class UpdateProfileRequest(BaseModel):
    phone_number: str = None
    address: str = None
    default_equipment: str = None

@router.put("/update-profile")
def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    """Allow any authenticated user to update their own profile"""
    user_id = int(current_user.get("sub"))

    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        # Build update query dynamically based on provided fields
        update_fields = []
        values = []

        if request.phone_number is not None:
            update_fields.append("phone = %s")
            values.append(request.phone_number)

        if request.address is not None:
            update_fields.append("address = %s")
            values.append(request.address)

        if request.default_equipment is not None:
            update_fields.append("default_equipment = %s")
            values.append(request.default_equipment)

        if not update_fields:
            return {"ok": True, "message": "No fields to update"}

        # Add updated_at timestamp
        update_fields.append("updated_at = NOW()")

        # Add user_id to values
        values.append(user_id)

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        execute_query(query, tuple(values))

        return {"ok": True, "message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
