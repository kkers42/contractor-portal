# Discord Integration for Monitoring Alerts

## Why Discord is Better for You:

✅ **You already have it** - No new accounts needed
✅ **Better mobile notifications** - Instant push alerts
✅ **Rich embeds** - Color-coded severity levels
✅ **Free forever** - No paid plans needed
✅ **Easy webhooks** - Simple setup

## Recommended Setup: Discord + Email

**Use Discord for**:
- ✅ Auto-repair notifications (green = success)
- ⚠️ Medium severity issues
- 📊 Daily health summaries

**Use Email for**:
- 🚨 CRITICAL issues only
- Bug reports requiring immediate action
- End-of-day summary reports

This way you get:
- **Instant Discord pings** for normal operations
- **Email alerts** only when you REALLY need to check something

## Setting Up Discord Webhooks

### Step 1: Create a Server Channel

1. Open your Discord server
2. Create a new text channel called `#monitoring-alerts`
3. Right-click the channel → **Edit Channel**
4. Go to **Integrations** → **Webhooks**
5. Click **New Webhook**
6. Name it: `Monitoring Agent`
7. **Copy the Webhook URL** (looks like: `https://discord.com/api/webhooks/123456789/abc...`)

### Step 2: Configure in N8N

In your N8N workflow:
1. Find the "Send Discord Notification" node
2. Paste your webhook URL into the `webhookUri` field
3. Activate the workflow

### Step 3: Test It

Send a test webhook:
```bash
curl -X POST "YOUR_DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "embeds": [{
      "title": "✅ Test Alert",
      "description": "Monitoring system is working!",
      "color": 65280,
      "fields": [
        {"name": "Status", "value": "All systems operational", "inline": true},
        {"name": "Test", "value": "Success", "inline": true}
      ]
    }]
  }'
```

You should see a message appear in your `#monitoring-alerts` channel!

## What Discord Messages Look Like

### Auto-Repair Success (Green)
```
✅ Auto-Repair Completed
Service crashed and was restarted

Severity: MEDIUM
Type: auto_repair
Actions Taken:
  ✅ Restarted contractor-portal service
  ✅ Verified service is running
Timestamp: 2025-12-23T14:30:00Z
```

### Critical Issue (Red)
```
🚨 Issue Detected
Database connection pool exhausted

Severity: CRITICAL
Type: bug_report
Actions Taken:
  None (requires manual intervention)
Timestamp: 2025-12-23T14:35:00Z
```

### High Severity (Orange)
```
⚠️ Issue Detected
Disk usage at 92%

Severity: HIGH
Type: auto_repair
Actions Taken:
  ✅ Cleaned old log files
  ✅ Freed 2.5GB disk space
Timestamp: 2025-12-23T14:40:00Z
```

## Color Codes

- 🟢 **Green (65280)** - Success, low severity, all good
- 🟠 **Orange (16744192)** - High severity, attention needed
- 🔴 **Red (16711680)** - Critical, immediate action required

## Recommended Discord Settings

### For Mobile:

1. Open Discord mobile app
2. Go to **Settings** → **Notifications**
3. Enable **Push Notifications**
4. Go to your server → **Notification Settings**
5. Set `#monitoring-alerts` to **All Messages**
6. Enable **Mobile Push Notifications**

### For Desktop:

1. Right-click `#monitoring-alerts` channel
2. **Notification Settings**
3. Set to **All Messages**
4. Enable **Desktop Notifications**

### Quiet Hours (Optional):

If you don't want alerts at night:
1. Discord → **User Settings** → **Notifications**
2. Enable **Suppress @everyone and @here**
3. Or use **Do Not Disturb** mode during sleep hours

## Multi-Channel Setup (Advanced)

You can create different channels for different severity levels:

- `#critical-alerts` - Only critical issues (red)
- `#auto-repairs` - Successful auto-fixes (green)
- `#health-reports` - Daily/hourly summaries

Just create multiple webhooks and configure the N8N workflow to route based on severity.

## Email + Discord Combo

**Recommended N8N Flow**:

```
Issue Detected
    ↓
┌───┴────┐
│ CRITICAL?
└───┬────┘
    ├─ YES → Send Email + Discord
    └─ NO  → Send Discord only
```

This way:
- **Normal issues** = Discord notification (you'll see it when you check)
- **Critical issues** = Email + Discord (immediate attention)

## Discord vs Slack

**Discord Advantages**:
- Free forever (no message limits)
- Better mobile app
- You already use it
- No paid plans needed
- Rich embeds out of the box

**Slack Advantages**:
- More business-oriented
- Better enterprise integrations
- Searchable message history UI

For a small operation like yours, **Discord is perfect**. No need for Slack.

## Testing Your Setup

After configuring N8N:

1. Trigger a test alert from N8N
2. Check your Discord `#monitoring-alerts` channel
3. Verify colors are showing correctly
4. Test mobile notification

You should get instant notifications!

## Troubleshooting

**Not receiving Discord messages?**
- Check webhook URL is correct
- Verify N8N workflow is active
- Check Discord channel permissions
- Test webhook with curl command above

**Too many notifications?**
- Adjust monitoring frequency (default 5 min)
- Filter out low-severity in N8N
- Use quiet hours in Discord

**Want to @mention yourself?**
Add this to the Discord node in N8N:
```json
"content": "<@YOUR_DISCORD_USER_ID> 🚨 Critical Alert!"
```

Find your User ID: Right-click your name → Copy ID (enable Developer Mode first)
