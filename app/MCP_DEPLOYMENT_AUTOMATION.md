# MCP Deployment Automation Guide

This guide explains how to use Claude Code's MCP integration to **automatically deploy** your Contractor Portal to Hostinger VPS.

## What This Does

Instead of manually SSHing into your server and running deployment scripts, Claude Code can now:

1. **Deploy the application** automatically via SSH
2. **Check deployment status** and troubleshoot issues
3. **Generate DNS configuration** instructions
4. **Set up SSL certificates** automatically
5. **View logs** from the VPS in real-time
6. **Restart the application** remotely

All through simple conversational commands!

## Setup

### 1. Install MCP Server Locally

The MCP server is already included in your project at `contractor_mcp/server.py`.

Install required dependencies:

```bash
cd r:\Contractor App\app
pip install mcp python-dotenv mysql-connector-python
```

### 2. Configure Claude Code MCP Client

Create or edit your Claude Code MCP configuration file:

**Windows**: `%USERPROFILE%\.claude\mcp_config.json`
**macOS/Linux**: `~/.claude/mcp_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": [
        "r:\\Contractor App\\app\\contractor_mcp\\server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 3. Set Up SSH Keys (Required for Deployment)

The MCP deployment tools use SSH to connect to your Hostinger VPS. You need SSH key authentication configured:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy your public key to the VPS
ssh-copy-id root@your-vps-ip

# Test connection
ssh root@your-vps-ip "echo 'SSH connection successful'"
```

### 4. Restart Claude Code

After configuring MCP, restart Claude Code to load the new server.

## Usage Examples

Once configured, you can use natural language commands in Claude Code:

### Deploy to Hostinger

```
Deploy the contractor portal to my Hostinger VPS at 123.45.67.89
using domain myapp.com and database password MySecurePass123!
```

Claude Code will call the `deploy_to_hostinger` MCP tool with:
- vps_host: 123.45.67.89
- domain: myapp.com
- db_password: MySecurePass123!

### Check Deployment Status

```
Check the status of my contractor portal deployment on 123.45.67.89
```

This will show:
- Application service status
- Nginx status
- MySQL status
- Disk space
- Recent logs
- Listening ports

### Configure DNS

```
Generate DNS configuration for myapp.com pointing to 123.45.67.89
```

Returns step-by-step instructions for configuring DNS in Hostinger control panel.

### Set Up SSL

```
Set up SSL certificate for myapp.com on VPS 123.45.67.89
using email admin@myapp.com
```

Automatically runs Let's Encrypt certbot to install SSL certificate.

### View Logs

```
Show me the last 50 lines of logs from my deployed application on 123.45.67.89
```

### Restart Application

```
Restart the contractor portal application on 123.45.67.89
```

## Available MCP Tools

### 1. deploy_to_hostinger

**Description**: Fully automated deployment to Hostinger VPS

**Parameters**:
- `vps_host` (required): VPS IP address
- `domain` (required): Domain name for the app
- `db_password` (required): MySQL password to set
- `ssh_user` (optional): SSH username (default: root)
- `ssh_key_path` (optional): Path to SSH private key

**Example**:
```
Use the deploy_to_hostinger tool with:
- vps_host: 123.45.67.89
- domain: contractorapp.com
- db_password: SecurePassword123!
```

**What it does**:
1. Downloads deployment script from GitHub beta branch
2. Updates script with your domain and password
3. Runs full deployment (installs Python, MySQL, Nginx, etc.)
4. Clones repository and sets up application
5. Configures systemd service
6. Sets up Nginx reverse proxy

**Duration**: 10-15 minutes

### 2. check_deployment_status

**Description**: Check health of deployed application

**Parameters**:
- `vps_host` (required): VPS IP address
- `ssh_user` (optional): SSH username

**Returns**:
- Service statuses (app, nginx, mysql)
- Disk space usage
- Recent application logs
- Network ports in use

### 3. configure_dns

**Description**: Generate DNS configuration instructions

**Parameters**:
- `domain` (required): Domain name
- `vps_ip` (required): VPS IP address

**Returns**: JSON with step-by-step DNS setup instructions for Hostinger panel

### 4. setup_ssl

**Description**: Automatically set up SSL certificate via Let's Encrypt

**Parameters**:
- `vps_host` (required): VPS IP address
- `domain` (required): Domain name
- `email` (required): Email for Let's Encrypt notifications
- `ssh_user` (optional): SSH username

**Prerequisites**: DNS must be configured and propagated first!

### 5. view_deployment_logs

**Description**: View application logs from VPS

**Parameters**:
- `vps_host` (required): VPS IP address
- `lines` (optional): Number of lines to retrieve (default: 100)
- `ssh_user` (optional): SSH username

### 6. restart_application

**Description**: Restart the contractor portal service

**Parameters**:
- `vps_host` (required): VPS IP address
- `ssh_user` (optional): SSH username

## Complete Deployment Workflow

Here's the full workflow using Claude Code with MCP:

### Step 1: Deploy Application
```
Deploy contractor portal to VPS 123.45.67.89 with domain myapp.com
and database password MySecureDB123!
```

**Wait**: 10-15 minutes for deployment to complete.

### Step 2: Configure DNS
```
Generate DNS configuration for myapp.com pointing to 123.45.67.89
```

Follow the instructions to configure DNS in Hostinger control panel.

**Wait**: 10-30 minutes for DNS propagation.

### Step 3: Verify DNS
```
Check if DNS for myapp.com has propagated
```

