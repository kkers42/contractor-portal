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

echo "[1/11] Pulling latest changes from GitHub..."
git pull origin feature/passwordless-sso

echo ""
echo "[2/11] Running locations table migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_locations_table.sql

echo ""
echo "[3/11] Running unique address constraint migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_add_unique_address_constraint.sql

echo ""
echo "[4/11] Running winter ops logs table migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_winter_ops_logs.sql

echo ""
echo "[5/11] Running green services logs table migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_green_services_logs.sql

echo ""
echo "[6/11] Running product tables migration..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_product_tables.sql

echo ""
echo "[7/11] Adding equipment field to winter_ops_logs..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_add_equipment_to_winter_ops.sql

echo ""
echo "[8/11] Adding contractor relationship to users..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_add_contractor_relationship.sql

echo ""
echo "[9/11] Adding contractor fields to winter_ops_logs..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_add_contractor_to_winter_ops.sql

echo ""
echo "[10/11] Creating equipment_rates table..."
mysql -u contractor -p'Bimmer325!' contractor_portal < db/migrations/2025-11-03_create_equipment_rates.sql

echo ""
echo "[11/11] Restarting contractor-portal service..."
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
echo "All updates deployed successfully!"
echo "- Contractor/Worker relationship structure implemented"
echo "- Equipment rates management system added"
echo "- Winter logs now track contractor + worker + equipment"
echo "- Equipment pricing displayed in log submission"
echo "- Reports updated to show contractor and worker columns"
