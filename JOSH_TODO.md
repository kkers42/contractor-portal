# Josh's Todo List

**Last Updated**: 2025-12-23

---

## 🔴 HIGH PRIORITY - Required for Monitoring System

### 1. Get Anthropic API Key
- [ ] Sign up at https://console.anthropic.com/
- [ ] Create API key
- [ ] Copy the key (starts with `sk-ant-`)
- [ ] Provide key to add to monitoring agent service file

### 2. Setup N8N Webhook
- [ ] Log into your N8N instance
- [ ] Create new workflow
- [ ] Add Webhook node (POST)
- [ ] Copy the webhook URL
- [ ] Provide URL for monitoring agent configuration

### 3. Create Discord Webhook
- [ ] Go to your Discord server
- [ ] Create channel: `#monitoring-alerts`
- [ ] Channel Settings → Integrations → Webhooks
- [ ] Create New Webhook named "Monitoring Agent"
- [ ] Copy webhook URL
- [ ] Provide URL for N8N configuration

### 4. Configure Email for Critical Alerts
- [ ] Decide which email to use for critical alerts
- [ ] Provide SMTP credentials if using custom email
- [ ] Or use existing email service

---

## 🟡 MEDIUM PRIORITY - Nice to Have

### 5. Add Phone Numbers to Users
- [ ] Decide which contractors should have SMS enabled
- [ ] Collect phone numbers (format: +1234567890)
- [ ] Update users table with phone numbers

### 6. GitHub Integration (Optional)
- [ ] Create GitHub repo for bug tracking (or use existing)
- [ ] Generate GitHub Personal Access Token
- [ ] Configure in N8N workflow

### 7. Google Sheets Logging (Optional)
- [ ] Create Google Sheet for monitoring logs
- [ ] Share sheet with N8N service account
- [ ] Provide Sheet ID

---

## 🟢 LOW PRIORITY - Future Enhancements

### 8. Test Monitoring System
- [ ] After setup, trigger a test alert
- [ ] Verify Discord notification received
- [ ] Check email alert for critical issues

### 9. Adjust Monitoring Frequency
- [ ] Default is 5 minutes
- [ ] Decide if you want more/less frequent checks
- [ ] Current: Every 5 min = 288 checks/day

### 10. Configure Alert Preferences
- [ ] Which severities should ping you at night?
- [ ] Setup Discord quiet hours if needed
- [ ] Adjust what gets emailed vs Discord only

---

## ✅ COMPLETED
- [x] Event Check-In system built
- [x] SMS system switched to ChatGPT
- [x] Monitoring agent created
- [x] Discord integration configured
- [x] Property Board filters (Lists & Routes)
- [x] Clear All Contractors button
- [x] Default equipment for users
- [x] User Profile page created (Phone Number, Address, Default Equipment)
- [x] Comprehensive workflow documentation created in workflows/ folder

---

## 📝 NOTES

**DEFINITIONS**:
- **Person**: Any single account holder/sign-in (User, Admin, Contractor, Subcontractor, Manager, etc.)

**AI ROLES**:
- **Anthropic (Claude)**:
  - Backbone & main code
  - GitHub integration & bug fixes
  - Revision control
  - Backend monitoring & self-healing
  - Create documents
  - Communicate with lead developer (Josh)

- **ChatGPT (OpenAI)**:
  - Frontend communication with persons
  - Update and edit database
  - Chatbot functionality
  - AI logic for frontend tools
  - Workflow documents
  - Database operations
  - Invoicing assistance
  - Google search & general LLM queries

- **Gemini (Google)**: TBD (likely similar to ChatGPT's role)

**API Keys Needed**:
1. Anthropic API Key (for monitoring agent)
2. OpenAI API Key (already configured for SMS)
3. Twilio credentials (already configured for SMS)

**Current Status**:
- ✅ Check-in system is live
- ✅ SMS using ChatGPT
- ⏳ Monitoring agent ready to deploy (needs API keys)
- ⏳ N8N workflow ready (needs webhook URLs)

---

## 🎯 NEXT SESSION CHECKLIST

When you're ready to deploy monitoring:
1. Provide Anthropic API key
2. Provide N8N webhook URL
3. Provide Discord webhook URL
4. I'll deploy monitoring agent
5. Test the system
6. You're at 100% uptime!
