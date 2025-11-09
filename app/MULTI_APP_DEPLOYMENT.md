# Deploying Contractor Portal Alongside Existing Apps (n8n, etc.)

This guide explains how to deploy the Contractor Portal on a VPS that's already running other applications like n8n.

## Your Current Setup

You have:
- **VPS**: Already running with apps
- **n8n**: Running on existing domain (e.g., `n8n.yourdomain.com`)
- **New domain**: On GoDaddy for contractor portal (e.g., `contractorapp.com`)

## How It Works

Both apps will run on the same VPS using Nginx as a reverse proxy:

```
Internet
   ↓
Nginx (ports 80/443)
   ├─→ n8n.yourdomain.com → http://localhost:5678 (n8n)
   └─→ contractorapp.com → http://localhost:8080 (contractor portal)
```

Each app:
- Runs on its own port
- Has its own domain
- Has its own SSL certificate
- Operates independently

## Pre-Deployment Checklist

### 1. Check Current Nginx Configuration

SSH into your VPS and check existing sites:

```bash
ssh root@your-vps-ip
ls -la /etc/nginx/sites-enabled/
cat /etc/nginx/sites-enabled/*
```

Take note of:
- What port n8n is running on (probably 5678)
- What domain n8n is using
- Any other configured sites

### 2. Verify Available Ports

Check what ports are in use:

```bash
netstat -tlnp | grep LISTEN
```

The contractor portal uses port **8080**. Make sure it's available (it should be fine).

### 3. Configure Your GoDaddy Domain

In your GoDaddy account:

1. Go to DNS Management for your new domain
2. Add A Record:
   - **Type**: A
   - **Name**: @ (for root domain)
   - **Value**: Your VPS IP address
   - **TTL**: 600 (10 minutes)
3. Add A Record for www:
   - **Type**: A
   - **Name**: www
   - **Value**: Your VPS IP address
   - **TTL**: 600

**Note**: Since your domain is on GoDaddy (not Hostinger), the Hostinger API tools won't work for DNS. You'll configure DNS manually in GoDaddy (takes 2 minutes).

## Deployment Process

### Option 1: Using Claude Code MCP (Recommended)

Since your domain is on GoDaddy, use the SSH-only deployment (not the Hostinger API):

**Tell me:**
```
Deploy contractor portal to VPS [your-vps-ip] with domain [your-godaddy-domain]
and database password [secure-password]
```

