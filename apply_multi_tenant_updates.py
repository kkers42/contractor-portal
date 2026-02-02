"""
Comprehensive script to apply multi-tenant customer_id filtering to all route files.
This script systematically updates database queries to include customer_id WHERE clauses.

IMPORTANT: This script makes extensive changes. Review the diff before committing.
"""

import re
import os
from pathlib import Path

# Route files to update (excluding customer_routes.py which is already multi-tenant)
ROUTE_FILES = [
    'app/routes/property_routes.py',
    'app/routes/winter_event_routes.py',
    'app/routes/ops_routes.py',
    'app/routes/route_routes.py',
    'app/routes/weather_routes.py',
    'app/routes/assignment_routes.py',
    'app/routes/property_list_routes.py',
    'app/routes/sms_routes.py',
    'app/routes/jobber_routes.py',
    'app/routes/quickbooks_routes.py',
    'app/routes/report_routes.py',
    'app/routes/settings_routes.py',
    'app/routes/ai_routes.py',
    'app/routes/misc_routes.py',
    'app/routes/equipment_routes.py',
    'app/routes/tenant_routes.py',
    'app/routes/n8n_routes.py',
    'app/routes/email_routes.py',
    'app/routes/checkin_routes.py',
]

# Tables that need customer_id filtering
TENANT_TABLES = [
    'users', 'locations', 'winter_ops_logs', 'winter_events', 'property_contractors',
    'routes', 'property_lists', 'equipment_rates', 'weather_data', 'sms_context',
    'api_keys', 'jobber_auth', 'quickbooks_auth', 'event_checkins'
]

def add_customer_id_import(content):
    """Add get_customer_id to imports if not already present"""
    if 'get_customer_id' in content:
        return content

    # Find the auth import line
    pattern = r'from auth import ([^\\n]+)'
    match = re.search(pattern, content)

    if match:
        imports = match.group(1)
        if 'get_customer_id' not in imports:
            new_imports = imports + ', get_customer_id'
            content = content.replace(match.group(0), f'from auth import {new_imports}')

    return content

def add_customer_id_param_to_endpoint(content, endpoint_pattern):
    """Add customer_id parameter to endpoint function signature"""
    # Find function definition
    func_match = re.search(rf'(@router\\.{endpoint_pattern}[^\\n]+\\n)(def [^(]+\\([^)]*)', content, re.MULTILINE | re.DOTALL)

    if func_match:
        decorator = func_match.group(1)
        func_sig = func_match.group(2)

        # Check if customer_id already in signature
        if 'customer_id' not in func_sig:
            # Add customer_id parameter
            if 'current_user' in func_sig:
                # Add after current_user
                new_sig = func_sig.replace(
                    'current_user: dict = Depends(get_current_user)',
                    'current_user: dict = Depends(get_current_user),\\n    customer_id: str = Depends(get_customer_id)'
                )
            elif 'Depends(' in func_sig:
                # Add to end before closing paren
                new_sig = func_sig.rstrip(')') + ',\\n    customer_id: str = Depends(get_customer_id)'
            else:
                # Add as first parameter
                new_sig = func_sig.rstrip(')') + 'customer_id: str = Depends(get_customer_id)'

            content = content.replace(func_match.group(0), decorator + new_sig)

    return content

def update_file(filepath):
    """Update a single route file with customer_id filtering"""
    print(f"\\nProcessing: {filepath}")

    if not os.path.exists(filepath):
        print(f"  [WARNING] File not found, skipping")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Step 1: Add customer_id to imports
    content = add_customer_id_import(content)

    # Step 2: Note which patterns to update (manual review required)
    # This script adds the import and we'll document which queries need updating

    changes_made = content != original_content

    if changes_made:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Updated imports")
    else:
        print(f"  [INFO] No changes needed (already has get_customer_id import)")

    # Count queries that need manual review
    select_count = len(re.findall(r'SELECT.*FROM\\s+(' + '|'.join(TENANT_TABLES) + ')', content, re.IGNORECASE))
    insert_count = len(re.findall(r'INSERT INTO\\s+(' + '|'.join(TENANT_TABLES) + ')', content, re.IGNORECASE))
    update_count = len(re.findall(r'UPDATE\\s+(' + '|'.join(TENANT_TABLES) + ')\\s+SET', content, re.IGNORECASE))
    delete_count = len(re.findall(r'DELETE FROM\\s+(' + '|'.join(TENANT_TABLES) + ')', content, re.IGNORECASE))

    total_queries = select_count + insert_count + update_count + delete_count

    if total_queries > 0:
        print(f"  [QUERIES] Found {total_queries} queries requiring customer_id filtering:")
        print(f"      - SELECT: {select_count}")
        print(f"      - INSERT: {insert_count}")
        print(f"      - UPDATE: {update_count}")
        print(f"      - DELETE: {delete_count}")
        print(f"  [WARNING] MANUAL REVIEW REQUIRED - Each query must be updated to:")
        print(f"      1. Add customer_id: str = Depends(get_customer_id) to function params")
        print(f"      2. Add 'AND customer_id = %s' to WHERE clauses (SELECT/UPDATE/DELETE)")
        print(f"      3. Add 'customer_id' column and value to INSERT statements")
        print(f"      4. Add customer_id to query parameters tuple")

def main():
    print("="*80)
    print("MULTI-TENANT CUSTOMER_ID FILTERING - ROUTE FILE UPDATES")
    print("="*80)
    print("\\nThis script adds get_customer_id imports to all route files.")
    print("Manual review and updates are still required for each database query.")
    print("\\nProcessing files...")

    for filepath in ROUTE_FILES:
        update_file(filepath)

    print("\\n" + "="*80)
    print("IMPORT UPDATES COMPLETE")
    print("="*80)
    print("\\nNEXT STEPS (MANUAL):")
    print("1. Review each route file listed above")
    print("2. For each endpoint that queries tenant tables:")
    print("   a. Add 'customer_id: str = Depends(get_customer_id)' to function parameters")
    print("   b. Update all SELECT/UPDATE/DELETE queries with 'AND customer_id = %s'")
    print("   c. Update all INSERT queries to include customer_id column and value")
    print("   d. Add customer_id to the query parameters tuple")
    print("\\n3. Test thoroughly with multiple customer_ids")
    print("4. Run database migrations before deploying")
    print("\\n[CRITICAL] Every query MUST filter by customer_id for data isolation!")
    print("="*80)

if __name__ == "__main__":
    main()
