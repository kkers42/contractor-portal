# Hostinger VPS Deployment Guide - BETA

This guide will walk you through deploying the Contractor Portal to Hostinger VPS.

## Prerequisites

1. **Hostinger VPS**: Active VPS hosting account
2. **Domain Name**: Your custom domain (configured in Hostinger)
3. **SSH Access**: Root or sudo access to your VPS
4. **GitHub Access**: Ability to clone the repository

## Quick Start

### Step 1: Connect to Your Hostinger VPS

```bash
ssh root@your-vps-ip-address
```

Or use the Hostinger panel's built-in SSH terminal.

### Step 2: Download and Run Deployment Script

```bash
# Download the deployment script
curl -O https://raw.githubusercontent.com/kkers42/contractor-portal/beta/deploy-to-hostinger.sh

# Make it executable
chmod +x deploy-to-hostinger.sh

# Edit configuration variables (IMPORTANT!)
nano deploy-to-hostinger.sh
```

**Update these variables in the script:**
- `DOMAIN="your-domain.com"` - Your actual domain name
- `DB_PASS` - Choose a secure database password

### Step 3: Run the Deployment

```bash
./deploy-to-hostinger.sh
```

The script will automatically:
- Update system packages
- Install Python, MySQL, Nginx
- Clone the repository (beta branch)
- Set up virtual environment
- Install dependencies
- Configure database
- Create systemd service
- Configure Nginx reverse proxy

### Step 4: Configure DNS

In your Hostinger domain management panel:

1. Go to **DNS/Name Servers**
2. Add/Update A Record:
   - **Type**: A
   - **Name**: @ (for root domain)
   - **Points to**: Your VPS IP address
   - **TTL**: 3600

3. Add/Update A Record for www:
   - **Type**: A
   - **Name**: www
   - **Points to**: Your VPS IP address
   - **TTL**: 3600

Wait 5-30 minutes for DNS propagation.

### Step 5: Enable SSL Certificate

Once DNS is configured, run:

```bash
certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts and select option 2 (redirect HTTP to HTTPS).

## Post-Deployment Configuration

### Claude Code MCP Integration

The application includes MCP (Model Context Protocol) support. To configure:

1. **Check MCP Server Status**:
```bash
systemctl status contractor-portal
journalctl -u contractor-portal -f
```

2. **MCP Configuration**:
The MCP server runs on port 8080 alongside the main application. Configure your Claude Code client:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "url": "https://your-domain.com/mcp",
      "transport": "sse"
    }
  }
}
```

3. **Available MCP Tools**:
   - `get-properties`: List all properties
   - `get-contractors`: List all contractors
   - `get-logs`: Retrieve service logs
   - `create-property`: Add new property
   - `create-contractor`: Add new contractor

### Environment Variables

Update the `.env` file in `/opt/contractor-portal`:

```bash
nano /opt/contractor-portal/.env
```

**Required updates:**
- `EMAIL_USER`: Your Gmail address for notifications
- `EMAIL_PASSWORD`: App-specific password (not your Gmail password)
- `BACKDOOR_ADMIN_PASSWORD`: Change from default

**Optional OAuth (recommended):**
- `GOOGLE_CLIENT_ID`: For Google SSO
- `GOOGLE_CLIENT_SECRET`: For Google SSO

After changes, restart the service:
```bash
systemctl restart contractor-portal
```

### Email Configuration (Gmail)

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification (enable if not already)
3. Security → App passwords
4. Generate new app password for "Mail"
5. Copy the 16-character password to `.env` as `EMAIL_PASSWORD`

## Useful Commands

### Service Management
```bash
# Check application status
systemctl status contractor-portal

# View real-time logs
journalctl -u contractor-portal -f

# Restart application
systemctl restart contractor-portal

# Stop application
systemctl stop contractor-portal
```

### Database Access
```bash
# Connect to MySQL
mysql -u contractor -p contractor_portal

# Backup database
mysqldump -u contractor -p contractor_portal > backup-$(date +%Y%m%d).sql

# Restore database
mysql -u contractor -p contractor_portal < backup-file.sql
```

### Update Application
```bash
cd /opt/contractor-portal
git pull origin beta
source venv/bin/activate
pip install -r requirements.txt
systemctl restart contractor-portal
```

### Nginx Management
```bash
# Test Nginx configuration
nginx -t

# Reload Nginx
systemctl reload nginx

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Firewall Configuration

Ensure these ports are open:
- **80**: HTTP (will redirect to HTTPS)
- **443**: HTTPS
- **22**: SSH (for management)

```bash
# Using UFW (Ubuntu Firewall)
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

## Troubleshooting

### Application Won't Start
```bash
# Check logs for errors
journalctl -u contractor-portal -n 100 --no-pager

# Verify Python environment
cd /opt/contractor-portal
source venv/bin/activate
python main.py
```

### Database Connection Issues
```bash
# Test database connection
mysql -u contractor -p -h 127.0.0.1 contractor_portal

# Check MySQL status
systemctl status mysql
```

### DNS Not Resolving
```bash
# Check DNS propagation
nslookup your-domain.com
dig your-domain.com

# Verify Nginx is listening
netstat -tlnp | grep nginx
```

### SSL Certificate Issues
```bash
# Renew certificate manually
certbot renew --dry-run

# Check certificate status
certbot certificates
```

## Security Recommendations

1. **Change Default Passwords**: Update all passwords in `.env`
2. **Enable Firewall**: Use UFW or iptables
3. **Regular Updates**: Keep system packages updated
4. **Backup Strategy**: Schedule regular database backups
5. **Monitor Logs**: Set up log monitoring/alerting
6. **Disable Root SSH**: Use a dedicated user with sudo

## Support & Resources

- **GitHub Repository**: https://github.com/kkers42/contractor-portal
- **Branch**: beta
- **Issues**: Report bugs on GitHub Issues tab

## Architecture Overview

```
Internet → Cloudflare (optional) → Nginx (80/443) → FastAPI (8080) → MySQL (3306)
                                                  └→ MCP Server
```

- **Web Server**: Nginx (reverse proxy + SSL)
- **Application**: FastAPI + Uvicorn
- **Database**: MySQL 8.0
- **Process Manager**: systemd
- **SSL**: Let's Encrypt (via Certbot)

## Next Steps After Deployment

1. **Test Login**: Visit `https://your-domain.com`
2. **Admin Access**: Use backdoor credentials from `.env`
3. **Add Users**: Import users via admin panel
4. **Configure OAuth**: Set up Google SSO (optional)
5. **Test MCP**: Connect Claude Code to the MCP endpoint
6. **Monitor**: Check logs and service status regularly

---

**Deployment Date**: November 2025
**Version**: Beta
**Last Updated**: Check GitHub for latest changes
