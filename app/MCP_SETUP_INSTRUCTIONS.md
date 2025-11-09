# Claude Desktop MCP Setup Instructions

## Quick Setup for Hostinger API Access

### Step 1: Locate Your Claude Desktop Config File

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

To open it quickly:
1. Press `Win + R`
2. Type: `%APPDATA%\Claude`
3. Press Enter
4. Open `claude_desktop_config.json` in a text editor

### Step 2: Add the MCP Server Configuration

Replace the contents with this (or add the `mcpServers` section if you already have a config):

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": [
        "r:\\Contractor App\\app\\contractor_mcp\\server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "HOSTINGER_API_KEY": "YOUR_HOSTINGER_API_KEY_HERE"
      }
    }
  }
}
```

**IMPORTANT**: Replace `YOUR_HOSTINGER_API_KEY_HERE` with your actual Hostinger API key!

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop completely for the changes to take effect.

### Step 4: Verify It's Working

In Claude Desktop, try asking:
```
List my Hostinger domains
```

If it works, you'll see your domains listed!

## Available MCP Commands

Once configured, you can use these commands in Claude Desktop:

### Deployment Commands
- "Deploy contractor portal to VPS [IP] with domain [domain] and database password [password]"
- "Check deployment status on VPS [IP]"
- "View deployment logs from VPS [IP]"
- "Restart contractor portal on VPS [IP]"

### DNS Commands (with Hostinger API)
- "List my Hostinger domains"
- "Show DNS records for [domain]"
- "Configure DNS for [domain] to point to [IP]"

### Complete Deployment (Fully Automated!)
```
Complete deployment of contractor portal to VPS [IP] with domain [domain],
database password [password], and email [email]
```

This will:
1. Deploy the app
2. Configure DNS automatically via API
3. Wait for DNS propagation
4. Install SSL certificate
5. Verify everything is working

## Troubleshooting

### "MCP server not found" error
- Check that the path `r:\\Contractor App\\app\\contractor_mcp\\server.py` exists
- Make sure you've installed dependencies: `pip install -r requirements.txt`

### "HOSTINGER_API_KEY not found" error
- Verify you replaced `YOUR_HOSTINGER_API_KEY_HERE` with your actual API key
- Make sure there are no extra spaces or quotes around the key
- Restart Claude Desktop after making changes

### "Domain not found" error
- The domain must be in your Hostinger account
- Check available domains with: "List my Hostinger domains"

## Getting Your Hostinger API Key

1. Log in to your Hostinger control panel
2. Search for "API" in the search bar
3. Click "Create API Key" or "Generate New Key"
4. Copy the key (it starts with `hapi_` or similar)
5. Paste it into your config file

**Important**: Keep your API key secure! Don't commit it to git or share it publicly.

## Example Config File Locations

**If you have other MCP servers**, your config might look like:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": ["r:\\Contractor App\\app\\contractor_mcp\\server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "HOSTINGER_API_KEY": "your-key-here"
      }
    },
    "some-other-mcp": {
      "command": "node",
      "args": ["path/to/other/server.js"]
    }
  }
}
```

Just add the `contractor-portal` section alongside your existing servers.
