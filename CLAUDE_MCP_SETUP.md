# Claude Code MCP Integration Guide

This guide explains how to connect Claude Code to your deployed Contractor Portal using the Model Context Protocol (MCP).

## What is MCP?

Model Context Protocol (MCP) allows Claude Code to directly interact with your contractor portal data through a standardized interface. This enables Claude to:
- Query properties, contractors, and service logs
- Create new records
- Generate reports
- Analyze data patterns

## Prerequisites

1. Contractor Portal deployed and running on Hostinger
2. Claude Code installed locally
3. Domain with HTTPS enabled (SSL certificate)

## MCP Server Architecture

The Contractor Portal includes a built-in MCP server that exposes these tools:

### Available MCP Tools

1. **get-properties**: Retrieve list of all properties
2. **get-contractors**: Retrieve list of all contractors
3. **get-logs**: Get service logs with filtering options
4. **create-property**: Add a new property to the system
5. **create-contractor**: Add a new contractor/worker
6. **get-property-stats**: Get statistics for a specific property
7. **search-logs**: Search logs by date range, contractor, or property

## Configuration Steps

### Step 1: Verify MCP Server is Running

SSH into your Hostinger VPS:

```bash
ssh root@your-vps-ip

# Check if the application is running
systemctl status contractor-portal

# Check MCP endpoint is accessible
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "mcp_enabled": true,
  "version": "1.0-beta"
}
```

### Step 2: Configure Claude Code Client

#### Option A: Using Claude Code MCP Configuration File

1. Open your Claude Code MCP configuration:

```bash
# On Windows
%USERPROFILE%\.claude\mcp_servers.json

# On macOS/Linux
~/.claude/mcp_servers.json
```