Or manually: `dig myapp.com` or `nslookup myapp.com`

### Step 4: Set Up SSL
```
Set up SSL for myapp.com on VPS 123.45.67.89 using email admin@myapp.com
```

### Step 5: Verify Deployment
```
Check deployment status on 123.45.67.89
```

### Step 6: Test Application
Visit: `https://myapp.com`

Default login:
- Email: `admin@contractor.local`
- Password: `ContractorAdmin2025!`

**IMPORTANT**: Change this password immediately after first login!

## Troubleshooting

### SSH Connection Fails

**Error**: `Permission denied (publickey)`

**Solution**:
```bash
# Ensure SSH key is added
ssh-add ~/.ssh/id_ed25519

# Or specify key path in deployment
ssh_key_path: /path/to/your/private/key
```

### Deployment Script Times Out

**Cause**: VPS is slow or has network issues

**Solution**:
- Check VPS performance in Hostinger panel
- Try deployment again (script is idempotent)
- SSH manually and run: `journalctl -u contractor-portal -f`

### SSL Setup Fails

**Error**: DNS not resolved

**Solution**:
- Verify DNS with: `dig yourdomain.com`
- Wait longer for DNS propagation
- Check DNS records in Hostinger panel

### Application Won't Start

**Check logs**:
```
Show logs from deployment on 123.45.67.89
```

**Common issues**:
- Database connection failed (check .env file)
- Port 8080 already in use
- Python dependencies missing

**SSH manually**:
```bash
ssh root@123.45.67.89
journalctl -u contractor-portal -f
systemctl status contractor-portal
```

## Security Considerations

### SSH Key Security
- Never share your private SSH key
- Use passphrase-protected keys
- Use `ssh-agent` to manage keys securely

### Database Passwords
- Use strong passwords (16+ characters)
- Mix uppercase, lowercase, numbers, symbols
- Never reuse passwords

### MCP Tool Access
- MCP server runs locally with your user permissions
- Can execute SSH commands on your behalf
- Only give VPS IP to trusted parties

### VPS Security
After deployment:
```bash
# Enable firewall
ssh root@your-vps "ufw enable"

# Change default passwords
ssh root@your-vps "nano /opt/contractor-portal/.env"

# Set up fail2ban (SSH protection)
ssh root@your-vps "apt install fail2ban -y"
```

## Advanced Usage

### Custom SSH Port

If your VPS uses a non-standard SSH port:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": ["r:\\Contractor App\\app\\contractor_mcp\\server.py"],
      "env": {
        "SSH_PORT": "2222"
      }
    }
  }
}
```

Then modify SSH commands to use `-p 2222`.

### Multiple Environments

Deploy to different environments:

```
Deploy to staging VPS at 10.0.0.5 with domain staging.myapp.com
Deploy to production VPS at 123.45.67.89 with domain myapp.com
```

### Automated Updates

Schedule updates via Claude Code:

```
Update the application on VPS 123.45.67.89
```

Creates a script that:
1. Pulls latest code from GitHub beta branch
2. Installs dependencies
3. Runs migrations
4. Restarts application

## MCP Server Development

The MCP server is in `contractor_mcp/server.py`.

To add new deployment tools:

1. Add tool definition in `handle_list_tools()`
2. Add implementation in `handle_call_tool()`
3. Update this documentation
4. Restart Claude Code

Example - Add backup tool:

```python
Tool(
    name="backup_database",
    description="Backup MySQL database from VPS",
    inputSchema={
        "type": "object",
        "properties": {
            "vps_host": {"type": "string"},
            "backup_name": {"type": "string"}
        },
        "required": ["vps_host"]
    }
)
```

## Testing MCP Tools

Test MCP tools without Claude Code:

```bash
cd r:\Contractor App\app
python contractor_mcp/test_server.py
```

Or manually:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python contractor_mcp/server.py
```

## Benefits of MCP Deployment

### vs Manual SSH
- ✅ No need to remember commands
- ✅ Automated error handling
- ✅ Consistent deployments
- ✅ Natural language interface

### vs CI/CD (GitHub Actions)
- ✅ No complex YAML configuration
- ✅ Interactive troubleshooting
- ✅ On-demand deployments
- ✅ Easier for small teams

### vs Deployment Platforms (Heroku, Vercel)
- ✅ Full control over VPS
- ✅ Lower cost
- ✅ No vendor lock-in
- ✅ Custom configurations

## Monitoring Post-Deployment

After successful deployment, set up monitoring:

1. **Application Logs**:
```
Show me the last 100 logs from 123.45.67.89
```

2. **Service Status**:
```
Check deployment status on 123.45.67.89
```

3. **Database Backups**:
```bash
ssh root@vps-ip "mysqldump -u contractor -p contractor_portal > backup-$(date +%Y%m%d).sql"
```

4. **SSL Certificate Renewal**:
Certbot auto-renews, but check:
```bash
ssh root@vps-ip "certbot certificates"
```

## Next Steps

After successful deployment:

1. ✅ Change default admin password
2. ✅ Configure email settings (Gmail app password)
3. ✅ Set up OAuth (Google SSO) - optional
4. ✅ Add users and properties
5. ✅ Test all features
6. ✅ Set up automated backups
7. ✅ Configure monitoring/alerting

---

**Ready to deploy?**

Just tell Claude Code:
```
Deploy the contractor portal to Hostinger VPS [your-ip]
with domain [your-domain.com] and database password [secure-password]
```

Claude Code + MCP will handle the rest!
