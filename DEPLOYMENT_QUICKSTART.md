# 🚀 Contractor Portal - Beta Deployment Quick Start

## One-Command Deployment

```bash
ssh root@your-hostinger-vps "curl -sL https://raw.githubusercontent.com/kkers42/contractor-portal/beta/deploy-to-hostinger.sh | bash"
```

## Step-by-Step (Recommended)

### 1️⃣ Before You Start

You'll need:
- ✅ Hostinger VPS access (root/sudo)
- ✅ Domain name configured
- ✅ VPS IP address
- ✅ 10-15 minutes

### 2️⃣ Connect to VPS

```bash
ssh root@your-vps-ip-address
```

### 3️⃣ Download & Edit Script

```bash
curl -O https://raw.githubusercontent.com/kkers42/contractor-portal/beta/deploy-to-hostinger.sh
nano deploy-to-hostinger.sh
```

**Change these lines:**
```bash
DOMAIN="your-actual-domain.com"  # Your domain
DB_PASS="YourSecurePassword123!" # Database password
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### 4️⃣ Run Deployment

```bash
chmod +x deploy-to-hostinger.sh
./deploy-to-hostinger.sh
```

Wait 5-10 minutes while it installs everything.

### 5️⃣ Configure DNS

In Hostinger control panel:
1. Go to **Domain** → **DNS/Nameservers**
2. Add A Record:
   - **Type**: A
   - **Name**: @
   - **Points to**: Your VPS IP
   - **TTL**: 3600
3. Add another A Record:
   - **Type**: A
   - **Name**: www
   - **Points to**: Your VPS IP
   - **TTL**: 3600

### 6️⃣ Enable SSL (After DNS Propagates)

Wait 10-30 minutes for DNS, then:

```bash
certbot --nginx -d your-domain.com -d www.your-domain.com
```

Choose option **2** (redirect HTTP to HTTPS)

### 7️⃣ Test Your Site

Visit: `https://your-domain.com`

**Default Login:**
- Email: `admin@contractor.local`
- Password: `ContractorAdmin2025!`

**⚠️ CHANGE THIS PASSWORD IMMEDIATELY!**

## 🔧 Post-Deployment

### Change Admin Password

```bash
nano /opt/contractor-portal/.env
```

Change this line:
```bash
BACKDOOR_ADMIN_PASSWORD=YourNewSecurePassword!
```

Then restart:
```bash
systemctl restart contractor-portal
```

### Configure Email (Optional but Recommended)

1. Get Gmail App Password:
   - Go to Google Account → Security
   - Enable 2-Step Verification
   - Create App Password (select "Mail")

2. Update .env:
```bash
nano /opt/contractor-portal/.env
```

Update:
```bash
EMAIL_USER=your-gmail@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
```

Restart:
```bash
systemctl restart contractor-portal
```

## 📱 Connect Claude Code MCP

### Get Your JWT Token

1. Log in to your portal
2. Open browser DevTools (F12)
3. Go to **Application** → **Local Storage**
4. Copy the value of `token`

### Configure Claude Code

Create/edit `~/.claude/mcp_servers.json`:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "url": "https://your-domain.com/mcp",
      "auth": {
        "type": "bearer",
        "token": "paste-your-jwt-token-here"
      }
    }
  }
}
```

### Test MCP Connection

In Claude Code, try:
```
Show me all properties in the contractor portal
```

## ⚡ Useful Commands

### Check Status
```bash
systemctl status contractor-portal
```

### View Logs
```bash
journalctl -u contractor-portal -f
```

### Restart Application
```bash
systemctl restart contractor-portal
```

### Update Application
```bash
cd /opt/contractor-portal
git pull origin beta
systemctl restart contractor-portal
```

### Backup Database
```bash
mysqldump -u contractor -p contractor_portal > backup-$(date +%Y%m%d).sql
```

### Test Database Connection
```bash
mysql -u contractor -p contractor_portal
```

## 🆘 Troubleshooting

### Site Not Loading
```bash
# Check if app is running
systemctl status contractor-portal

# Check Nginx
systemctl status nginx
nginx -t

# Check firewall
ufw status
```

### Database Errors
```bash
# Check MySQL
systemctl status mysql

# Test connection
mysql -u contractor -p -h 127.0.0.1 contractor_portal
```

### SSL Certificate Issues
```bash
# Check certificate
certbot certificates

# Renew manually
certbot renew
```

### Application Crashes
```bash
# View detailed logs
journalctl -u contractor-portal -n 100 --no-pager

# Check Python errors
cd /opt/contractor-portal
source venv/bin/activate
python main.py
```

## 📚 Full Documentation

- **Complete Guide**: [HOSTINGER_DEPLOYMENT_GUIDE.md](app/HOSTINGER_DEPLOYMENT_GUIDE.md)
- **MCP Setup**: [CLAUDE_MCP_SETUP.md](app/CLAUDE_MCP_SETUP.md)
- **Release Notes**: [BETA_RELEASE_NOTES.md](app/BETA_RELEASE_NOTES.md)

## 🔐 Security Checklist

After deployment, do these immediately:

- [ ] Change backdoor admin password
- [ ] Enable firewall: `ufw enable`
- [ ] Configure email notifications
- [ ] Set up automated backups
- [ ] Review application logs
- [ ] Test all functionality
- [ ] Enable fail2ban (SSH protection)
- [ ] Remove unnecessary services

## 🎯 What's Deployed

When deployment finishes, you have:

✅ FastAPI application on port 8080
✅ MySQL database configured
✅ Nginx reverse proxy (ports 80/443)
✅ SSL certificate (auto-renewing)
✅ Systemd service (auto-restart)
✅ MCP server for Claude Code
✅ Admin panel accessible
✅ All dependencies installed

## 🌐 URLs

- **Main Site**: https://your-domain.com
- **Login Page**: https://your-domain.com/static/login.html
- **Admin Panel**: https://your-domain.com/static/GreenOpsAdmin.html
- **MCP Health**: https://your-domain.com/health

## 💡 Tips

1. **DNS Propagation**: Can take 5-30 minutes, be patient
2. **SSL Before DNS**: Won't work, DNS must resolve first
3. **Logs Are Your Friend**: Always check logs when troubleshooting
4. **Backups**: Set up automated daily backups ASAP
5. **Security**: Change all default passwords immediately

## 🚨 Emergency Contacts

- **GitHub Issues**: https://github.com/kkers42/contractor-portal/issues
- **Hostinger Support**: Available in your control panel
- **Certbot Docs**: https://certbot.eff.org/

---

**Need help?** Check the full documentation or open a GitHub issue.

**Ready to go?** Start with step 1 above!
