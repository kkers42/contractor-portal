from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from db import execute_query, fetch_query
from auth import hash_password, verify_password, create_access_token, decode_access_token
from pydantic import BaseModel
from auth import get_current_user

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

@router.post("/api/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    password = form_data.password
    user = fetch_query("SELECT * FROM users WHERE email = %s", (email,))
    if not user or not verify_password(password, user[0]['password']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user[0]['email'], "role": user[0]['role']})
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
        return {"ok": True, "message": "✅ User created successfully"}
    except Exception as e:
        return {"ok": False, "message": f"❌ Failed to create user: {str(e)}"}
