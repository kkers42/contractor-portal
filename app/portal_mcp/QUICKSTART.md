# Portal MCP Quick Start Guide

Get the Contractor Portal MCP server up and running in minutes.

## What is This?

This MCP (Model Context Protocol) server enables AI assistants like Claude to interact with your Contractor Portal, providing:
- Weather information for operations planning
- Messaging capabilities
- Notification management
- Future integrations (APIs will be added later)

## Quick Start

### 1. Prerequisites Check

Make sure you have:
- Python 3.8 or higher installed
- The Contractor Portal application set up
- Claude Code or another MCP-compatible client

### 2. Install Dependencies

All dependencies are already in the main requirements.txt:

```bash
cd "r:\Contractor App"
pip install -r app\requirements.txt
```

### 3. Test the MCP Server

Run the server to verify it works:

```bash
python app\portal_mcp\server.py
```

You should see:
```
INFO:__main__:Starting Contractor Portal MCP Server...
INFO:__main__:Available tools: weather info, weather forecast, messaging, notifications
INFO:__main__:Note: This is a placeholder implementation. API integrations pending.
```

Press Ctrl+C to stop it.

### 4. Configure Claude Code

Add the MCP server to your Claude Code configuration.

**Windows:**
Edit `%USERPROFILE%\.claude\mcp_config.json`

**Mac/Linux:**
Edit `~/.claude/mcp_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": ["r:\\Contractor App\\app\\portal_mcp\\server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "DB_HOST": "localhost",
        "DB_NAME": "contractor_portal"
      }
    }
  }
}
```

**Note:** Adjust the path if your Contractor App is in a different location.

### 5. Restart Claude Code

Restart Claude Code to load the MCP server.

### 6. Test in Claude Code

Ask Claude to use the weather tools:

```
Can you check the weather for Toronto?
```

Claude will use the `get_weather_info` tool. You'll see placeholder data since the API isn't integrated yet.

## Current Status

All tools return **placeholder/sample data**. This is intentional for the initial setup. You can verify the MCP integration is working, and actual API integrations will be added later.

### Available Tools (Placeholders)

- `get_weather_info` - Current weather
- `get_weather_forecast` - 5-day forecast
- `check_weather_alerts` - Weather alerts
- `send_message` - Send portal messages
- `get_messages` - Retrieve messages
- `get_portal_notifications` - Get notifications

## Next Steps

Once you've verified the MCP server works:

1. **Weather API Integration**: Get an API key from OpenWeatherMap or similar service
2. **Database Connection**: Connect to the portal database for messaging
3. **Customize Tools**: Add project-specific tools and features

See [README.md](README.md) for full documentation and integration guides.

## Troubleshooting

### Server won't start
- Check Python version: `python --version` (need 3.8+)
- Verify dependencies: `pip list | grep mcp`
- Check for typos in the server.py path

### Claude doesn't see the tools
- Verify MCP config path is correct
- Restart Claude Code completely
- Check the logs in Claude Code's output panel

### Tools return errors
- This version uses placeholders, so errors indicate a code issue
- Check the server logs for details
- Ensure all required arguments are provided

## Support

- Main documentation: [README.md](README.md)
- MCP documentation: https://modelcontextprotocol.io/
- Portal documentation: See main app README

## What's Next?

The placeholder implementation is complete and ready for version control. Future development will add:
- Real weather API integration
- Database connections for messaging
- Notification system integration
- Additional portal features

Check the README.md for the full development roadmap.
