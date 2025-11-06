# MCP Quick Start Guide

## What is MCP?

MCP (Model Context Protocol) connects Claude Desktop to your Contractor Portal application, giving Claude direct access to your database, files, and application state. This means you can ask Claude to:

- Query your database using natural language
- Approve pending users
- Generate reports
- Review code files
- Monitor application health
- And much more!

## 5-Minute Setup

### Step 1: Install MCP Package

Open a terminal in the app directory and run:

```bash
pip install mcp
```

### Step 2: Configure Claude Desktop

**Windows Users:**
1. Open: `%APPDATA%\Claude\claude_desktop_config.json`
2. If the file doesn't exist, create it
3. Add this configuration:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": ["r:\\Contractor App\\app\\mcp\\server.py"]
    }
  }
}
```

**Mac/Linux Users:**
1. Open: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Use `python3` instead of `python` in the command
3. Update the path to match your installation

### Step 3: Restart Claude Desktop

Completely quit and restart Claude Desktop (not just close the window).

### Step 4: Verify Connection

Look for the 🔌 plug icon at the bottom of Claude Desktop. If you see it, you're connected!

## What You Can Do

### User Management

```
Show me all pending users
```

```
Approve user 5 as a Manager
```

```
Get details for admin@contractor.local
```

### Database Queries

```
How many users do we have by role?
```

```
Show me all properties in the system
```

```
List the last 10 winter operation logs
```

### Reports

```
What was the equipment usage cost last month?
```

```
Which contractor logged the most hours this week?
```

```
Show me all logs for property "Main Street Office"
```

### Application Management

```
Show me the database schema
```

```
What's the current environment configuration?
```

```
Read the OAuth configuration file
```

### File Operations

```
Show me the auth_routes.py file
```

```
List all Python files in the routes directory
```

```
What's in the .env file?
```

## Common Use Cases

### Scenario 1: New OAuth User Signs Up

**You:** "Show me pending users"

**Claude:** Uses `query_database` to show:
```
- John Doe (john@example.com) - Signed up via Google
- Jane Smith (jane@example.com) - Signed up via Microsoft
```

**You:** "Approve John as a Subcontractor and Jane as a Manager"

**Claude:** Uses `approve_pending_users` twice to activate both accounts.

### Scenario 2: Generate Weekly Report

**You:** "Generate a report of all winter operations from last week with total costs"

**Claude:**
1. Uses `get_logs` to fetch winter logs from last week
2. Uses `get_equipment_usage` to calculate costs
3. Formats a comprehensive report with totals

### Scenario 3: Debug an Issue

**You:** "User admin@contractor.local says they can't log in. What's their account status?"

**Claude:**
1. Uses `get_user_info` to check account details
2. Shows status, role, OAuth identities
3. Suggests fixes if needed

### Scenario 4: Add a New Feature

**You:** "I need to add a messaging system. Show me how the current user system works"

**Claude:**
1. Uses `read_file` to show `routes/auth_routes.py`
2. Uses database queries to show user table structure
3. Suggests implementation approach based on existing patterns

## Pro Tips

### Natural Language Queries

You don't need to know SQL! Just ask naturally:
- ❌ "SELECT * FROM users WHERE role='Admin'"
- ✅ "Show me all admin users"

### Multiple Operations

Chain operations together:
- "Show me pending users, then approve anyone from @company.com as Subcontractors"

### Context Awareness

Claude remembers the conversation context:
- **You:** "Show me property 5"
- **You:** "Now show me all logs for that property"

### Data Analysis

Ask for insights:
- "What trends do you see in the winter operations logs?"
- "Which equipment has the highest cost per use?"

## Troubleshooting

### MCP Not Connecting

1. **Check the config file path is correct**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **Verify Python path**
   - Run `python --version` in terminal
   - Update config to use `python3` if needed

3. **Check the MCP server path**
   - Make sure the path to `server.py` is correct
   - Use absolute paths, not relative

4. **Restart completely**
   - Quit Claude Desktop entirely (check Task Manager on Windows)
   - Start it again

### Database Connection Errors

If Claude says "Database connection failed":

1. Check that MySQL is running
2. Verify credentials in your `.env` file
3. Test manually: `mysql -u root -p contractor_portal`

### Permission Errors

If you see "Access denied":

1. Check database user permissions
2. Verify the MCP server can read the `.env` file
3. On Linux/Mac, check file permissions: `chmod 644 .env`

## Advanced Features

### Custom SQL Queries

```
Run this query: SELECT contractor_name, COUNT(*) as log_count
FROM winter_ops_logs
GROUP BY contractor_name
ORDER BY log_count DESC
```

### Bulk Operations

```
Find all users with @oldcompany.com email and update their emails to @newcompany.com
```

### Real-time Monitoring

```
Show me any logs created in the last hour
```

### Code Review

```
Review the security of the login endpoint in auth_routes.py
```

## What's Next?

### Add Messaging System

With MCP in place, you can ask Claude to:
1. Design the database schema for messages
2. Write the backend routes
3. Create the frontend UI
4. Test the implementation

All through natural conversation!

### Add AI Features

Examples:
- **Smart Routing:** "Analyze log patterns and suggest optimal contractor assignments"
- **Predictive Maintenance:** "Which equipment is likely to need replacement based on usage?"
- **Cost Optimization:** "Recommend ways to reduce winter operations costs"

### Automate Workflows

- **Daily Reports:** "Generate and email yesterday's activity summary to admins"
- **User Onboarding:** "When a new user is approved, send them a welcome email with login instructions"
- **Anomaly Detection:** "Alert me if any contractor logs more than 12 hours in a day"

## Example Session

```
You: Hi Claude! I just set up the MCP server for my contractor portal.

