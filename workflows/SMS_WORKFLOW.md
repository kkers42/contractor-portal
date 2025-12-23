# SMS Workflow Documentation

**Purpose**: How SMS messaging works for contractor communication
**AI Provider**: ChatGPT (OpenAI gpt-4o-mini)
**SMS Provider**: Twilio
**Last Updated**: 2025-12-23

---

## Overview

The SMS system allows contractors to:
1. Check in/out of snow events via text message
2. Create and manage winter service tickets (ops logs)
3. Report equipment, salt usage, and notes
4. Receive property assignments

All SMS messages are interpreted by ChatGPT to extract structured data.

---

## Architecture

```
Contractor
    ↓ (sends SMS)
Twilio
    ↓ (webhook POST)
FastAPI /sms/webhook
    ↓
sms_routes.py: handle_sms_message()
    ↓
ChatGPT (gpt-4o-mini)
    ↓ (interprets message)
Database (update conversation state)
    ↓
Response message
    ↓
Twilio API
    ↓
Contractor (receives SMS reply)
```

---

## Components

### 1. Twilio Configuration
**File**: Environment variables in `.env`

```bash
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
```

**Webhook**: https://snow-contractor.com/sms/webhook
- Method: POST
- Configured in Twilio Console

---

### 2. SMS Route Handler
**File**: `app/routes/sms_routes.py`

#### Key Functions:

**`handle_sms_message(from_number: str, message_body: str, user_id: int)`**
- Main SMS processing function
- Determines intent from message
- Routes to appropriate handler
- Returns response text

**`get_ai_interpretation(user_message: str, conversation_context: dict)`**
- Calls ChatGPT to interpret natural language
- Extracts structured data (equipment, salt, notes)
- Returns JSON with intent and extracted fields

**`create_ticket_from_sms(user_id: int, user_name: str, property_id: int)`**
- Creates new winter_ops_log entry
- Snaps time to nearest 15 minutes
- Uses user's default equipment

**`send_sms(to_phone: str, message: str, conversation_id: int)`**
- Sends SMS via Twilio API
- Logs outbound message to database
- Returns Twilio message object

---

### 3. Database Tables

#### sms_conversations
Stores conversation state for each contractor:

```sql
CREATE TABLE sms_conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL DEFAULT 1,
    user_id INT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    state ENUM('idle', 'awaiting_property', 'collecting_data'),
    active_ticket_id INT,
    active_property_id INT,
    context_data JSON,
    last_message_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Conversation States**:
- `idle` - No active ticket
- `awaiting_property` - Waiting for property selection after "START"
- `collecting_data` - Ticket active, collecting equipment/salt/notes

#### sms_messages
Stores all inbound and outbound messages:

```sql
CREATE TABLE sms_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    direction ENUM('inbound', 'outbound'),
    from_number VARCHAR(20),
    to_number VARCHAR(20),
    message_body TEXT,
    ai_interpretation JSON,
    twilio_sid VARCHAR(100),
    status VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## SMS Commands

### Event Check-In Commands

#### `READY` / `CHECKIN` / `CHECK-IN` / `AVAILABLE`
**Purpose**: Check in for the active snow event

**Flow**:
1. User texts "READY"
2. System checks for active winter event
3. If event exists:
   - Creates/updates event_checkins record
   - Sets status to 'checked_in'
   - Uses user's default equipment
4. Responds with confirmation

**Response**:
```
✅ Checked in for December 23 Snowstorm!

Equipment: F350, Plow, Salter

You may receive assignments soon.

Reply:
- WORKING when servicing
- HOME when finished
```

**Edge Cases**:
- No active event → "❌ No active snow event..."
- Already checked in → Updates status to READY

---

#### `WORKING` / `BUSY` / `ON SITE` / `SERVICING`
**Purpose**: Update status to "working" (servicing a property)

**Flow**:
1. User texts "WORKING"
2. System finds active check-in
3. Updates event_checkins.status = 'working'
4. Responds with confirmation

**Response**:
```
✅ Status updated to WORKING for December 23 Snowstorm.

Reply READY when available for new assignments, or HOME when finished.
```

---

#### `HOME` / `OFF` / `OFFLINE`
**Purpose**: Check out and mark unavailable

**Flow**:
1. User texts "HOME"
2. System:
   - Checks out from active event (sets checked_out_at)
   - Sets users.available_for_assignment = FALSE
   - Closes any open tickets
   - Clears conversation state
3. Responds with confirmation

**Response**:
```
🏠 You're marked as HOME. Checked out and any open tickets have been closed. You won't receive new assignments until a manager re-enables you. Drive safe!
```

---

### Ticket Management Commands

#### `START` / `OMW` (On My Way)
**Purpose**: Begin a new service ticket

**Flow**:
1. User texts "START"
2. System fetches properties assigned to user
3. If 1 property:
   - Automatically creates ticket
   - Responds: "✅ Ticket started for [Property]..."
4. If multiple properties:
   - Lists properties with numbers
   - Sets state to 'awaiting_property'
   - Waits for property selection

**Response (multiple properties)**:
```
📋 Select property:
1. Main Street Plaza
2. Downtown Parking
3. Office Complex

Reply with the number.
```

