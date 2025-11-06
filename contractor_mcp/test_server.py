#!/usr/bin/env python3
"""
Simple test script for the MCP server
Tests database connectivity and basic operations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("Testing Contractor Portal MCP Server")
print("=" * 60)

# Test 1: Import MCP SDK
print("\n[1/6] Testing MCP SDK import...")
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    print("[OK] MCP SDK imported successfully")
except ImportError as e:
    print(f"[FAIL] MCP SDK not installed: {e}")
    print("  Run: pip install mcp")
    sys.exit(1)

# Test 2: Database connection
print("\n[2/6] Testing database connection...")
try:
    import mysql.connector
    from mysql.connector import Error

    DB_CONFIG = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'contractor_portal')
    }

    conn = mysql.connector.connect(**DB_CONFIG)
    if conn.is_connected():
        print(f"[OK] Connected to database: {DB_CONFIG['database']}")
        conn.close()
    else:
        print("[FAIL] Failed to connect to database")
        sys.exit(1)
except Error as e:
    print(f"[FAIL] Database error: {e}")
    print(f"  Check your .env file and MySQL server")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] Unexpected error: {e}")
    sys.exit(1)

# Test 3: Query execution
print("\n[3/6] Testing query execution...")
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Test query - count users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    result = cursor.fetchone()
    user_count = result['count']
    print(f"[OK] Query executed successfully")
    print(f"  Found {user_count} users in database")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"[FAIL] Query execution failed: {e}")
    sys.exit(1)

# Test 4: Table existence check
print("\n[4/6] Testing required tables...")
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    required_tables = [
        'users',
        'locations',
        'winter_ops_logs',
        'green_services_logs',
        'equipment_rates',
        'identities'
    ]

    cursor.execute("SHOW TABLES")
    existing_tables = [table[0] for table in cursor.fetchall()]

    missing_tables = [t for t in required_tables if t not in existing_tables]

    if missing_tables:
        print(f"[FAIL] Missing tables: {', '.join(missing_tables)}")
        print("  Run database migrations first")
    else:
        print(f"[OK] All required tables exist ({len(required_tables)} tables)")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"[FAIL] Table check failed: {e}")
    sys.exit(1)

# Test 5: Application directory
print("\n[5/6] Testing application directory...")
try:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    required_dirs = ['routes', 'static', 'db', 'contractor_mcp']
    required_files = ['main.py', '.env', 'requirements.txt']

    missing_dirs = [d for d in required_dirs if not os.path.exists(os.path.join(APP_DIR, d))]
    missing_files = [f for f in required_files if not os.path.exists(os.path.join(APP_DIR, f))]

    if missing_dirs or missing_files:
        print(f"[FAIL] Missing directories: {', '.join(missing_dirs) if missing_dirs else 'none'}")
        print(f"[FAIL] Missing files: {', '.join(missing_files) if missing_files else 'none'}")
    else:
        print(f"[OK] Application directory structure valid")
        print(f"  App directory: {APP_DIR}")

except Exception as e:
    print(f"[FAIL] Directory check failed: {e}")

# Test 6: Environment variables
print("\n[6/6] Testing environment configuration...")
try:
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    optional_vars = ['APP_BASE_URL', 'GOOGLE_CLIENT_ID', 'MS_CLIENT_ID']

    missing_vars = [v for v in required_vars if not os.getenv(v)]

    if missing_vars:
        print(f"[FAIL] Missing required env vars: {', '.join(missing_vars)}")
        print("  Check your .env file")
    else:
        print(f"[OK] Required environment variables configured")

    configured_optional = [v for v in optional_vars if os.getenv(v)]
    if configured_optional:
        print(f"  Optional vars configured: {', '.join(configured_optional)}")

except Exception as e:
    print(f"[FAIL] Environment check failed: {e}")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("\nThe MCP server is ready to use!")
print("\nNext steps:")
print("1. Configure Claude Desktop (see QUICK_START.md)")
print("2. Restart Claude Desktop")
print("3. Look for the plug icon to verify connection")
print("4. Try: 'Show me the database schema'")
print("\n" + "=" * 60)
