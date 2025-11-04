#!/bin/bash
# Deployment script for contractor portal fixes
# Run this on the server: bash deploy.sh

set -e  # Exit on any error

echo "======================================"
echo "Contractor Portal Deployment"
echo "======================================"
echo ""

# Navigate to application directory
cd /opt/contractor-portal

echo "[1/7] Pulling latest changes from GitHub..."
git pull origin feature/passwordless-sso

echo ""
echo "[2/7] Running locations table migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_locations_table.sql

echo ""
echo "[3/7] Running unique address constraint migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_add_unique_address_constraint.sql

echo ""
echo "[4/7] Running winter ops logs table migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_winter_ops_logs.sql

echo ""
echo "[5/7] Running green services logs table migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_green_services_logs.sql

echo ""
echo "[6/7] Running product tables migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_product_tables.sql

echo ""
echo "[7/8] Adding equipment field to winter_ops_logs..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_add_equipment_to_winter_ops.sql

echo ""
echo "[8/8] Restarting contractor-portal service..."
sudo systemctl restart contractor-portal

echo ""
echo "======================================"
echo "Deployment complete!"
echo "======================================"
echo ""
echo "Service status:"
sudo systemctl status contractor-portal --no-pager -l

echo ""
echo "Recent logs:"
sudo journalctl -u contractor-portal -n 20 --no-pager

echo ""
echo "All fixes deployed successfully!"
echo "- Property edit/delete now working"
echo "- Winter ops log submissions now working"
echo "- Add user from admin dashboard now working"
echo "- Product tables (winter & landscape) now available"
