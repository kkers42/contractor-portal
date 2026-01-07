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

def get_user_by_email(email: str) -> Optional[int]:
    sql = "SELECT id FROM users WHERE email=%s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()
            return int(row[0]) if row else None

def create_user(email: Optional[str], display_name: Optional[str], avatar_url: Optional[str]) -> int:
    sql = "INSERT INTO users (email, display_name, avatar_url, created_at, updated_at) VALUES (%s,%s,%s,NOW(),NOW())"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email, display_name, avatar_url))
            user_id = cur.lastrowid
        conn.commit()
    return int(user_id)

def touch_last_login(user_id: int):
    sql = "UPDATE users SET last_login_at=NOW(), updated_at=NOW() WHERE id=%s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
        conn.commit()
