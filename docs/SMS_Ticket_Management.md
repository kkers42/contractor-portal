# SMS Ticket Management System

## Overview
The SMS Ticket Management system allows contractors and field workers to manage winter service tickets entirely via text message, powered by AI to interpret natural language responses.

## Features

### For Field Workers (Contractors/Subcontractors)
- Start tickets via SMS
- Update ticket details (equipment, salt quantities, notes) using natural language
- Complete tickets via SMS
- Receive assignment notifications
- Query property addresses

### For Managers/Admins
- Send automatic SMS notifications when assigning properties
- View SMS conversation history
- Monitor active conversations and ticket status
- Track AI interpretation of messages

## Setup Instructions

### 1. Twilio Account Setup

1. Create a Twilio account at https://twilio.com
2. Purchase a phone number with SMS capabilities
3. Note down your credentials:
   - Account SID
   - Auth Token
   - Phone Number

### 2. Environment Variables

Add these environment variables to your server:

```bash
# Twilio Configuration
export TWILIO_ACCOUNT_SID="AC..." # Your Twilio Account SID
export TWILIO_AUTH_TOKEN="..." # Your Twilio Auth Token
export TWILIO_PHONE_NUMBER="+15551234567" # Your Twilio phone number

# Anthropic AI Configuration
export ANTHROPIC_API_KEY="sk-ant-..." # Your Anthropic API key for Claude
```

### 3. Database Migration

Run the SMS support migration:

```bash
cd /opt/contractor-portal/app
mysql -u root -p contractor_portal < migrations/add_sms_support.sql
```

This adds:
- `phone_number` and `sms_notifications_enabled` fields to `users` table
- `sms_conversations` table for tracking conversation state
- `sms_messages` table for message history
- `sms_notification_preferences` table for user preferences

### 4. Install Dependencies

```bash
pip install twilio anthropic
```

### 5. Configure Twilio Webhook

1. Log into Twilio Console
2. Go to Phone Numbers → Your purchased number
3. Under "Messaging", set:
   - **A MESSAGE COMES IN**: Webhook
   - **URL**: `https://your-domain.com/sms/webhook`
   - **HTTP Method**: POST

### 6. Add Phone Numbers to Users

In the web admin panel:
1. Go to **Manage Users**
2. Edit each user
3. Add their phone number in E.164 format: `+15551234567`
4. Save

## SMS Workflow

### Starting a Ticket

**User sends:** `START`

**System responds:**
```
✅ Ticket started for Walmart Parking Lot!

Please reply with:
- Equipment used
- Salt quantities
- Any notes

Example: Plow truck, 3 yards bulk salt, parking lot clear
```

If user has multiple assigned properties:
```
📍 Which property?

1. Walmart - 123 Main St
2. Target - 456 Oak Ave
3. Home Depot - 789 Pine Rd

Reply with the number or property name.
```

### Providing Ticket Details

The AI interprets natural language messages:

**Examples:**

| User Message | AI Interpretation |
|--------------|-------------------|
| `Plow truck 3 yards salt` | Equipment: Plow Truck, Bulk Salt: 3 yards |
| `Skid steer, 5 bags, icy conditions` | Equipment: Skid Steer, Bag Salt: 5, Notes: "icy conditions" |
| `Loader 2 yards bulk 3 bags calcium` | Equipment: Loader, Bulk Salt: 2, Calcium Chloride: 3 |
| `Salted twice very slippery` | Notes: "Salted twice very slippery" |

**System responds:**
```
✅ Ticket updated!

Reply DONE when finished, or send more details to update.
```

### Completing a Ticket

**User sends:** `DONE` or `FINISHED` or `DONE 5 bags`

**System responds:**
```
✅ Ticket completed for Walmart Parking Lot!

Thank you. Reply START when you begin the next job.
```

### Getting Help

**User sends:** `HELP`

**System responds:**
```
📱 SMS Ticket Help:

START - Begin a new ticket
DONE - Complete current ticket
Status of tickets - Check ticket status

While working, just text:
- Equipment used
- Salt quantities
- Notes

Example: "Plow truck 3 yards bulk salt parking lot clear"

Need help? Call dispatch.
```

## AI Interpretation

The system uses Claude AI (Anthropic) to interpret text messages and extract structured data.

### Supported Intents

1. **start_ticket** - Keywords: START, BEGIN, NEW TICKET
2. **complete_ticket** - Keywords: DONE, FINISHED, COMPLETE
3. **provide_details** - Equipment, quantities, notes
4. **query_address** - Address lookups
5. **unknown** - Fallback for unclear messages

### Extracted Data

The AI can extract:
- **Equipment**: Plow truck, skid steer, loader, salt truck, etc.
- **Bulk Salt Quantity**: "3 yards", "2.5 tons"
- **Bag Salt Quantity**: "5 bags", "10"
- **Calcium Chloride**: "2 bags calcium"
- **Notes**: Any additional context
- **Times**: "started at 2am", "finished at 3:30"

