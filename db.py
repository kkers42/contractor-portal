import mysql.connector
from mysql.connector import Error
import os

# ✅ REMOVE: from dotenv import load_dotenv
# ✅ REMOVE: load_dotenv()

DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME")
}

print("🚀 DB Config:", DB_CONFIG)

def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def fetch_query(query, params=None):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except mysql.connector.Error as e:
        print(f"❌ Fetch query error: {e}")
        return None

def execute_query(query, params=None):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()