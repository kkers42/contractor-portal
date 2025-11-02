from fastapi import APIRouter, Depends, HTTPException, status, Form
from db import fetch_query, execute_query
from auth import get_current_user, hash_password
import os
import smtplib
from email.mime.text import MIMEText

router = APIRouter()

@router.post("/signup-request/")
def signup_request(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    role: str = Form(...),
    password: str = Form(...)
):
    print(f"[INFO] Processing signup request for: {email}")

    # First, save to database with pending status
    hashed_pw = hash_password(password)
    # Generate username from email (everything before @)
    username = email.split('@')[0]
    try:
        # Check if status column exists, if not use query without it
        query = """
            INSERT INTO users (name, phone, username, email, role, password, password_hash, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
        """
        values = (name, phone, username, email, role, hashed_pw, hashed_pw)
        execute_query(query, values)
        print(f"[SUCCESS] User created with pending status: {email}")
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Failed to save signup request: {error_msg}")

        # If status column doesn't exist, try without it
        if "status" in error_msg.lower() or "unknown column" in error_msg.lower():
            try:
                print("[INFO] Retrying without status column...")
                query = """
                    INSERT INTO users (name, phone, username, email, role, password, password_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = (name, phone, username, email, role, hashed_pw, hashed_pw)
                execute_query(query, values)
                print(f"[SUCCESS] User created without status: {email}")
            except Exception as e2:
                print(f"[ERROR] Retry also failed: {str(e2)}")
                raise HTTPException(status_code=500, detail=f"Failed to save signup request: {str(e2)}")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to save signup request: {error_msg}")

    # Then try to send email notification (non-critical)
    try:
        msg = MIMEText(f"""
New signup request:

Name: {name}
Email: {email}
Phone: {phone}
Role: {role}

Please review in the Admin Dashboard under Pending Users.
        """)
        msg["Subject"] = "New Signup Request"
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = os.getenv("EMAIL_USER")

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
        server.sendmail(os.getenv("EMAIL_USER"), os.getenv("EMAIL_USER"), msg.as_string())
        server.quit()
        print("[INFO] Signup notification email sent successfully")
    except Exception as e:
        print(f"[WARN] Failed to send signup email (non-critical): {str(e)}")

    return {"message": "✅ Signup request submitted! Awaiting admin approval."}

@router.post("/request-user/")
def request_user(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    role: str = Form(...)
):
    admin_email = get_admin_email()

    query = """
        INSERT INTO signup_requests (name, phone, email, role)
        VALUES (%s, %s, %s, %s)
    """
    values = (name, phone, email, role)
    execute_query(query, values)

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

@router.get("/signup-requests/")
def get_signup_requests(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    query = "SELECT id, name, phone, email, role, created_at as request_date FROM users WHERE status = 'pending' ORDER BY created_at DESC"
    results = fetch_query(query)
    return results if results else []

@router.post("/approve-signup-requests/")
def approve_signup_requests(request_ids: list[int], current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    if not request_ids:
        raise HTTPException(status_code=400, detail="No request IDs provided")

    placeholders = ','.join(['%s'] * len(request_ids))
    # Update status from 'pending' to 'active' for approved users
    query_update = f"UPDATE users SET status = 'active' WHERE id IN ({placeholders}) AND status = 'pending'"
    execute_query(query_update, request_ids)

    return {"message": f"{len(request_ids)} signup requests approved!"}

@router.put("/update-signup-email/")
def update_signup_email(new_email: str = Form(...)):
    query = "UPDATE admin_settings SET value = %s WHERE setting = 'signup_notification_email'"
    execute_query(query, (new_email,))
    return {"message": f"Admin signup email updated to {new_email}"}

@router.put("/reset-password/")
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

def get_admin_email():
    query = "SELECT value FROM admin_settings WHERE setting = 'signup_notification_email'"
    result = fetch_query(query)
    if result and len(result) > 0:
        return result[0]['value']
    return 'contractorappdev@gmail.com'

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
