# ⚡ Tomorrow Morning Quick Start - AI Assistant

## 🎯 What I Built Tonight

**AI Chatbot Assistant** - Complete and deployed to production!
- 🤖 Floating purple button on 7 key pages
- 💬 Context-aware help (knows user, properties, tickets)
- 🧠 Uses OpenAI GPT-4o-mini
- 💰 Costs ~$5-20/month

## ⏱️ 10-Minute Setup

### 1️⃣ Get API Key (5 min)
```
https://platform.openai.com/api-keys
→ "Create new secret key"
→ Copy key (starts with sk-...)
```

### 2️⃣ Add to VPS (3 min)
```bash
ssh root@72.61.0.186
nano /etc/systemd/system/contractor-portal.service

# Add this line in [Service] section:
Environment="OPENAI_API_KEY=sk-your-key-here"

# Save and restart
systemctl daemon-reload
systemctl restart contractor-portal
```

### 3️⃣ Test (2 min)
```
https://snow-contractor.com/static/MyTickets.html
→ Click purple 🤖 button (bottom-right)
→ Ask: "How do I start a ticket?"
→ Should respond!
```

## 📋 GitHub Push Fix

GitHub blocked push due to old secrets. To fix:

**Option A**: Allow the secrets
- Visit: https://github.com/kkers42/contractor-portal/security/secret-scanning/unblock-secret/35eNd33jLHGcWcPipxwR3e8qQqB
- Visit: https://github.com/kkers42/contractor-portal/security/secret-scanning/unblock-secret/35eNcxwOSD7ehGGlwOQymCHWw1v
- Then: `git push origin feature/mcp-web-portal`

**Option B**: New clean branch
```bash
git checkout main
git pull
git checkout -b feature/ai-assistant
git cherry-pick 33cbb37 e9a4ba4 846d890
git push origin feature/ai-assistant
```

## 📚 Full Docs

- **AI_DEPLOYMENT_SUMMARY.md** - Everything that was built
- **AI_ASSISTANT_SETUP.md** - Detailed setup & troubleshooting

## ✅ Status

- ✅ Backend deployed
- ✅ Frontend deployed
- ✅ Service restarted
- ⏳ **Needs**: OPENAI_API_KEY

That's it! You're ready to go. 🚀

Sleep well! - Claude Code
