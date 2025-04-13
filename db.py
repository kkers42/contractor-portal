import pymysql
import os

# Load database config from environment variables
DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),              # Should be the Unix socket path
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME"),
    "unix_socket": os.environ.get("DB_HOST"),       # Cloud SQL Unix socket path
    "cursorclass": pymysql.cursors.DictCursor
}

print("🚀 DB Config:", DB_CONFIG)

def get_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print(f"❌ Database connection error: {e}")
        return None

def fetch_query(query, params=None):
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            results = cursor.fetchall()
        conn.close()
        return results
    except pymysql.MySQLError as e:
        print(f"❌ Fetch query error: {e}")
        return None

def execute_query(query, params=None):
    conn = get_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            conn.commit()
    except pymysql.MySQLError as e:
        print(f"❌ Execute query error: {e}")
    finally:
        conn.close()