**Property Selection**:
- User texts "1"
- System creates ticket for property 1
- Sets state to 'collecting_data'

---

#### `DONE` / `COMPLETE` / `FINISHED`
**Purpose**: Complete current ticket

**Flow**:
1. User texts "DONE"
2. System:
   - Finds active ticket
   - Sets end_time = NOW()
   - Calculates duration
   - Sets status = 'completed'
   - Clears conversation state
3. Responds with summary

**Response**:
```
✅ Ticket completed for Main Street Plaza!

Thank you. Reply START when you begin the next job.
```

---

### Data Collection (Natural Language)

While a ticket is active (state = 'collecting_data'), contractors can text natural language messages:

**Examples**:
```
"Plow truck 3 yards bulk salt"
"F350 salter 5 bags parking lot clear"
"Skid steer 2 yards bulk 3 bags calcium sidewalks done"
```

**ChatGPT Interpretation**:
The AI extracts:
- Equipment: "Plow truck", "F350", "Skid steer"
- Bulk salt: "3 yards", "2 yards"
- Bagged salt: "5 bags", "3 bags"
- Calcium: "3 bags calcium"
- Notes: "parking lot clear", "sidewalks done"

**Database Update**:
```sql
UPDATE winter_ops_log
SET equipment = 'Plow truck',
    bulk_salt_yards = 3.00,
    bags_applied = 0,
    calcium_bags = 0,
    notes = CONCAT(notes, '\n', 'parking lot clear')
WHERE id = <active_ticket_id>;
```

**Response**:
```
✅ Updated ticket for Main Street Plaza:
Equipment: Plow truck
Bulk salt: 3.0 yards

Reply DONE when finished, or send more updates.
```

---

## ChatGPT Integration

### API Configuration
**File**: `app/routes/sms_routes.py`

```python
from openai import OpenAI

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
```

### System Prompt
```python
system_prompt = """You are an AI assistant helping contractors manage winter service tickets via SMS.

Your job is to interpret natural language text messages and extract structured ticket information.

User messages may include:
- Equipment used: "plow truck", "skid steer", "loader", "salt truck", etc.
- Salt quantities: "3 yards bulk salt", "5 bags", "2 bags calcium"
- Notes: "parking lot clear", "sidewalks done", "driveway plowed"

Respond ONLY with valid JSON in this format:
{
  "intent": "update_ticket",
  "equipment": "extracted equipment or null",
  "bulk_salt_yards": number or null,
  "bags_applied": number or null,
  "calcium_bags": number or null,
  "notes": "extracted notes or null"
}
"""
```

### API Call
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{context_info}\nUser message: {user_message}"}
    ],
    temperature=0.3,
    max_tokens=500
)

response_text = response.choices[0].message.content.strip()
interpretation = json.loads(response_text)
```

### Example Interpretation

**Input**: "F350 plow 3 yards salt parking lot done"

**ChatGPT Output**:
```json
{
  "intent": "update_ticket",
  "equipment": "F350 plow",
  "bulk_salt_yards": 3.0,
  "bags_applied": null,
  "calcium_bags": null,
  "notes": "parking lot done"
}
```

---

## Conversation State Machine

```
[IDLE]
  ↓ (user texts "START")
[AWAITING_PROPERTY]
  ↓ (user texts "1" to select property)
[COLLECTING_DATA]
  ↓ (user texts equipment/salt/notes)
[COLLECTING_DATA]
  ↓ (user texts "DONE")
[IDLE]
```

### State: `idle`
- No active ticket
- Waiting for command (START, READY, HOME, HELP)

### State: `awaiting_property`
- User initiated START
- Waiting for property number selection
- context_data contains property list

### State: `collecting_data`
- Ticket is active
- Collecting equipment, salt, notes
- context_data contains:
  - active_ticket_id
  - active_property_id
  - property_name
  - partial_data (accumulated info)

---

## Data Flow Example

### Full Ticket Creation Flow

1. **Contractor texts**: "START"
2. **System queries**:
   ```sql
   SELECT id, name FROM properties WHERE assigned_to = <user_id>
   ```
3. **System responds**: "📋 Select property: 1. Main Street Plaza..."
4. **System updates**:
   ```sql
   UPDATE sms_conversations
   SET state = 'awaiting_property',
       context_data = '{"properties": [{"id": 1, "name": "Main Street Plaza"}]}'
   WHERE user_id = <user_id>;
   ```
5. **Contractor texts**: "1"
6. **System creates ticket**:
   ```sql
   INSERT INTO winter_ops_log (property_id, contractor_id, start_time, status)
   VALUES (1, <user_id>, NOW(), 'in_progress');
   ```
7. **System updates conversation**:
   ```sql
   UPDATE sms_conversations
   SET state = 'collecting_data',
       active_ticket_id = <new_ticket_id>,
       active_property_id = 1
   WHERE user_id = <user_id>;
   ```
8. **Contractor texts**: "Plow truck 3 yards salt"
9. **System calls ChatGPT** → Gets JSON interpretation
10. **System updates ticket**:
    ```sql
    UPDATE winter_ops_log
    SET equipment = 'Plow truck',
        bulk_salt_yards = 3.0
    WHERE id = <active_ticket_id>;
    ```
11. **Contractor texts**: "DONE"
12. **System completes ticket**:
    ```sql
    UPDATE winter_ops_log
    SET end_time = NOW(),
        duration_hours = TIMESTAMPDIFF(MINUTE, start_time, NOW()) / 60.0,
        status = 'completed'
    WHERE id = <active_ticket_id>;
    ```
13. **System resets conversation**:
    ```sql
    UPDATE sms_conversations
    SET state = 'idle',
        active_ticket_id = NULL,
        active_property_id = NULL,
        context_data = '{}'
    WHERE user_id = <user_id>;
    ```

---

## Error Handling

### Twilio Webhook Failure
- Twilio retries webhook up to 3 times
- Logged in Twilio console
- Check journalctl logs for errors

### ChatGPT API Failure
```python
except Exception as e:
    print(f"[ERROR] AI interpretation failed: {e}")
    return {
        "intent": "unknown",
        "error": str(e)
    }
