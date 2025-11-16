# MCP SSH Deployment Fix

## Problem
The MCP deployment tools (deploy_to_hostinger, check_deployment_status, etc.) are failing with returncode 255 because SSH authentication isn't configured.

## Solution

### Option 1: Use the Quick Update Script (IMMEDIATE - DO THIS NOW)

I've created `quick-update.bat` in your project root. Simply run:

```batch
quick-update.bat
```

This will:
1. SSH to your VPS (using your existing SSH keys)
2. Pull latest changes from git beta branch
3. Restart the contractor-portal service
4. Show you the status

### Option 2: Configure SSH Keys for MCP (For Full Automation)

To enable the MCP deployment tools to work automatically, you need to configure SSH keys in the MCP environment:

#### Step 1: Locate Your SSH Keys

Your SSH private key is likely at:
- Windows: `C:\Users\YourUsername\.ssh\id_rsa` or `id_ed25519`
- The key you use to connect to root@72.61.0.186

#### Step 2: Update MCP Configuration

Edit your Claude Desktop config:
**Location**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the SSH key path:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": [
        "R:\\Contractor App\\app\\contractor_mcp\\server.py"
      ],
      "env": {
        "DB_HOST": "127.0.0.1",
        "DB_USER": "root",
        "DB_PASSWORD": "Bimmer325!",
        "DB_NAME": "contractor_portal",
        "APP_BASE_URL": "http://localhost:8080",
        "SSH_KEY_PATH": "C:\\Users\\YourUsername\\.ssh\\id_rsa",
        "VPS_HOST": "72.61.0.186",
        "VPS_USER": "root",
        "DOMAIN": "snow-contractor.com"
      }
    }
  }
}
```

Replace:
- `YourUsername` with your Windows username
- `id_rsa` with your actual key filename if different

#### Step 3: Update MCP Server Code

The MCP server needs to be modified to use the SSH_KEY_PATH environment variable. I'll create an updated version:

```python
# In contractor_mcp/server.py, update the SSH command building:
ssh_key_path = arguments.get("ssh_key_path") or os.getenv('SSH_KEY_PATH')
if ssh_key_path:
    ssh_cmd = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no {ssh_user}@{vps_host}"
else:
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no {ssh_user}@{vps_host}"
```

#### Step 4: Restart Claude Desktop

After updating the config, completely quit and restart Claude Desktop.

### Option 3: Use Windows SSH Agent (Recommended)

1. **Start SSH Agent**:
```powershell
# Open PowerShell as Administrator
Start-Service ssh-agent
Set-Service -Name ssh-agent -StartupType Automatic
```

2. **Add Your Key**:
```powershell
ssh-add C:\Users\YourUsername\.ssh\id_rsa
```

3. **Test Connection**:
```powershell
ssh root@72.61.0.186 "echo 'Connection successful'"
```

4. Now the MCP tools should work because SSH will use the agent.

## Testing the Fix

After applying one of the solutions above, test by asking me:

```
Deploy the latest changes to snow-contractor.com
```

Or:

```
Check the deployment status of snow-contractor.com
```

The MCP tools should now work properly.

## Current Workaround Commands

Until SSH is configured for MCP, you can run these manually:

### Update Application
```bash
ssh root@72.61.0.186 "cd /opt/contractor-portal && git pull origin beta && systemctl restart contractor-portal"
```

### Check Status
```bash
ssh root@72.61.0.186 "systemctl status contractor-portal --no-pager"
```

### View Logs
```bash
ssh root@72.61.0.186 "journalctl -u contractor-portal -n 50 --no-pager"
```

### Restart Application
```bash
ssh root@72.61.0.186 "systemctl restart contractor-portal"
```

## Why This Happened

The MCP server uses Python's `subprocess` to run SSH commands, but it doesn't have access to:
1. Your SSH keys in `~/.ssh/`
2. Your SSH agent
3. Your SSH config

By explicitly providing the SSH key path in the MCP environment variables, or by using the SSH agent, the MCP tools can authenticate to your VPS.

## Next Steps

1. **Right now**: Run `quick-update.bat` to deploy your changes
2. **Later**: Configure SSH keys in MCP config for full automation
3. **Test**: Try the MCP deployment commands to verify they work

---

**Quick Update**: `quick-update.bat`
**VPS IP**: 72.61.0.186
**Domain**: snow-contractor.com
**Application Path**: /opt/contractor-portal