2. Add the contractor portal server:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "node",
      "args": [
        "/path/to/mcp-client-sse.js"
      ],
      "env": {
        "MCP_SERVER_URL": "https://your-domain.com",
        "MCP_AUTH_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

#### Option B: Using Direct HTTP Connection

Create a file `contractor-portal-mcp.json`:

```json
{
  "name": "contractor-portal",
  "version": "1.0",
  "endpoint": {
    "type": "sse",
    "url": "https://your-domain.com/mcp/sse",
    "headers": {
      "Authorization": "Bearer YOUR_JWT_TOKEN"
    }
  },
  "tools": [
    {
      "name": "get-properties",
      "description": "Retrieve all properties from the contractor portal",
      "inputSchema": {
        "type": "object",
        "properties": {}
      }
    },
    {
      "name": "get-contractors",
      "description": "Retrieve all contractors and workers",
      "inputSchema": {
        "type": "object",
        "properties": {}
      }
    },
    {
      "name": "get-logs",
      "description": "Get service logs with optional filtering",
      "inputSchema": {
        "type": "object",
        "properties": {
          "start_date": {
            "type": "string",
            "description": "Start date (YYYY-MM-DD)"
          },
          "end_date": {
            "type": "string",
            "description": "End date (YYYY-MM-DD)"
          },
          "contractor_id": {
            "type": "integer",
            "description": "Filter by contractor ID"
          },
          "property_id": {
            "type": "integer",
            "description": "Filter by property ID"
          }
        }
      }
    },
    {
      "name": "create-property",
      "description": "Add a new property to the system",
      "inputSchema": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "Property name"
          },
          "address": {
            "type": "string",
            "description": "Property address"
          },
          "property_type": {
            "type": "string",
            "description": "Type of property"
          }
        },
        "required": ["name", "address"]
      }
    }
  ]
}
```

### Step 3: Obtain Authentication Token

1. Log in to your contractor portal at `https://your-domain.com`
2. Open browser DevTools (F12)
3. Go to Application → Local Storage
4. Find the `token` key and copy its value

Alternatively, use the API:

```bash
curl -X POST https://your-domain.com/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-admin-email@example.com",
    "password": "your-password"
  }'
```

Copy the JWT token from the response.

### Step 4: Test MCP Connection

Create a test script `test-mcp.js`:

```javascript
const MCPClient = require('@anthropic/mcp-client');

async function testConnection() {
  const client = new MCPClient({
    serverUrl: 'https://your-domain.com/mcp/sse',
    headers: {
      'Authorization': 'Bearer YOUR_JWT_TOKEN'
    }
  });

  try {
    // Test: Get all properties
    const properties = await client.callTool('get-properties', {});
    console.log('Properties:', properties);

    // Test: Get all contractors
    const contractors = await client.callTool('get-contractors', {});
    console.log('Contractors:', contractors);

  } catch (error) {
    console.error('MCP Connection Error:', error);
  }
}

testConnection();
```

Run:
```bash
node test-mcp.js
```

## Using MCP with Claude Code

Once configured, you can interact with your contractor portal directly in Claude Code:

### Example Prompts

1. **Query Data**:
   ```
   Show me all properties in the system
   ```

2. **Create Records**:
   ```
   Add a new property called "Oak Street Complex" at "123 Oak St, Seattle, WA"
   ```

3. **Analyze Logs**:
   ```
   Show me all service logs from last week for contractor ID 5
   ```

4. **Generate Reports**:
   ```
   Create a summary report of all pool services performed this month
   ```

## MCP Server Code Structure

The MCP server is implemented in `/app/contractor_mcp/server.py`:

```python
from fastapi import APIRouter, Depends
from mcp.server import MCPServer
from mcp.types import Tool, TextContent

router = APIRouter(prefix="/mcp")
mcp_server = MCPServer("contractor-portal-mcp")

# Tool definitions
@mcp_server.tool()
async def get_properties():
    """Retrieve all properties"""
    # Implementation
    pass

@mcp_server.tool()
async def get_contractors():
    """Retrieve all contractors"""
    # Implementation
    pass

# Add router to main app
router.include_router(mcp_server.get_router())
```

## Security Considerations

1. **JWT Authentication**: All MCP requests require valid JWT token
2. **Rate Limiting**: Implement rate limiting on MCP endpoints
3. **HTTPS Only**: MCP should only be accessible over HTTPS
4. **Token Expiration**: JWT tokens expire after 2 hours (default)
5. **CORS**: Configure CORS properly for your domain

### Securing MCP Endpoint

Add IP whitelist in `/opt/contractor-portal/.env`:

```env
MCP_ALLOWED_IPS=123.45.67.89,98.76.54.32
```

Or use Nginx to restrict access:

```nginx
location /mcp {
    allow 123.45.67.89;  # Your IP
    deny all;

    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
}
```

## Troubleshooting

### MCP Connection Timeout
```bash
# Check if service is running
systemctl status contractor-portal

# Check firewall rules
ufw status
```

### Authentication Failures
```bash
# Verify JWT token is valid
curl https://your-domain.com/verify-token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Tool Not Found Errors
```bash
# Check MCP server logs
journalctl -u contractor-portal -f | grep MCP
```

## Advanced Configuration

### Custom MCP Tools

Add custom tools by editing `contractor_mcp/server.py`:

```python
@mcp_server.tool()
async def generate_monthly_report(month: int, year: int):
    """Generate comprehensive monthly report"""
    # Implementation
    return {
        "total_services": 45,
        "total_hours": 120.5,
        "top_contractor": "John Doe",
        # ... more data
    }
```

### Webhook Integration

Configure webhooks to notify Claude Code of changes:

```python
# In routes/green_logs.py
async def create_log(log_data: dict):
    # Save log to database
    result = save_log(log_data)

    # Notify MCP clients
    await mcp_server.notify_clients({
        "event": "log_created",
        "data": result
    })

    return result
```

## Performance Optimization

1. **Caching**: Enable Redis caching for frequent queries
2. **Connection Pooling**: Use connection pooling for database
3. **Async Operations**: Ensure all MCP tools use async/await
4. **Rate Limiting**: Implement per-tool rate limits

## Monitoring

### Set Up Logging

```python
# Add to main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MCP - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/contractor-portal-mcp.log'),
        logging.StreamHandler()
    ]
)
```

### Monitor MCP Usage

```bash
# View MCP-specific logs
journalctl -u contractor-portal -f | grep "MCP"

# Count MCP requests
cat /var/log/contractor-portal-mcp.log | grep "Tool called" | wc -l
```

## Support

For MCP-related issues:
1. Check [Anthropic MCP Documentation](https://modelcontextprotocol.io)
2. Review application logs: `journalctl -u contractor-portal -f`
3. Test endpoints manually: `curl https://your-domain.com/mcp/health`
4. Open GitHub issue with logs and configuration

---

**MCP Version**: 1.0
**Protocol**: Server-Sent Events (SSE)
**Authentication**: JWT Bearer Token
**Last Updated**: November 2025
