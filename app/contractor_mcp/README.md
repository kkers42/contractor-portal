# Contractor Portal MCP Server

This MCP (Model Context Protocol) server provides Claude with direct access to your Contractor Portal application, enabling intelligent assistance with database queries, user management, application configuration, and more.

## Features

### Resources
- **Database Schema** - View all tables and columns in your database
- **Environment Configuration** - Check current environment settings
- **Application Statistics** - Get overview of users, properties, and logs

### Tools
1. **query_database** - Execute SELECT queries on the database
2. **update_database** - Execute INSERT/UPDATE/DELETE queries
3. **get_user_info** - Get detailed user information by email or ID
4. **get_property_info** - Get property details by name or ID
5. **get_logs** - Retrieve operation logs with filtering
6. **approve_pending_users** - Approve OAuth users and assign roles
7. **read_file** - Read application files (code, configs, logs)
8. **list_files** - List files in application directories
9. **get_equipment_usage** - Get equipment usage reports with costs

## Installation

### 1. Install MCP SDK

```bash
pip install mcp
```

Update your [requirements.txt](../requirements.txt):

```bash
cd "r:\Contractor App\app"
pip install mcp
pip freeze > requirements.txt
```

### 2. Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": [
        "r:\\Contractor App\\app\\contractor_mcp\\server.py"
      ],
      "env": {
        "DB_HOST": "127.0.0.1",
        "DB_USER": "root",
        "DB_PASSWORD": "Bimmer325!",
        "DB_NAME": "contractor_portal",
        "APP_BASE_URL": "http://localhost:8080"
      }
    }
  }
}
```

**Important:** For production deployments, use environment variables or a secure vault instead of hardcoding credentials.

### 3. Restart Claude Desktop

After updating the configuration, restart Claude Desktop completely (quit and reopen).

## Usage Examples

### View Database Schema

```
Can you show me the database schema for the contractor portal?
```

Claude will use the `contractor://database/schema` resource to display all tables and columns.

### Query Users

```
Show me all pending users waiting for approval
```

Claude will use `query_database` tool:
```sql
SELECT id, name, email, display_name, created_at
FROM users
WHERE status = 'pending'
ORDER BY created_at DESC
```

### Get User Details

```
Get information about user admin@contractor.local
```

Claude will use `get_user_info` tool to show complete user details including OAuth identities.

### Approve Users

```
Approve user ID 5 as a Manager
```

Claude will use `approve_pending_users` tool to activate the user with the Manager role.

### View Logs

```
Show me the last 20 winter operation logs
```

Claude will use `get_logs` tool with appropriate filters.

### Equipment Usage Report

```
What was the equipment usage and cost for the last 30 days?
```

Claude will use `get_equipment_usage` tool to calculate total hours and costs.

### Read Application Files

```
Show me the current OAuth configuration in auth_oidc.py
```

Claude will use `read_file` tool to display the file contents.

### Application Statistics

```
Give me an overview of the application usage
```

Claude will use the `contractor://stats/overview` resource to show user counts, log counts, and recent activity.

## Security Considerations

### Path Traversal Protection
The MCP server includes path traversal protection - it will only access files within the application directory.

### Database Access
- **Read access:** `query_database` tool allows SELECT queries
- **Write access:** `update_database` tool allows INSERT/UPDATE/DELETE (use with caution!)

### Credentials
- Database credentials are loaded from environment variables
- Never commit credentials to version control
- Use `.env` file for local development
- Use secure vaults (AWS Secrets Manager, etc.) for production

## Advanced Configuration

### Production Deployment

For production servers, create a separate configuration:

```json
{
  "mcpServers": {
    "contractor-portal-prod": {
      "command": "ssh",
      "args": [
        "bubbles@contractorportal",
        "cd /opt/contractor-portal && python3 contractor_mcp/server.py"
      ]
    }
  }
}
```

This allows you to interact with your production database through SSH.

### Custom Queries

You can ask Claude to run any SQL query:

```
Run this query: SELECT role, COUNT(*) FROM users GROUP BY role
```

### Bulk Operations

```
Approve all pending users who signed up today as Subcontractors
```

Claude will:
1. Query pending users created today
2. Loop through and approve each one
3. Report the results

## Troubleshooting

### MCP Server Not Showing in Claude Desktop

1. Check that the path in `claude_desktop_config.json` is correct
2. Verify Python is in your PATH
3. Check Claude Desktop logs: `%APPDATA%\Claude\logs` (Windows)
4. Restart Claude Desktop completely

### Database Connection Errors

1. Verify database credentials in the config
2. Check that MySQL is running
3. Test connection manually: `mysql -u root -p contractor_portal`
4. Ensure firewall allows database connections

### Permission Errors

1. Verify the Python script has execute permissions
2. Check database user permissions
3. Ensure the user can read `.env` file

## Integration with Other Features

### Future Extensions

The MCP server can be easily extended to support:

1. **Messaging System** - Add tools for sending/receiving messages
2. **AI Analysis** - Add tools that use AI to analyze logs, detect patterns
3. **Automated Reports** - Generate and email reports on schedule
4. **Real-time Monitoring** - Subscribe to database changes
5. **Backup Management** - Tools for database backups and restoration

### Example: Adding a Messaging Tool

```python
Tool(
    name="send_message",
    description="Send a message to a user or group",
    inputSchema={
        "type": "object",
        "properties": {
            "recipient_id": {"type": "integer"},
            "message": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "normal", "high"]}
        },
        "required": ["recipient_id", "message"]
    }
)
```

## Testing the MCP Server

### Manual Test

Run the server directly to check for errors:

```bash
cd "r:\Contractor App\app"
python mcp\server.py
```

It should wait for input (it's a stdio server). Press Ctrl+C to exit.

### Test from Claude Desktop

After configuration:
1. Open Claude Desktop
2. Start a new conversation
3. Look for the 🔌 icon indicating MCP is connected
4. Try a simple query: "Show me the database schema"

## Benefits

### Development
- Instant database queries without switching tools
- Quick testing of features
- Easy debugging of user issues
- Code review assistance

### Operations
- User management (approvals, role changes)
- Data analysis and reporting
- System monitoring
- Quick fixes and updates

### Future Features
- Natural language interface for non-technical users
- Automated workflows
- AI-powered insights and recommendations
- Integration with external services

## Next Steps

1. Install the MCP server (follow installation steps above)
2. Test basic queries and tools
3. Extend with custom tools as needed
4. Deploy to production server for remote management
5. Add messaging system integration
6. Add AI analysis capabilities

## Support

For issues or questions:
- Check the troubleshooting section above
- Review MCP SDK documentation: https://modelcontextprotocol.io/
- Check application logs in the app directory
