#!/usr/bin/env python3
"""
Run Phase 1 SAAS Migrations
This script applies the Phase 1 multi-tenancy database changes
"""

import sys
import os

# Add parent directory to path to import db module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import execute_query, fetch_query

def run_migration(filename):
    """Run a single migration file"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    print(f"\n{'='*60}")
    print(f"Running migration: {filename}")
    print(f"{'='*60}\n")

    with open(filepath, 'r') as f:
        sql = f.read()

    # Split into individual statements
    statements = []
    current_stmt = []

    for line in sql.split('\n'):
        # Skip pure comment lines
        if line.strip().startswith('--'):
            continue

        current_stmt.append(line)

        # If line ends with semicolon, it's end of statement
        if line.strip().endswith(';'):
            stmt = '\n'.join(current_stmt).strip()
            if stmt:
                statements.append(stmt)
            current_stmt = []

    # Execute each statement
    for i, stmt in enumerate(statements, 1):
        # Show first 100 chars of statement
        preview = stmt.replace('\n', ' ').strip()
        if len(preview) > 100:
            preview = preview[:97] + '...'

        print(f"{i}. Executing: {preview}")

        try:
            execute_query(stmt)
            print(f"   ✓ Success\n")
        except Exception as e:
            error_msg = str(e)

            # These errors are OK - column/constraint already exists
            if any(x in error_msg.lower() for x in [
                'already exists',
                'duplicate column',
                'duplicate key',
                'duplicate entry'
            ]):
                print(f"   ⚠ Already exists (skipping): {error_msg}\n")
                continue
            else:
                print(f"   ✗ ERROR: {error_msg}\n")
                raise

def main():
    print("\n" + "="*60)
    print("Phase 1 SAAS Multi-Tenancy Migration")
    print("="*60)

    try:
        # Step 1: Create tenants table
        run_migration('phase1_create_tenants.sql')

        # Step 2: Add tenant_id to all tables
        run_migration('phase1_add_tenant_id.sql')

        print("\n" + "="*60)
        print("✓ All migrations completed successfully!")
        print("="*60)

        # Verify tenant exists
        result = fetch_query("SELECT * FROM tenants WHERE id = 1")
        if result:
            print(f"\n✓ Default tenant verified:")
            print(f"  Company: {result[0]['company_name']}")
            print(f"  Subdomain: {result[0]['subdomain']}")
            print(f"  Max Users: {result[0]['max_users']}")
            print(f"  Max Properties: {result[0]['max_properties']}")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
