# Contractor Portal MCP Server

Model Context Protocol (MCP) server for the Contractor Portal web application, providing AI-powered integrations for weather services, messaging, notifications, and other portal features.

## Overview

This MCP server acts as a bridge between AI assistants (like Claude) and the Contractor Portal, enabling:

- **Weather Integration**: Real-time weather data and forecasts for contractor operations
- **Messaging System**: Send and retrieve messages within the portal
- **Notifications**: Manage portal notifications for users
- **Weather Alerts**: Monitor severe weather conditions affecting operations

## Current Status

This is the initial implementation with **placeholder tools**. All tools are functional but return sample data. API integrations for the following services are planned:

- Weather APIs (OpenWeatherMap, WeatherAPI, etc.)
- Portal messaging system
- Notification system
- Alert management

## Available Tools

### Weather Tools

1. **get_weather_info**
   - Get current weather information for a location
   - Parameters: location (required), units (optional: metric/imperial)
   - Status: Placeholder - API integration pending

2. **get_weather_forecast**
   - Get weather forecast for up to 5 days
   - Parameters: location (required), days (optional: 1-5)
   - Status: Placeholder - API integration pending

3. **check_weather_alerts**
   - Check for severe weather alerts
   - Parameters: location (required)
   - Status: Placeholder - API integration pending

### Messaging Tools

4. **send_message**
   - Send a message through the portal
   - Parameters: recipient, subject, message, priority (optional)
   - Status: Placeholder - Integration pending

5. **get_messages**
   - Retrieve messages from the portal
   - Parameters: user_id, status (optional), limit (optional)
   - Status: Placeholder - Integration pending

### Notification Tools

6. **get_portal_notifications**
   - Get portal notifications for a user
   - Parameters: user_id, type (optional)
   - Status: Placeholder - Integration pending

## Installation

### Prerequisites

- Python 3.8+
- MCP SDK (`pip install mcp`)
- Access to Contractor Portal database (for future integrations)

### Setup

1. Install dependencies:
```bash
cd "r:\Contractor App"
pip install -r app/requirements.txt
```

2. Configure environment variables (create `.env` file):
```env
# Database configuration (for future use)
DB_HOST=localhost
DB_USER=contractor
DB_PASSWORD=your_password
DB_NAME=contractor_portal

# Weather API configuration (for future use)
WEATHER_API_KEY=your_api_key_here
WEATHER_API_PROVIDER=openweathermap

# Portal configuration
APP_BASE_URL=http://localhost:8080
```

## Usage

### Running the MCP Server

Run the server directly:
```bash
python app/portal_mcp/server.py
```

### Integrating with Claude Code

Add to your Claude Code MCP configuration (`~/.claude/mcp_config.json` or `%USERPROFILE%\.claude\mcp_config.json` on Windows):

```json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": ["r:\\Contractor App\\app\\portal_mcp\\server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "DB_HOST": "localhost",
        "DB_USER": "contractor",
        "DB_PASSWORD": "your_password",
        "DB_NAME": "contractor_portal",
        "APP_BASE_URL": "http://localhost:8080"
      }
    }
  }
}
```

### Testing Tools

Example tool calls:

```python
# Get weather info
{
  "location": "Toronto",
  "units": "metric"
}

# Send a message
{
  "recipient": "user123",
  "subject": "Winter Storm Alert",
  "message": "Heavy snow expected tonight. Please prepare equipment.",
  "priority": "urgent"
}

# Get notifications
{
  "user_id": "user123",
  "type": "weather"
}
```

## Future Development

### Phase 1: Weather API Integration
- [ ] Integrate OpenWeatherMap or similar API
- [ ] Add API key management
- [ ] Implement real-time weather data fetching
- [ ] Add weather alert monitoring
- [ ] Cache weather data to reduce API calls

### Phase 2: Portal Database Integration
- [ ] Connect to contractor portal database
- [ ] Implement message storage and retrieval
- [ ] Add notification management
- [ ] User preference handling

### Phase 3: Advanced Features
- [ ] Weather-based operation recommendations
- [ ] Automated alerts for severe weather
- [ ] Message templates and bulk messaging
- [ ] Analytics and reporting integration
- [ ] Mobile push notification support

### Phase 4: Additional Integrations
- [ ] Calendar/scheduling integration
- [ ] Equipment tracking integration
- [ ] Route optimization with weather data
- [ ] Cost estimation based on weather forecasts

## Architecture

```
portal_mcp/
├── server.py              # Main MCP server
├── README.md             # This file
├── config.example.json   # Example configuration
└── tools/                # Tool implementations (future)
    ├── weather_tools.py
    ├── messaging_tools.py
    └── notification_tools.py
```

## API Integration Guide

### Weather API Options

1. **OpenWeatherMap** (Recommended)
   - Free tier: 1000 calls/day
   - Comprehensive data
   - Global coverage
   - Sign up: https://openweathermap.org/api

2. **WeatherAPI**
   - Free tier: 1M calls/month
   - Easy integration
   - Sign up: https://www.weatherapi.com/

3. **NOAA/Environment Canada**
   - Free government data
   - No API key required
   - Regional coverage

### Database Schema Requirements

For messaging and notifications:

```sql
-- Messages table (example)
CREATE TABLE portal_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id VARCHAR(50),
    recipient_id VARCHAR(50),
    subject VARCHAR(255),
    message TEXT,
    priority ENUM('low', 'normal', 'high', 'urgent'),
    read_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table (example)
CREATE TABLE portal_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    type ENUM('weather', 'messages', 'tasks', 'system'),
    title VARCHAR(255),
    message TEXT,
    read_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Considerations

- API keys should be stored in environment variables, never in code
- Database credentials should use least-privilege access
- Input validation on all tool parameters
- Rate limiting for API calls
- Audit logging for sensitive operations

## Support

For issues or questions:
- Check the main Contractor Portal documentation
- Review MCP SDK documentation: https://modelcontextprotocol.io/
- Contact the development team

## License

Same as Contractor Portal application