Claude: Great! I can see I'm connected to your Contractor Portal. I have access to your database, files, and application resources. What would you like to do?

You: Give me an overview of the system

Claude: [Uses contractor://stats/overview resource]

Here's your Contractor Portal overview:

**Users:**
- 3 Admins (all active)
- 5 Managers (all active)
- 12 Subcontractors (10 active, 2 pending)

**Properties:** 8 locations

**Operation Logs:**
- Winter operations: 234 logs
- Green services: 156 logs

**Recent Activity:**
Last 5 logins:
1. John Doe (Manager) - 2 hours ago
2. Admin User (Admin) - 3 hours ago
...

You: Show me the 2 pending subcontractors

Claude: [Uses query_database]

Here are the 2 pending subcontractors:

1. Mike Johnson (mike.j@example.com)
   - Signed up: 2 days ago via Google
   - Awaiting approval

2. Sarah Chen (sarah.c@example.com)
   - Signed up: 1 day ago via Microsoft
   - Awaiting approval

Would you like to approve either of them?

You: Approve both as Subcontractors

Claude: [Uses approve_pending_users twice]

✓ Mike Johnson approved as Subcontractor
✓ Sarah Chen approved as Subcontractor

Both users can now log in and access the system.

You: Perfect! Now show me equipment usage costs for January

Claude: [Uses get_equipment_usage with date filters]

Equipment Usage Report - January 2025:

1. Plow Truck - 45 uses, 180 hours, $9,000
2. Salt Spreader - 38 uses, 76 hours, $3,800
3. Skid Steer - 22 uses, 88 hours, $6,600

Total: 105 uses, 344 hours, $19,400

You: Thanks! This is so much easier than using SQL directly.

Claude: You're welcome! Let me know if you need any reports, user management, or help building new features. I can access your entire application through MCP.
```

## Ready to Deploy?

Once you're comfortable with MCP locally, you can:

1. Install MCP on your production server
2. Configure SSH access for remote management
3. Manage your live application through Claude Desktop

See [README.md](README.md) for production deployment instructions.

---

**Happy building! 🚀**
