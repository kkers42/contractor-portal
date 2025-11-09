import mysql.connector
from mysql.connector import Error
import os
#from dotenv import load_dotenv # Comment out for server
#load_dotenv() # Comment out for server

DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME")
}

print("DB Config:", DB_CONFIG)
print("DB_HOST ENV:", os.getenv("DB_HOST"))


def get_connection():
    try:
        if DB_CONFIG["host"] and DB_CONFIG["host"].startswith("/cloudsql/"):
            return mysql.connector.connect(
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"],
                unix_socket=DB_CONFIG["host"]
            )
        else:
            return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"[ERROR] Database connection error: {e}")
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
        print(f"[ERROR] Fetch query error: {e}")
        return None

def execute_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()

def insert_location(user_id, property_id, time_in, time_out, notes=None):
    query = """
        INSERT INTO location_logs (user_id, property_id, time_in, time_out, notes)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (user_id, property_id, time_in, time_out, notes)
    try:
        execute_query(query, params)
        print(f"[SUCCESS] Location log inserted: user_id={user_id}, property_id={property_id}")
    except Error as e:
        print(f"[ERROR] Insert location error: {e}")