I'll use the `deploy_to_hostinger` MCP tool which:
- ✅ Deploys the app on port 8080
- ✅ Creates separate Nginx config (doesn't touch n8n)
- ✅ Sets up systemd service
- ✅ Leaves existing apps untouched

Then after DNS propagates:
```
Set up SSL for [your-domain] on VPS [vps-ip] using email [your-email]
```

### Option 2: Manual Deployment

If you prefer to do it manually:

```bash
# SSH into VPS
ssh root@your-vps-ip

# Download deployment script
curl -O https://raw.githubusercontent.com/kkers42/contractor-portal/beta/deploy-to-hostinger.sh

# Edit configuration
nano deploy-to-hostinger.sh
# Update: DOMAIN="your-godaddy-domain.com"
# Update: DB_PASS="YourSecurePassword123!"

# Run deployment
chmod +x deploy-to-hostinger.sh
./deploy-to-hostinger.sh
```

The script will:
- Install to `/opt/contractor-portal`
- Run on port 8080
- Create separate Nginx config at `/etc/nginx/sites-available/contractor-portal`
- **NOT remove** existing Nginx configs

## Nginx Configuration

The deployment creates this configuration at `/etc/nginx/sites-available/contractor-portal`:

```nginx
server {
    listen 80;
    server_name your-godaddy-domain.com www.your-godaddy-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/contractor-portal/static;
        expires 30d;
    }
}
```

Your n8n configuration remains untouched in `/etc/nginx/sites-available/n8n` (or similar).

## SSL Setup

After DNS propagates (10-30 minutes), set up SSL for your new domain:

```bash
certbot --nginx -d your-godaddy-domain.com -d www.your-godaddy-domain.com
```

This will:
- Add SSL to the contractor portal
- **NOT affect** n8n's SSL certificate
- Both domains will have their own certificates

## Verification

### 1. Check Both Apps Are Running

```bash
# Check n8n
systemctl status n8n  # or whatever service name n8n uses

# Check contractor portal
systemctl status contractor-portal

# Check all listening ports
netstat -tlnp | grep -E ':(5678|8080|80|443)'
```

Expected output:
```
tcp   0.0.0.0:5678   LISTEN   1234/node     # n8n
tcp   0.0.0.0:8080   LISTEN   5678/python   # contractor portal
tcp   0.0.0.0:80     LISTEN   9012/nginx
tcp   0.0.0.0:443    LISTEN   9012/nginx
```

### 2. Check Nginx Configuration

```bash
# List all enabled sites
ls -la /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t

# View Nginx status
systemctl status nginx
```

### 3. Test Both Domains

```bash
# Test n8n domain
curl -I https://n8n.yourdomain.com
# Should return 200 OK

# Test contractor portal domain
curl -I http://your-godaddy-domain.com
# Should return 200 OK (or redirect to https after SSL)
```

### 4. Access Both Apps

- **n8n**: `https://n8n.yourdomain.com`
- **Contractor Portal**: `https://your-godaddy-domain.com` (after SSL)

## Troubleshooting

### Both Apps Don't Load

**Check Nginx status:**
```bash
systemctl status nginx
nginx -t
```

If Nginx fails to start, check logs:
```bash
tail -100 /var/log/nginx/error.log
```

Common issue: Port conflict. Make sure apps are on different ports.

### Contractor Portal Works, n8n Doesn't (or vice versa)

**Check individual services:**
```bash
systemctl status contractor-portal
systemctl status n8n

journalctl -u contractor-portal -n 50
journalctl -u n8n -n 50
```

**Check if apps are listening:**
```bash
netstat -tlnp | grep 8080  # contractor portal
netstat -tlnp | grep 5678  # n8n
```

### SSL Won't Install for New Domain

**Check DNS first:**
```bash
dig your-godaddy-domain.com
nslookup your-godaddy-domain.com
```

Must resolve to your VPS IP.

**Check port 80 is accessible:**
```bash
curl -I http://your-godaddy-domain.com
```

**If SSL fails:**
```bash
# View certbot logs
cat /var/log/letsencrypt/letsencrypt.log

# Try manual setup with verbose output
certbot --nginx -d your-godaddy-domain.com --verbose
```

### Nginx Configuration Conflict

If you get "duplicate server" or similar errors:

```bash
# Check for conflicts
nginx -t

# View all server blocks
grep -r "server_name" /etc/nginx/sites-enabled/

# Disable conflicting site temporarily
mv /etc/nginx/sites-enabled/conflicting-site /etc/nginx/sites-available/
nginx -t
systemctl reload nginx
```

## Resource Considerations

### RAM Usage

Typical usage per app:
- **n8n**: 200-400 MB
- **Contractor Portal**: 100-200 MB
- **Nginx**: 50-100 MB
- **MySQL**: 200-400 MB

**Minimum VPS**: 2GB RAM (for both apps + MySQL)
**Recommended**: 4GB RAM for comfortable operation

Check current usage:
```bash
free -h
htop  # or top
```

### Disk Space

Each app needs:
- **n8n**: ~500 MB
- **Contractor Portal**: ~300 MB
- **MySQL Database**: 100-500 MB (grows over time)

Check available space:
```bash
df -h
```

### Database

The contractor portal creates its own MySQL database (`contractor_portal`), separate from n8n's database. No conflicts.

Verify:
```bash
mysql -u root -p
SHOW DATABASES;
```

You should see:
- `n8n` (or whatever n8n uses)
- `contractor_portal` (new)

## Backups

Since you now have two apps, update your backup strategy:

```bash
# Backup n8n (method depends on n8n setup)
# Usually: Database + n8n data folder

# Backup contractor portal
mysqldump -u contractor -p contractor_portal > contractor_backup_$(date +%Y%m%d).sql
tar -czf contractor_files_$(date +%Y%m%d).tar.gz /opt/contractor-portal

# Backup Nginx configs
tar -czf nginx_configs_$(date +%Y%m%d).tar.gz /etc/nginx/sites-available/
```

## Performance Tips

### 1. Enable Nginx Caching

Edit `/etc/nginx/nginx.conf`:

```nginx
http {
    # Add cache configuration
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;

    # ... rest of config
}
```

### 2. Optimize MySQL

Add to `/etc/mysql/mysql.conf.d/mysqld.cnf`:

```ini
[mysqld]
innodb_buffer_pool_size = 512M  # Adjust based on available RAM
max_connections = 50
```

Restart MySQL:
```bash
systemctl restart mysql
```

### 3. Monitor Resources

Install monitoring:
```bash
apt install htop iotop

# Real-time monitoring
htop
```

Set up alerts for high resource usage.

## Updates

### Updating Contractor Portal

```bash
cd /opt/contractor-portal
git pull origin beta
source venv/bin/activate
pip install -r requirements.txt
systemctl restart contractor-portal
```

This won't affect n8n.

### Updating n8n

Follow n8n's update procedure. This won't affect the contractor portal.

## Firewall Configuration

Make sure these ports are open:

```bash
# Using UFW
ufw allow 22      # SSH
ufw allow 80      # HTTP (for both apps)
ufw allow 443     # HTTPS (for both apps)
ufw enable

# Check status
ufw status
```

Ports 5678 (n8n) and 8080 (contractor portal) should NOT be exposed directly - only accessible through Nginx.

## Cost Considerations

Running both apps on one VPS:
- **VPS Cost**: ~$10-20/month (2-4GB RAM)
- **Domain Cost**: ~$15/year (GoDaddy)
- **SSL Certificates**: Free (Let's Encrypt)

**Total**: ~$10-20/month + domain

vs. separate hosting:
- n8n VPS: $10/month
- Contractor portal VPS: $10/month
- **Total**: $20/month + domains

**Savings**: $0-10/month by sharing VPS

## Summary

✅ **Safe to deploy** - Contractor portal won't interfere with n8n
✅ **Separate ports** - n8n (5678), contractor portal (8080)
✅ **Separate domains** - Each app has its own domain and SSL
✅ **Separate configs** - Independent Nginx configurations
✅ **Separate databases** - No database conflicts

## Deployment Command for Your Setup

Since your domain is on GoDaddy (not Hostinger), you'll:

1. **Configure DNS in GoDaddy** (2 minutes)
   - Add A records pointing to VPS IP

2. **Deploy via Claude Code** (without Hostinger API):
   ```
   Deploy contractor portal to VPS [vps-ip] with domain [godaddy-domain]
   and database password [secure-password]
   ```

3. **Wait for DNS** (10-30 minutes)

4. **Set up SSL via Claude Code**:
   ```
   Set up SSL for [godaddy-domain] on VPS [vps-ip] using email [your-email]
   ```

That's it! Both apps will coexist peacefully. 🎉

---

**Ready to deploy?** Let me know your:
1. VPS IP address
2. GoDaddy domain name
3. Desired database password
4. Email for SSL

I'll handle the deployment while preserving your n8n setup!
