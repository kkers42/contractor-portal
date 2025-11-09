from typing import Optional
from .db import get_conn

def upsert_identity(user_id: int, provider: str, subject: str, email: Optional[str], email_verified: bool):
    sql = """
    INSERT INTO identities (user_id, provider, subject, email, email_verified, created_at, updated_at)
    VALUES (%s,%s,%s,%s,%s,NOW(),NOW())
    ON DUPLICATE KEY UPDATE email=VALUES(email), email_verified=VALUES(email_verified), updated_at=NOW();
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, provider, subject, email, 1 if email_verified else 0))
        conn.commit()

def get_user_by_identity(provider: str, subject: str) -> Optional[int]:
    sql = "SELECT u.id FROM identities i JOIN users u ON u.id=i.user_id WHERE i.provider=%s AND i.subject=%s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (provider, subject))
            row = cur.fetchone()
            return int(row[0]) if row else None

def get_user_by_email(email: str) -> Optional[tuple]:
    """Returns (user_id, status, role) or None"""
    sql = "SELECT id, status, role FROM users WHERE email=%s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()
            if row:
                return (int(row[0]), row[1], row[2])
            return None

def get_user_status_and_role(user_id: int) -> tuple:
    """Returns (status, role) for a user"""
    sql = "SELECT status, role FROM users WHERE id=%s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            if row:
                return (row[0], row[1])
            return ("pending", "User")

def create_user(email: Optional[str], display_name: Optional[str], avatar_url: Optional[str]) -> int:
    # Generate username from email
    username = email.split('@')[0] if email else "oauth_user"
    # Use display_name for name field if available, otherwise use username
    name = display_name if display_name else username

    sql = """INSERT INTO users (name, username, email, display_name, avatar_url, password, password_hash, status, role, created_at, updated_at)
             VALUES (%s,%s,%s,%s,%s,'','','pending','User',NOW(),NOW())"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (name, username, email, display_name, avatar_url))
            user_id = cur.lastrowid
        conn.commit()
    return int(user_id)

def touch_last_login(user_id: int):
    sql = "UPDATE users SET last_login_at=NOW(), updated_at=NOW() WHERE id=%s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
        conn.commit()