```

**Fallback Response**: "🤔 I didn't understand that. Reply HELP for commands."

### Database Connection Error
- Connection pooling handles reconnection
- If persistent: logs error, returns generic message

### Invalid Property Selection
- User texts "99" but only 3 properties
- Response: "❌ Invalid selection. Please choose 1-3."

---

## Testing SMS Workflow

### Manual Test (via Twilio Console)
1. Go to Twilio Console → Phone Numbers
2. Select your Twilio number
3. Use "Test" feature to send SMS
4. Check webhook responses

### Curl Test (direct webhook)
```bash
curl -X POST https://snow-contractor.com/sms/webhook \
  -d "From=+15551234567" \
  -d "Body=START" \
  -d "MessageSid=SM123"
```

### Database Verification
```sql
-- Check conversation state
SELECT * FROM sms_conversations WHERE user_id = <user_id>;

-- Check messages
SELECT * FROM sms_messages WHERE conversation_id = <conv_id> ORDER BY created_at DESC;

-- Check active ticket
SELECT * FROM winter_ops_log WHERE contractor_id = <user_id> ORDER BY created_at DESC LIMIT 1;
```

---

## Monitoring & Logs

### Application Logs
```bash
journalctl -u contractor-portal -f | grep SMS
```

### Twilio Logs
- Twilio Console → Monitor → Logs → Messaging
- Shows delivery status, errors

### ChatGPT API Logs
- No built-in logging from OpenAI
- Application logs API calls in journalctl

---

## Cost Estimation

### Twilio Costs
- **Inbound SMS**: $0.0075 per message
- **Outbound SMS**: $0.0079 per message
- **Phone number**: $1.15/month

**Example**: 100 messages/day (50 in, 50 out)
- Daily: (50 × $0.0075) + (50 × $0.0079) = $0.77
- Monthly: ~$23

### OpenAI Costs (gpt-4o-mini)
- **Input**: $0.150 / 1M tokens
- **Output**: $0.600 / 1M tokens

**Average SMS interpretation**:
- Input: ~200 tokens (system prompt + context + message)
- Output: ~100 tokens (JSON response)
- Cost: ~$0.00009 per message

**Example**: 50 AI calls/day
- Daily: ~$0.0045
- Monthly: ~$0.14

**Total Monthly**: ~$23 + $0.14 = **~$23.14**

---

## Security

### Webhook Validation
```python
# TODO: Implement Twilio signature validation
# Validates webhook came from Twilio
```

### Phone Number Verification
```python
# Check user exists
user = fetch_query("SELECT * FROM users WHERE phone = %s", (from_number,))
if not user:
    return "❌ Phone number not registered."
```

### API Key Security
- Keys stored in environment variables
- Not exposed to frontend
- Server-side only

---

## Future Enhancements

1. **Photo Uploads**: MMS support for before/after photos
2. **Voice Notes**: Transcription via OpenAI Whisper
3. **Automated Reminders**: "You've been working for 4 hours, don't forget to log salt usage"
4. **Smart Property Detection**: GPS-based automatic property detection
5. **Multi-language**: Spanish support for SMS commands
6. **Broadcast Messages**: Send alerts to all checked-in contractors

---

## Troubleshooting

### SMS Not Received by System
1. Check Twilio webhook configuration
2. Verify webhook URL: https://snow-contractor.com/sms/webhook
3. Check nginx logs: `tail -f /var/log/nginx/access.log`
4. Check app logs: `journalctl -u contractor-portal -f`

### SMS Not Sent to Contractor
1. Check Twilio console for delivery status
2. Verify phone number format (+1XXXXXXXXXX)
3. Check Twilio account balance

### ChatGPT Not Interpreting Correctly
1. Check OpenAI API key validity
2. Review system prompt in sms_routes.py
3. Increase temperature for more creative responses
4. Check token limits (max_tokens=500)

### Ticket Not Created
1. Check if user has assigned properties
2. Verify conversation state in sms_conversations
3. Check winter_ops_log for partial tickets
4. Review database constraints (foreign keys)
