#!/usr/bin/env python3
"""
MCP Server for Contractor Portal
Provides tools for database queries, API testing, and application management
"""

import asyncio
import os
import sys
from typing import Any, Optional
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel
    )
    from pydantic import AnyUrl
except ImportError:
    print("ERROR: MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'contractor_portal')
}

# Application configuration
APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://localhost:8080')
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

server = Server("contractor-portal-mcp")

def get_db_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise Exception(f"Database connection failed: {e}")

def execute_query(query: str, params: tuple = None) -> list:
    """Execute a SELECT query and return results"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        results = cursor.fetchall()

        # Convert datetime objects to strings for JSON serialization
        for row in results:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()

        return results
    finally:
        cursor.close()
        conn.close()

def execute_update(query: str, params: tuple = None) -> dict:
    """Execute an INSERT/UPDATE/DELETE query"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return {
            "affected_rows": cursor.rowcount,
            "last_insert_id": cursor.lastrowid
        }
    finally:
        cursor.close()
        conn.close()

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri=AnyUrl("contractor://database/schema"),
            name="Database Schema",
            description="Current database schema and tables",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("contractor://config/env"),
            name="Environment Configuration",
            description="Current environment variables and configuration",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("contractor://stats/overview"),
            name="Application Statistics",
            description="Overview of users, properties, logs, and activity",
            mimeType="application/json",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource"""

    if uri.scheme != "contractor":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    path = f"{uri.host}/{uri.path}".rstrip("/")

    if path == "database/schema":
        # Get table information
        tables_query = "SHOW TABLES"
        tables = execute_query(tables_query)

        schema = {}
        for table_row in tables:
            table_name = list(table_row.values())[0]
            columns_query = f"DESCRIBE {table_name}"
            columns = execute_query(columns_query)
            schema[table_name] = columns

        return json.dumps(schema, indent=2)

    elif path == "config/env":
        config = {
            "DB_HOST": DB_CONFIG['host'],
            "DB_NAME": DB_CONFIG['database'],
            "APP_BASE_URL": APP_BASE_URL,
            "APP_DIR": APP_DIR,
            "GOOGLE_CLIENT_ID": os.getenv('GOOGLE_CLIENT_ID', 'Not configured'),
            "MS_CLIENT_ID": os.getenv('MS_CLIENT_ID', 'Not configured'),
        }
        return json.dumps(config, indent=2)

    elif path == "stats/overview":
        stats = {}

        # Count users by role and status
        stats['users'] = execute_query("""
            SELECT role, status, COUNT(*) as count
            FROM users
            GROUP BY role, status
        """)

        # Count properties
        stats['properties'] = execute_query("SELECT COUNT(*) as count FROM locations")[0]

        # Count logs
        stats['winter_logs'] = execute_query("SELECT COUNT(*) as count FROM winter_ops_logs")[0]
        stats['green_logs'] = execute_query("SELECT COUNT(*) as count FROM green_services_logs")[0]

        # Recent activity
        stats['recent_logins'] = execute_query("""
            SELECT name, email, role, last_login_at
            FROM users
            WHERE last_login_at IS NOT NULL
            ORDER BY last_login_at DESC
            LIMIT 10
        """)

        return json.dumps(stats, indent=2)

    else:
        raise ValueError(f"Unknown resource path: {path}")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="query_database",
            description="Execute a SELECT query on the contractor portal database. Returns results as JSON.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional parameters for parameterized queries",
                        "items": {"type": "string"}
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="update_database",
            description="Execute an INSERT, UPDATE, or DELETE query on the database. Use with caution!",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL INSERT/UPDATE/DELETE query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional parameters for parameterized queries",
                        "items": {"type": "string"}
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_user_info",
            description="Get detailed information about a user by email or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "User email or ID"
                    }
                },
                "required": ["identifier"]
            }
        ),
        Tool(
            name="get_property_info",
            description="Get detailed information about a property by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Property name or ID"
                    }
                },
                "required": ["identifier"]
            }
        ),
        Tool(
            name="get_logs",
            description="Get operation logs (winter or green services) with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "log_type": {
                        "type": "string",
                        "enum": ["winter", "green"],
                        "description": "Type of logs to retrieve"
                    },
                    "property_id": {
                        "type": "integer",
                        "description": "Filter by property ID"
                    },
                    "contractor_id": {
                        "type": "integer",
                        "description": "Filter by contractor ID"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Filter logs after this date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Filter logs before this date (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of logs to return (default 100)"
                    }
                },
                "required": ["log_type"]
            }
        ),
        Tool(
            name="approve_pending_users",
            description="Approve pending OAuth users and assign them roles",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "User ID to approve"
                    },
                    "role": {
                        "type": "string",
                        "enum": ["Admin", "Manager", "Subcontractor"],
                        "description": "Role to assign to the user"
                    }
                },
                "required": ["user_id", "role"]
            }
        ),
        Tool(
            name="read_file",
            description="Read a file from the application directory (code files, configs, logs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from application root (e.g., 'routes/auth_routes.py', '.env', 'static/login.html')"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="list_files",
            description="List files in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from application root (e.g., 'routes', 'static')"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional glob pattern to filter files (e.g., '*.py', '*.html')"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="get_equipment_usage",
            description="Get equipment usage report with cost calculations",
            inputSchema={
                "type": "object",
                "properties": {
                    "equipment_name": {
                        "type": "string",
                        "description": "Filter by equipment name"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    },
                    "contractor_id": {
                        "type": "integer",
                        "description": "Filter by contractor ID"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="deploy_to_hostinger",
            description="Deploy the contractor portal to Hostinger VPS via SSH. Automates the entire deployment process.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vps_host": {
                        "type": "string",
                        "description": "VPS IP address or hostname"
                    },
                    "ssh_user": {
                        "type": "string",
                        "description": "SSH username (default: root)",
                        "default": "root"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain name for the application"
                    },
                    "db_password": {
                        "type": "string",
                        "description": "MySQL database password to set"
                    },
                    "ssh_key_path": {
                        "type": "string",
                        "description": "Path to SSH private key (optional, uses default if not provided)"
                    }
                },
                "required": ["vps_host", "domain", "db_password"]
            }
        ),
        Tool(
            name="check_deployment_status",
            description="Check the status of the deployed application on Hostinger VPS",
            inputSchema={
                "type": "object",
                "properties": {
                    "vps_host": {
                        "type": "string",
                        "description": "VPS IP address or hostname"
                    },
                    "ssh_user": {
                        "type": "string",
                        "description": "SSH username (default: root)",
                        "default": "root"
                    }
                },
                "required": ["vps_host"]
            }
        ),
        Tool(
            name="configure_dns",
            description="Generate DNS configuration instructions for Hostinger domain setup",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to configure"
                    },
                    "vps_ip": {
                        "type": "string",
                        "description": "VPS IP address to point domain to"
                    }
                },
                "required": ["domain", "vps_ip"]
            }
        ),
        Tool(
            name="setup_ssl",
            description="Set up SSL certificate via Let's Encrypt on the VPS",
            inputSchema={
                "type": "object",
                "properties": {
                    "vps_host": {
                        "type": "string",
                        "description": "VPS IP address or hostname"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain name for SSL certificate"
                    },
                    "ssh_user": {
                        "type": "string",
                        "description": "SSH username (default: root)",
                        "default": "root"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address for Let's Encrypt notifications"
                    }
                },
                "required": ["vps_host", "domain", "email"]
            }
        ),
        Tool(
            name="view_deployment_logs",
            description="View application logs from the deployed VPS",
            inputSchema={
                "type": "object",
                "properties": {
                    "vps_host": {
                        "type": "string",
                        "description": "VPS IP address or hostname"
                    },
                    "ssh_user": {
                        "type": "string",
                        "description": "SSH username (default: root)",
                        "default": "root"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of log lines to retrieve (default: 100)",
                        "default": 100
                    }
                },
                "required": ["vps_host"]
            }
        ),
        Tool(
            name="restart_application",
            description="Restart the contractor portal application on VPS",
            inputSchema={
                "type": "object",
                "properties": {
                    "vps_host": {
                        "type": "string",
                        "description": "VPS IP address or hostname"
                    },
                    "ssh_user": {
                        "type": "string",
                        "description": "SSH username (default: root)",
                        "default": "root"
                    }
                },
                "required": ["vps_host"]
            }
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution"""

    try:
        if name == "query_database":
            query = arguments["query"]
            params = tuple(arguments.get("params", []))
            results = execute_query(query, params if params else None)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "update_database":
            query = arguments["query"]
            params = tuple(arguments.get("params", []))
            result = execute_update(query, params if params else None)
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        elif name == "get_user_info":
            identifier = arguments["identifier"]

            # Try as email first, then as ID
            if "@" in identifier:
                query = """
                    SELECT u.*, c.name as contractor_name,
                           GROUP_CONCAT(CONCAT(i.provider, ':', i.email) SEPARATOR ', ') as oauth_identities
                    FROM users u
                    LEFT JOIN users c ON u.contractor_id = c.id
                    LEFT JOIN identities i ON i.user_id = u.id
                    WHERE u.email = %s
                    GROUP BY u.id
                """
                params = (identifier,)
            else:
                query = """
                    SELECT u.*, c.name as contractor_name,
                           GROUP_CONCAT(CONCAT(i.provider, ':', i.email) SEPARATOR ', ') as oauth_identities
                    FROM users u
                    LEFT JOIN users c ON u.contractor_id = c.id
                    LEFT JOIN identities i ON i.user_id = u.id
                    WHERE u.id = %s
                    GROUP BY u.id
                """
                params = (int(identifier),)

            results = execute_query(query, params)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "get_property_info":
            identifier = arguments["identifier"]

            # Try as ID first, then as name
            try:
                prop_id = int(identifier)
                query = "SELECT * FROM locations WHERE id = %s"
                params = (prop_id,)
            except ValueError:
                query = "SELECT * FROM locations WHERE name LIKE %s"
                params = (f"%{identifier}%",)

            results = execute_query(query, params)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "get_logs":
            log_type = arguments["log_type"]
            table = "winter_ops_logs" if log_type == "winter" else "green_services_logs"

            query = f"""
                SELECT l.*, loc.name as property_name
                FROM {table} l
                JOIN locations loc ON l.property_id = loc.id
                WHERE 1=1
            """
            params = []

            if arguments.get("property_id"):
                query += " AND l.property_id = %s"
                params.append(arguments["property_id"])

            if arguments.get("contractor_id"):
                query += " AND l.contractor_id = %s"
                params.append(arguments["contractor_id"])

            if arguments.get("start_date"):
                query += " AND DATE(l.time_in) >= %s"
                params.append(arguments["start_date"])

            if arguments.get("end_date"):
                query += " AND DATE(l.time_in) <= %s"
                params.append(arguments["end_date"])

            query += " ORDER BY l.time_in DESC"

            limit = arguments.get("limit", 100)
            query += f" LIMIT {limit}"

            results = execute_query(query, tuple(params) if params else None)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "approve_pending_users":
            user_id = arguments["user_id"]
            role = arguments["role"]

            result = execute_update(
                "UPDATE users SET status = 'active', role = %s, updated_at = NOW() WHERE id = %s",
                (role, user_id)
            )

            return [TextContent(
                type="text",
                text=f"User {user_id} approved as {role}. Affected rows: {result['affected_rows']}"
            )]

        elif name == "read_file":
            path = arguments["path"]
            file_path = os.path.join(APP_DIR, path)

            # Security: prevent path traversal
            if not os.path.abspath(file_path).startswith(APP_DIR):
                raise ValueError("Access denied: Path traversal not allowed")

            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return [TextContent(
                type="text",
                text=content
            )]

        elif name == "list_files":
            path = arguments["path"]
            pattern = arguments.get("pattern", "*")

            dir_path = os.path.join(APP_DIR, path)

            # Security: prevent path traversal
            if not os.path.abspath(dir_path).startswith(APP_DIR):
                raise ValueError("Access denied: Path traversal not allowed")

            if not os.path.exists(dir_path):
                raise ValueError(f"Directory not found: {path}")

            import glob
            files = glob.glob(os.path.join(dir_path, pattern))

            # Convert to relative paths
            files = [os.path.relpath(f, APP_DIR) for f in files]

            return [TextContent(
                type="text",
                text=json.dumps(files, indent=2)
            )]

        elif name == "get_equipment_usage":
            query = """
                SELECT
                    w.equipment,
                    e.hourly_rate,
                    COUNT(*) as total_uses,
                    SUM(TIMESTAMPDIFF(HOUR, w.time_in, w.time_out)) as total_hours,
                    SUM(TIMESTAMPDIFF(HOUR, w.time_in, w.time_out) * e.hourly_rate) as total_cost
                FROM winter_ops_logs w
                LEFT JOIN equipment_rates e ON w.equipment = e.equipment_name
                WHERE 1=1
            """
            params = []

            if arguments.get("equipment_name"):
                query += " AND w.equipment = %s"
                params.append(arguments["equipment_name"])

            if arguments.get("start_date"):
                query += " AND DATE(w.time_in) >= %s"
                params.append(arguments["start_date"])

            if arguments.get("end_date"):
                query += " AND DATE(w.time_in) <= %s"
                params.append(arguments["end_date"])

            if arguments.get("contractor_id"):
                query += " AND w.contractor_id = %s"
                params.append(arguments["contractor_id"])

            query += " GROUP BY w.equipment, e.hourly_rate"

            results = execute_query(query, tuple(params) if params else None)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "deploy_to_hostinger":
            import subprocess
            import tempfile

            vps_host = arguments["vps_host"]
            ssh_user = arguments.get("ssh_user", "root")
            domain = arguments["domain"]
            db_password = arguments["db_password"]
            ssh_key_path = arguments.get("ssh_key_path", "")

            # Build SSH command prefix
            ssh_cmd = f"ssh {ssh_user}@{vps_host}"
            if ssh_key_path:
                ssh_cmd = f"ssh -i {ssh_key_path} {ssh_user}@{vps_host}"

            # Create deployment script with custom values
            deploy_script_url = "https://raw.githubusercontent.com/kkers42/contractor-portal/beta/deploy-to-hostinger.sh"

            commands = [
                f"{ssh_cmd} 'curl -sL {deploy_script_url} -o /tmp/deploy.sh'",
                f"{ssh_cmd} 'sed -i \"s/DOMAIN=\\\"your-domain.com\\\"/DOMAIN=\\\"{domain}\\\"/\" /tmp/deploy.sh'",
                f"{ssh_cmd} 'sed -i \"s/DB_PASS=\\\"Bimmer325!\\\"/DB_PASS=\\\"{db_password}\\\"/\" /tmp/deploy.sh'",
                f"{ssh_cmd} 'chmod +x /tmp/deploy.sh'",
                f"{ssh_cmd} 'bash /tmp/deploy.sh'",
            ]

            results = []
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
                    results.append({
                        "command": cmd,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    })
                except subprocess.TimeoutExpired:
                    results.append({
                        "command": cmd,
                        "error": "Command timed out after 10 minutes"
                    })
                except Exception as e:
                    results.append({
                        "command": cmd,
                        "error": str(e)
                    })

            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "check_deployment_status":
            import subprocess

            vps_host = arguments["vps_host"]
            ssh_user = arguments.get("ssh_user", "root")

            ssh_cmd = f"ssh {ssh_user}@{vps_host}"

            # Check various aspects of deployment
            checks = {
                "application_status": "systemctl status contractor-portal --no-pager",
                "nginx_status": "systemctl status nginx --no-pager",
                "mysql_status": "systemctl status mysql --no-pager",
                "disk_space": "df -h /opt",
                "recent_logs": "journalctl -u contractor-portal -n 20 --no-pager",
                "listening_ports": "netstat -tlnp | grep -E ':(80|443|8080|3306)'",
            }

            results = {}
            for check_name, command in checks.items():
                try:
                    full_cmd = f"{ssh_cmd} '{command}'"
                    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
                    results[check_name] = {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    }
                except Exception as e:
                    results[check_name] = {"error": str(e)}

            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "configure_dns":
            domain = arguments["domain"]
            vps_ip = arguments["vps_ip"]

            instructions = {
                "domain": domain,
                "vps_ip": vps_ip,
                "instructions": [
                    "Log in to your Hostinger control panel",
                    "Navigate to 'Domains' section",
                    "Click on your domain: " + domain,
                    "Go to 'DNS / Name Servers' tab",
                    "Add or update the following DNS records:"
                ],
                "dns_records": [
                    {
                        "type": "A",
                        "name": "@",
                        "points_to": vps_ip,
                        "ttl": 3600,
                        "description": "Root domain"
                    },
                    {
                        "type": "A",
                        "name": "www",
                        "points_to": vps_ip,
                        "ttl": 3600,
                        "description": "WWW subdomain"
                    }
                ],
                "notes": [
                    "DNS propagation can take 5-30 minutes",
                    "You can check propagation with: dig " + domain,
                    "Or use online tools like: whatsmydns.net",
                    "Once DNS resolves, proceed with SSL setup"
                ]
            }

            return [TextContent(
                type="text",
                text=json.dumps(instructions, indent=2)
            )]

        elif name == "setup_ssl":
            import subprocess

            vps_host = arguments["vps_host"]
            domain = arguments["domain"]
            ssh_user = arguments.get("ssh_user", "root")
            email = arguments["email"]

            ssh_cmd = f"ssh {ssh_user}@{vps_host}"

            # Check DNS first
            dns_check_cmd = f"dig +short {domain}"
            try:
                dns_result = subprocess.run(dns_check_cmd, shell=True, capture_output=True, text=True, timeout=10)
                resolved_ip = dns_result.stdout.strip()
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"DNS check failed: {str(e)}. Make sure DNS is configured before setting up SSL."
                )]

            # Run certbot
            certbot_cmd = f"{ssh_cmd} 'certbot --nginx -d {domain} -d www.{domain} --non-interactive --agree-tos --email {email} --redirect'"

            try:
                result = subprocess.run(certbot_cmd, shell=True, capture_output=True, text=True, timeout=300)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "dns_resolved_to": resolved_ip,
                        "certbot_stdout": result.stdout,
                        "certbot_stderr": result.stderr,
                        "returncode": result.returncode,
                        "success": result.returncode == 0
                    }, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"SSL setup failed: {str(e)}"
                )]

        elif name == "view_deployment_logs":
            import subprocess

            vps_host = arguments["vps_host"]
            ssh_user = arguments.get("ssh_user", "root")
            lines = arguments.get("lines", 100)

            ssh_cmd = f"ssh {ssh_user}@{vps_host}"
            log_cmd = f"{ssh_cmd} 'journalctl -u contractor-portal -n {lines} --no-pager'"

            try:
                result = subprocess.run(log_cmd, shell=True, capture_output=True, text=True, timeout=30)
                return [TextContent(
                    type="text",
                    text=result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Failed to retrieve logs: {str(e)}"
                )]

        elif name == "restart_application":
            import subprocess

            vps_host = arguments["vps_host"]
            ssh_user = arguments.get("ssh_user", "root")

            ssh_cmd = f"ssh {ssh_user}@{vps_host}"
            restart_cmd = f"{ssh_cmd} 'systemctl restart contractor-portal && systemctl status contractor-portal --no-pager'"

            try:
                result = subprocess.run(restart_cmd, shell=True, capture_output=True, text=True, timeout=30)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                        "success": result.returncode == 0
                    }, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Restart failed: {str(e)}"
                )]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {str(e)}"
        )]

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="contractor-portal-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
