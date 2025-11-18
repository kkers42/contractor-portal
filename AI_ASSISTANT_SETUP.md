# AI Assistant Setup Guide

## Overview
The Contractor Portal now includes an AI-powered chatbot assistant that helps users with:
- Filling out forms and logs
- Finding property information
- Managing active tickets
- Answering questions about equipment and procedures

## Features

### 🤖 Context-Aware Assistant
- Knows which page the user is on
- Understands user's assigned properties
- Tracks active tickets
- Provides relevant suggestions

### 💬 Conversational Interface
- Floating chat button (bottom-right corner)
- Clean, dark-themed UI matching portal style
- Quick suggestion buttons
- Persistent chat history during session

### 🧠 Smart Capabilities
- Uses OpenAI GPT-4o-mini (fast and cost-effective)
- Context includes user role, properties, and active work
- Page-specific guidance (WinterOpsLog, MyTickets, etc.)
- Natural language understanding

## Setup Instructions

### Step 1: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. **Save it securely** - you won't see it again!

### Step 2: Configure Environment Variable

#### On VPS (Production)
```bash
# SSH into your VPS
ssh root@72.61.0.186

# Add to environment file
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> /opt/contractor-portal/.env

# Or edit systemd service file
nano /etc/systemd/system/contractor-portal.service

# Add this line in [Service] section:
Environment="OPENAI_API_KEY=sk-your-key-here"

# Reload and restart
systemctl daemon-reload
systemctl restart contractor-portal
```

#### Local Development
```bash
# Add to .env file in app directory
echo 'OPENAI_API_KEY=sk-your-key-here' >> app/.env

# Or export directly
export OPENAI_API_KEY="sk-your-key-here"
```

### Step 3: Add Widget to Pages

Add this script tag to any HTML page where you want the AI assistant:

```html
<!-- Before closing </body> tag -->
<script src="/static/ai-chat-widget.js"></script>
```

**Recommended pages:**
- WinterOpsLog.html ✅ (help with form filling)
- GreenOpsLog.html ✅ (help with form filling)
- MyTickets.html ✅ (help with ticket management)
- PropertyInfo.html ✅ (help finding properties)
- UserDashboard.html ✅ (general assistance)
- AdminDashboard.html ✅ (general assistance)
- ManagerDashboard.html ✅ (general assistance)

### Step 4: Test the Assistant

1. Open any page with the widget
2. Look for purple gradient button (🤖) in bottom-right
3. Click to open chat window
4. Try a suggestion or ask a question
5. Verify it responds appropriately

## Cost Estimation

### GPT-4o-mini Pricing
- **Input**: $0.150 per 1M tokens (~750k words)
- **Output**: $0.600 per 1M tokens (~750k words)

### Real-World Usage
For a typical contractor portal with 10 active users:

- **Light usage** (10 questions/day): ~$2-5/month
- **Medium usage** (50 questions/day): ~$10-20/month
- **Heavy usage** (200 questions/day): ~$40-80/month

Each conversation typically uses:
- System prompt: ~200 tokens
- User question: ~50 tokens
- AI response: ~150 tokens
- **Total**: ~400 tokens (~$0.0002 per conversation)

## API Endpoints

### POST `/ai/chat/`
Chat with the AI assistant

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "How do I start a ticket?"}
  ],
  "page_context": "MyTickets"
}
```

**Response:**
```json
{
  "message": "To start a ticket, find the property in your list and click the 'Start Ticket' button...",
  "suggestions": []
}
```

### GET `/ai/suggestions/?page=MyTickets`
Get context-aware suggestion prompts

**Response:**
```json
{
  "suggestions": [
    "Which properties need service today?",
    "How do I start a ticket?",
    "Show me my ticket history"
  ]
}
```

## Troubleshooting

### "AI assistant is not configured"
- **Cause**: OPENAI_API_KEY environment variable not set
- **Fix**: Follow Step 2 above

### "AI assistant timed out"
- **Cause**: OpenAI API taking too long (>30 seconds)
- **Fix**: Check internet connection, try again

### "AI request failed"
- **Cause**: Invalid API key or quota exceeded
- **Fix**:
  - Verify API key is correct
  - Check OpenAI dashboard for quota/billing issues

### Chat button not appearing
- **Cause**: Widget script not loaded
- **Fix**: Add `<script src="/static/ai-chat-widget.js"></script>` to page

## Security Notes

1. **API Key Protection**
   - Never commit API key to git
   - Use environment variables only
   - Keep `.env` files in `.gitignore`

2. **User Authentication**
   - All AI endpoints require valid JWT token
   - Users can only access their own context (properties, tickets)

3. **Rate Limiting** (TODO - Phase 2)
   - Consider adding rate limits per user
   - Prevent abuse/excessive costs

## Future Enhancements (Phase 2)

### Monitoring & Self-Healing
- AI monitors application logs
- Detects errors/issues automatically
- Sends alerts to N8N webhook
- Auto-fix common problems (database locks, service crashes)
- Text notifications when issues are resolved

### Advanced Features
- Voice input/output
- Proactive suggestions ("Snow forecasted, here are your properties")
- Multi-language support
- Image analysis (damage assessment photos)
- Integration with weather APIs

## Files Created

- `app/routes/ai_routes.py` - Backend API endpoints
- `app/static/ai-chat-widget.js` - Frontend chat widget
- `AI_ASSISTANT_SETUP.md` - This documentation

## Files Modified

- `app/main.py` - Added ai_routes router

## Dependencies

The AI assistant uses built-in Python libraries plus:
- `httpx` - Already in requirements.txt for async HTTP requests
- No new dependencies needed!

---

**Status**: ✅ Ready for deployment (just needs OpenAI API key)
**Cost**: ~$5-20/month for typical usage
**Next Step**: Add API key and deploy to production
