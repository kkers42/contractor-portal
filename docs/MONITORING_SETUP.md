# Monitoring Agent Setup Guide

## Overview

The Monitoring Agent uses **Claude (Anthropic AI)** to:
- Monitor application health 24/7
- Diagnose issues automatically
- Perform safe auto-repairs
- Create bug reports in N8N for manual intervention
- Maintain 100% uptime

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Monitoring Agent                         │
│                  (monitoring_agent.py)                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├─→ Health Checks (Every 5 min)
               │   ├─ Web server responding?
               │   ├─ API endpoints working?
               │   ├─ Database connected?
               │   ├─ Service running?
               │   ├─ Disk space OK?
               │   └─ Memory usage OK?
               │
               ├─→ Claude AI Diagnosis
               │   ├─ Analyze errors
               │   ├─ Determine root cause
               │   ├─ Assess severity
               │   └─ Generate repair plan
               │
               ├─→ Auto-Repair (if safe)
               │   ├─ Restart service
               │   ├─ Clear temp files
               │   ├─ Reset connections
               │   └─ Fix permissions
               │
               └─→ N8N Integration
                   ├─ Bug reports (manual needed)
                   ├─ Repair notifications
                   └─ Health summaries
```

## Installation Steps

### 1. Install Anthropic Library on Server

```bash
ssh root@72.61.0.186
cd /opt/contractor-portal
source venv/bin/activate
pip install anthropic
```

### 2. Upload Monitoring Agent

```bash
# From local machine
scp "r:\Contractor App\app\services\monitoring_agent.py" root@72.61.0.186:/opt/contractor-portal/app/services/monitoring_agent.py
scp "r:\Contractor App\monitoring-agent.service" root@72.61.0.186:/etc/systemd/system/monitoring-agent.service
```

### 3. Configure Environment Variables

Edit the service file on the server:

```bash
ssh root@72.61.0.186
nano /etc/systemd/system/monitoring-agent.service
```

Update these values:
```ini
Environment="ANTHROPIC_API_KEY=sk-ant-your-actual-key-here"
Environment="N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/contractor-monitoring"
Environment="APP_URL=https://snow-contractor.com"
Environment="SERVER_HOST=72.61.0.186"
```

### 4. Create Log Directory

```bash
ssh root@72.61.0.186
touch /var/log/monitoring-agent.log
chmod 644 /var/log/monitoring-agent.log
```

### 5. Start the Monitoring Agent

```bash
ssh root@72.61.0.186
systemctl daemon-reload
systemctl enable monitoring-agent
systemctl start monitoring-agent
systemctl status monitoring-agent
```

### 6. Setup N8N Workflow

1. Log into your N8N instance
2. Create new workflow
3. Add a Webhook node (POST method)
4. Copy the webhook URL
5. Import the template from `docs/n8n-monitoring-workflow.json`
6. Configure integrations:
   - Discord webhook (for instant alerts) - See `docs/DISCORD_SETUP.md`
   - GitHub (for bug tracking)
   - Email (for critical alerts)
   - Google Sheets (for logging)

## What the Agent Monitors

### Health Checks (Every 5 minutes)

1. **Web Server**
   - Can users access the site?
   - Is login page loading?

2. **API Endpoints**
   - Are endpoints responding?
   - Any 500 errors?
   - Timeout issues?

3. **Database**
   - Can connect to MySQL?
   - Queries executing?

4. **System Service**
   - Is contractor-portal.service running?
   - Process healthy?

5. **Resources**
   - Disk space < 90%?
   - Memory usage < 90%?

### Auto-Repair Capabilities

The agent can automatically fix:

✅ **Safe Auto-Repairs**:
- Restart crashed service
- Clear temporary files
- Reset stuck database connections
- Fix file permissions
- Clear log files (if disk full)

❌ **Requires Manual Intervention**:
- Database corruption
- Code errors/bugs
- Configuration issues
- Security breaches
- Hardware failures

## How It Works

### Example Scenario 1: Service Crash

```
1. Health check detects service down
2. Claude analyzes: "Service crashed, safe to restart"
3. Agent executes: systemctl restart contractor-portal
4. Service back up in 5 seconds
5. Notification sent to N8N: "Auto-repaired service crash"
```

### Example Scenario 2: Database Error

```
1. Health check detects 500 errors on API
2. Claude analyzes: "Database connection pool exhausted"
3. Claude determines: Manual intervention needed
4. Agent creates bug report in N8N
5. N8N creates GitHub issue
6. Email sent to admin
7. Agent monitors until fixed
```

### Example Scenario 3: Disk Full

```
1. Health check detects 95% disk usage
2. Claude analyzes: "Disk full, log files growing"
3. Claude suggests: Rotate and compress old logs
4. Agent executes cleanup commands
5. Disk usage drops to 70%
6. Notification sent: "Auto-cleared 2GB logs"
```

## Monitoring the Monitor

Check agent status:
```bash
systemctl status monitoring-agent
```

View logs:
```bash
tail -f /var/log/monitoring-agent.log
```

Manual test:
```bash
/opt/contractor-portal/venv/bin/python3 /opt/contractor-portal/app/services/monitoring_agent.py
```

## N8N Workflow Actions

When the agent detects issues:

**Bug Report** (Manual intervention needed):
- Creates GitHub issue with full diagnostics
- Sends email to admin
- Sends Discord alert (red embed)
- Logs to Google Sheets

**Auto-Repair** (Fixed automatically):
- Sends Discord notification (green embed)
- Logs repair actions
- Updates tracking sheet

## Security Considerations

The monitoring agent has **root access** to the server via SSH. This is necessary for:
- Restarting services
- Checking system resources
- Modifying files

**Safety measures**:
- Only executes "safe" commands approved by Claude
- Logs all actions
- Risk assessment for each repair
- Manual approval required for high-risk actions

## Cost Estimation

**Anthropic API Usage**:
- Health check every 5 minutes = 288 checks/day
- Each check with errors = ~1,000 tokens
- Monthly cost: ~$5-10 (assuming some errors)

**Benefits**:
- 100% uptime target
- Automatic issue resolution
- Instant response to problems
- Reduced manual monitoring

## Troubleshooting

**Agent not starting?**
```bash
journalctl -u monitoring-agent -n 50
```

**Anthropic API errors?**
- Check API key is valid
- Verify key has sufficient credits

**N8N not receiving webhooks?**
- Test webhook URL manually
- Check firewall rules
- Verify N8N workflow is active

## Next Steps

After setup:
1. Monitor for 24 hours
2. Review auto-repair actions
3. Adjust sensitivity if needed
4. Configure alert preferences in N8N
5. Add custom health checks as needed
