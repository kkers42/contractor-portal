#!/bin/bash
# Deployment script for Contractor Portal on Hostinger VPS
# Run this on your VPS after connecting via SSH

set -e  # Exit on any error

echo "=========================================="
echo "Contractor Portal Deployment Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/contractor-portal"
DOMAIN="your-domain.com"  # Update this with your actual domain
DB_NAME="contractor_portal"
DB_USER="contractor"
DB_PASS="Bimmer325!"

echo -e "${YELLOW}[1/11] Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}[2/11] Installing required packages...${NC}"
apt install -y python3 python3-pip python3-venv git mysql-server nginx certbot python3-certbot-nginx

echo -e "${YELLOW}[3/11] Creating application directory...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

echo -e "${YELLOW}[4/11] Cloning repository from GitHub...${NC}"
if [ -d ".git" ]; then
    echo "Repository already exists, pulling latest changes..."
    git pull origin feature/passwordless-sso
else
    git clone https://github.com/kkers42/contractor-portal.git .
    git checkout feature/passwordless-sso
fi

echo -e "${YELLOW}[5/11] Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[6/11] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${YELLOW}[7/11] Configuring MySQL database...${NC}"
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo -e "${YELLOW}[8/11] Creating .env file...${NC}"
cat > .env <<EOF
# Database Configuration
DB_HOST=127.0.0.1
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASS
DB_NAME=$DB_NAME

# JWT Configuration
SECRET_KEY=$(openssl rand -hex 32)
APP_JWT_SECRET=$(openssl rand -hex 32)
APP_JWT_EXP_MIN=120

# Email Configuration (update these)
EMAIL_USER=contractorappdev@gmail.com
EMAIL_PASSWORD=your_email_password

# OAuth Configuration
APP_BASE_URL=https://$DOMAIN
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MS_TENANT=common
MS_CLIENT_ID=
MS_CLIENT_SECRET=

# Backdoor Admin Access
BACKDOOR_ADMIN_EMAIL=admin@contractor.local
BACKDOOR_ADMIN_PASSWORD=ContractorAdmin2025!
EOF

echo -e "${YELLOW}[9/11] Running database migrations...${NC}"
# Create initial tables
mysql -u $DB_USER -p$DB_PASS $DB_NAME < db/schema.sql 2>/dev/null || echo "Schema already exists"

# Run migrations in order
for migration in db/migrations/*.sql; do
    if [ -f "$migration" ]; then
        echo "Running migration: $(basename $migration)"
        mysql -u $DB_USER -p$DB_PASS $DB_NAME < "$migration" 2>/dev/null || echo "Migration already applied or failed"
    fi
done

echo -e "${YELLOW}[10/11] Creating systemd service...${NC}"
cat > /etc/systemd/system/contractor-portal.service <<EOF
[Unit]
Description=Contractor Portal FastAPI Application
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable contractor-portal
systemctl restart contractor-portal

echo -e "${YELLOW}[11/11] Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/contractor-portal <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/contractor-portal /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t && systemctl reload nginx

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update domain DNS to point to: 72.61.0.186"
echo "2. Set up SSL certificate:"
echo "   certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""
echo "3. Configure Google OAuth (optional):"
echo "   - Edit .env file and add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
echo "   - Restart service: systemctl restart contractor-portal"
echo ""
echo "4. Check application status:"
echo "   systemctl status contractor-portal"
echo ""
echo "5. View logs:"
echo "   journalctl -u contractor-portal -f"
echo ""
echo "Application should be running at: http://$DOMAIN"
echo ""