### Confidence Levels

- **High**: Clear, unambiguous message
- **Medium**: Partially clear, some assumptions made
- **Low**: Unclear, may need clarification

## Conversation States

The system tracks conversation state for each user:

1. **idle** - No active conversation
2. **awaiting_start_confirmation** - User needs to select property
3. **collecting_ticket_details** - Active ticket, collecting updates
4. **awaiting_completion** - Waiting for completion confirmation
5. **collecting_completion_details** - Gathering final details

## Admin Features

### SMS Conversation Viewer

Access at `/static/SMSConversations.html`

Features:
- View all active and recent SMS conversations
- See conversation state for each user
- Read message history
- View AI interpretation of each message
- Auto-refresh every 30 seconds

### Sending Assignment Notifications

When assigning a property to a contractor:

```javascript
// Automatic SMS sent via API
POST /sms/notify-assignment
{
  "property_id": 123,
  "contractor_id": 456
}
```

Message sent:
```
📍 New Assignment!

Property: Walmart Parking Lot
Address: 123 Main Street, Anytown, ST 12345

Reply START when you begin work.
Reply HELP for commands.
```

## API Endpoints

### Twilio Webhook
- `POST /sms/webhook` - Receives incoming SMS from Twilio

### Admin Endpoints
- `POST /sms/notify-assignment` - Send assignment notification
- `GET /sms/conversations` - List all conversations
- `GET /sms/messages/{conversation_id}` - Get messages for a conversation

## Database Schema

### sms_conversations
Tracks ongoing SMS conversations with state machine.

```sql
CREATE TABLE sms_conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    user_id INT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    conversation_state ENUM('idle', 'awaiting_start_confirmation',
        'collecting_ticket_details', 'awaiting_completion',
        'collecting_completion_details') DEFAULT 'idle',
    active_ticket_id INT NULL,
    active_property_id INT NULL,
    context_data JSON NULL,
    last_message_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ...
);
```

### sms_messages
Stores all inbound and outbound SMS messages.

```sql
CREATE TABLE sms_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NULL,
    phone_number VARCHAR(20) NOT NULL,
    direction ENUM('inbound', 'outbound') NOT NULL,
    message_body TEXT NOT NULL,
    twilio_sid VARCHAR(100) NULL,
    ai_processed BOOLEAN DEFAULT FALSE,
    ai_interpretation JSON NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ...
);
```

### sms_notification_preferences
User preferences for SMS notifications.

```sql
CREATE TABLE sms_notification_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    notify_on_assignment BOOLEAN DEFAULT TRUE,
    notify_on_route_assignment BOOLEAN DEFAULT TRUE,
    notify_on_weather_alert BOOLEAN DEFAULT TRUE,
    quiet_hours_start TIME NULL,
    quiet_hours_end TIME NULL,
    ...
);
```

## Troubleshooting

### SMS Not Received

1. Check Twilio webhook is configured correctly
2. Verify webhook URL is publicly accessible (not localhost)
3. Check Twilio logs in Twilio Console → Messaging → Logs
4. Verify phone number is in E.164 format in database

### SMS Not Sent

1. Check environment variables are set (`TWILIO_ACCOUNT_SID`, etc.)
2. Verify user has `sms_notifications_enabled = TRUE`
3. Check user has valid phone number
4. Review application logs for errors

### AI Not Interpreting Correctly

1. Check `ANTHROPIC_API_KEY` is set
2. Review `sms_messages` table, column `ai_interpretation`
3. Messages should be processed within seconds
4. If confidence is "low", user message was unclear

### Webhook Errors

Common issues:
- **401 Unauthorized**: Twilio auth token mismatch
- **404 Not Found**: Webhook URL incorrect
- **500 Internal Server Error**: Check app logs, likely database or API key issue

## Cost Estimates

### Twilio SMS Costs
- **US SMS**: $0.0079 per message sent/received
- **Phone Number**: $1.15/month

**Example**: 100 messages/day = ~$47/month for SMS + $1.15/month for number = **$48.15/month**

### Anthropic AI Costs
- **Claude 3.5 Sonnet**: ~$3 per million input tokens, ~$15 per million output tokens
- **Average SMS processing**: ~100 input tokens, ~50 output tokens
- **1000 messages**: ~$0.30 for AI processing

## Security

- All messages are logged to database
- Phone numbers validated before processing
- User authentication required for all admin endpoints
- Twilio webhook validates message origin
- AI processing is stateless and doesn't store PII beyond conversation context

## Future Enhancements

- Photo/image support for damage documentation
- Voice-to-text for hands-free ticket updates
- Location tracking integration
- Automatic property detection via GPS
- Multi-language support
- WhatsApp integration
- Two-way SMS reminders for incomplete tickets
- SMS-based route acceptance workflow

## Support

For issues or questions:
1. Check application logs: `journalctl -u contractor-portal -f`
2. Review Twilio logs in Twilio Console
3. Check database for conversation state
4. View SMS conversation history in admin panel
