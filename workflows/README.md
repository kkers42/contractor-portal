# Workflow Documentation

**Last Updated**: 2025-12-23

Welcome to the Contractor Portal workflow documentation. This directory contains comprehensive technical documentation about how the entire system works.

---

## 📚 Documentation Index

### 1. [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)
**The Big Picture** - Start here for overall system understanding

**Contents**:
- Technology stack (FastAPI, MySQL, Nginx)
- Network architecture and ports
- Directory structure
- Data flow diagrams
- External integrations (Twilio, OpenAI, Anthropic, N8N)
- Environment variables
- Deployment process
- Security overview
- Monitoring and logging
- Troubleshooting

**For**: Developers, DevOps, AI assistants learning the system

---

### 2. [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)
**The Data Model** - Complete database documentation

**Contents**:
- All table structures with column descriptions
- Primary keys and foreign keys
- Indexes and relationships
- Entity relationship diagrams
- Common queries
- Data types explained
- Migration history
- Backup strategies

**For**: Backend developers, database administrators, data analysts

---

### 3. [SMS_WORKFLOW.md](./SMS_WORKFLOW.md)
**Text Message System** - How contractors communicate via SMS

**Contents**:
- Twilio integration
- ChatGPT AI interpretation
- SMS commands (READY, START, DONE, HOME, WORKING)
- Conversation state machine
- Natural language data collection
- Ticket creation via SMS
- Cost estimation
- Testing procedures

**For**: Frontend developers, AI integrators, support staff

---

### 4. [WINTER_EVENT_WORKFLOW.md](./WINTER_EVENT_WORKFLOW.md)
**Snow Storm Operations** - End-to-end event management

**Contents**:
- Event lifecycle (pending → active → completed)
- Contractor check-in process
- Property assignment
- Service ticket creation
- Status updates and monitoring
- Event completion
- Business rules and validations
- Reporting

**For**: Managers, operations staff, developers

---

### 5. [AI_INTEGRATION.md](./AI_INTEGRATION.md)
**Artificial Intelligence** - How AI powers the system

**Contents**:
- ChatGPT vs Claude (role separation)
- SMS message interpretation with GPT-4o-mini
- Monitoring and self-healing with Claude-3.5-sonnet
- AI chat widget for user suggestions
- Token usage and costs (~$10/month total)
- Prompt engineering best practices
- Error handling and rate limits
- Future AI enhancements

**For**: AI developers, ChatGPT assistants, cost analysts

---

## 🎯 Quick Navigation

### I want to understand...

**"How does the whole system work?"**
→ Start with [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)

**"What data do we store?"**
→ Read [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)

**"How do contractors send text messages?"**
→ See [SMS_WORKFLOW.md](./SMS_WORKFLOW.md)

**"How do we manage snow storms?"**
→ Check [WINTER_EVENT_WORKFLOW.md](./WINTER_EVENT_WORKFLOW.md)

**"How does AI work in this app?"**
→ Review [AI_INTEGRATION.md](./AI_INTEGRATION.md)

**"How do I set up monitoring?"**
→ See [../docs/MONITORING_SETUP.md](../docs/MONITORING_SETUP.md)

**"How do I configure Discord alerts?"**
→ See [../docs/DISCORD_SETUP.md](../docs/DISCORD_SETUP.md)

---

## 🤖 For AI Assistants (ChatGPT, etc.)

If you're an AI helping a user with this system:

### Before Answering Questions:
1. Read [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) for overall context
2. Check [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for data structure
3. Reference specific workflows for detailed processes

### Common User Questions:

**"How do I add a new property?"**
→ Properties table in DATABASE_SCHEMA.md, PropertyInfo.html in frontend

**"Why isn't my SMS working?"**
→ SMS_WORKFLOW.md, check Twilio configuration, verify phone number in users table

**"How do I create a winter event?"**
→ WINTER_EVENT_WORKFLOW.md, use ManageWinterEvents.html

**"What does 'checked_in' status mean?"**
→ WINTER_EVENT_WORKFLOW.md, event_checkins table in DATABASE_SCHEMA.md

**"How much does AI cost per month?"**
→ AI_INTEGRATION.md - Token Usage & Costs section (~$10/month total)

### When Updating Code:
1. Check DATABASE_SCHEMA.md for table structure
2. Follow patterns in SYSTEM_ARCHITECTURE.md
3. Update relevant workflow docs if changing functionality
4. Test SMS flows if touching sms_routes.py
5. Verify winter event flows if touching winter_event_routes.py

---

## 🏗️ System Components Map

```
┌─────────────────────────────────────────────────────────┐
│                   CONTRACTOR PORTAL                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Frontend (HTML/JS)                Backend (FastAPI)    │
│  ├── AdminDashboard.html          ├── main.py           │
│  ├── ManagerDashboard.html        ├── auth.py           │
│  ├── UserDashboard.html           ├── db.py             │
│  ├── UserProfile.html             └── routes/           │
│  ├── PropertyBoard.html               ├── auth_routes   │
│  ├── WinterOpsLog.html                ├── sms_routes    │
│  ├── EventCheckIn.html                ├── ops_routes    │
│  └── ... (50+ pages)                  └── ...           │
│                                                          │
│  Database (MySQL)                 Services               │
│  ├── users                        ├── monitoring_agent  │
│  ├── properties                   └── (systemd)         │
│  ├── winter_events                                      │
│  ├── event_checkins              External APIs          │
│  ├── winter_ops_log              ├── Twilio (SMS)       │
│  ├── sms_conversations            ├── OpenAI (ChatGPT)  │
│  └── ... (15+ tables)             ├── Anthropic (Claude)│
│                                    ├── N8N (Workflows)   │
│                                    └── Weather API       │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Workflow Checklists

### Adding a New Feature

- [ ] Read SYSTEM_ARCHITECTURE.md to understand where it fits
- [ ] Check DATABASE_SCHEMA.md if database changes needed
- [ ] Create migration SQL file if adding/modifying tables
- [ ] Implement backend route in appropriate routes/*.py file
- [ ] Create/update frontend HTML page
- [ ] Test with different user roles (Admin, Manager, User)
- [ ] Update relevant workflow documentation
- [ ] Add to JOSH_TODO.md completed section

### Debugging an Issue

- [ ] Check server logs: `journalctl -u contractor-portal -f`
- [ ] Review DATABASE_SCHEMA.md for table structure
- [ ] Check SYSTEM_ARCHITECTURE.md for data flow
- [ ] Verify environment variables in .env
- [ ] Test API endpoint directly with curl
- [ ] Check Nginx logs if 502/504 errors
- [ ] Review specific workflow doc (SMS, Winter Event, etc.)

### Deploying Code

- [ ] Test locally first (if applicable)
- [ ] Upload via SCP to server
- [ ] Restart service: `systemctl restart contractor-portal`
- [ ] Check status: `systemctl status contractor-portal`
- [ ] Verify in browser / test endpoint
- [ ] Monitor logs for errors
- [ ] Update documentation if behavior changed

---

## 🔧 Development Workflow

### For Josh (Lead Developer):
1. Describe task to Claude (me)
2. I implement solution
3. I upload to server
4. I restart services
5. I verify functionality
6. I update documentation
7. You test on mobile/browser
8. You approve or request changes

### For ChatGPT (Frontend Assistant):
1. User asks question
2. Read relevant workflow docs
3. Understand current system state
4. Provide accurate, helpful answer
5. Suggest next steps
6. Don't make assumptions - check docs!

---

## 📊 Key Metrics

### Performance Targets
- **Uptime**: 99.9% (self-healing monitoring)
- **API Response**: < 200ms average
- **SMS Response**: < 5 seconds
- **Database Queries**: < 100ms

### Usage Stats
- **Active Users**: ~20-50 contractors
- **Properties**: ~200 locations
- **SMS Messages**: ~50-100/day during events
- **AI API Calls**: ~400/day (SMS + suggestions + monitoring)
- **Storage**: ~500MB database

### Costs
- **Server**: $10-20/month (VPS)
- **Twilio**: ~$23/month (SMS)
- **OpenAI**: ~$0.35/month (ChatGPT)
- **Anthropic**: ~$9.50/month (Claude monitoring)
- **Total**: ~$43/month

---

## 📞 Support Resources

### Internal Documentation
- [../JOSH_TODO.md](../JOSH_TODO.md) - Current tasks and status
- [../docs/MONITORING_SETUP.md](../docs/MONITORING_SETUP.md) - Monitoring setup
- [../docs/DISCORD_SETUP.md](../docs/DISCORD_SETUP.md) - Discord webhooks

### External Resources
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [MySQL Docs](https://dev.mysql.com/doc/)
- [Twilio Docs](https://www.twilio.com/docs)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)

### Getting Help
- **Technical Issues**: Check logs first, then review relevant workflow doc
- **Database Questions**: DATABASE_SCHEMA.md has all table structures
- **API Errors**: SYSTEM_ARCHITECTURE.md has troubleshooting section
- **AI Questions**: AI_INTEGRATION.md covers all AI providers

---

## 🎓 Learning Path

### New Developer Onboarding

**Day 1**: System Overview
- Read SYSTEM_ARCHITECTURE.md
- Set up local development environment
- SSH into server, explore directory structure
- Review database in MySQL

**Day 2**: Data Model
- Study DATABASE_SCHEMA.md
- Run sample queries
- Understand relationships
- Explore tables in MySQL Workbench

**Day 3**: Core Workflows
- Read WINTER_EVENT_WORKFLOW.md
- Understand event lifecycle
- Test creating an event
- Assign properties to contractors

**Day 4**: SMS System
- Read SMS_WORKFLOW.md
- Test SMS commands via Twilio Console
- Understand conversation state machine
- Review ChatGPT integration

**Day 5**: AI & Monitoring
- Read AI_INTEGRATION.md
- Understand role separation (ChatGPT vs Claude)
- Review monitoring agent code
- Set up N8N workflow (if applicable)

**Week 2**: Hands-on Development
- Pick a small feature from JOSH_TODO.md
- Implement with guidance
- Deploy to server
- Update documentation

---

## 🚀 Next Steps

After reading these docs, you should be able to:

✅ Understand how the entire system works
✅ Navigate the codebase confidently
✅ Debug issues using logs and docs
✅ Add new features following established patterns
✅ Help users via ChatGPT with accurate information
✅ Set up monitoring and integrations
✅ Optimize AI usage and costs

**Ready to contribute?** Check [../JOSH_TODO.md](../JOSH_TODO.md) for current tasks!

---

## 📝 Document Maintenance

### Keeping Docs Up to Date

**When to Update**:
- Database schema changes → Update DATABASE_SCHEMA.md
- New API endpoint → Update SYSTEM_ARCHITECTURE.md
- SMS command added → Update SMS_WORKFLOW.md
- Winter event flow changes → Update WINTER_EVENT_WORKFLOW.md
- New AI integration → Update AI_INTEGRATION.md

**How to Update**:
1. Edit the relevant .md file
2. Update "Last Updated" date
3. Add to changelog if major change
4. Commit to git with descriptive message

---

## 💡 Tips for Success

### For Developers:
- **Read docs before coding** - Avoid reinventing existing features
- **Follow established patterns** - Consistency is key
- **Test on mobile** - Many users are contractors in trucks
- **Log everything** - Makes debugging much easier
- **Update docs** - Future you will thank you

### For AI Assistants:
- **Always check docs first** - Don't guess or assume
- **Reference specific sections** - Help users find info themselves
- **Ask clarifying questions** - Better to confirm than give wrong answer
- **Stay in your lane** - ChatGPT for frontend, Claude for backend
- **Update knowledge** - Docs change, keep context current

---

**Happy Building! 🛠️**

For questions or suggestions about these docs, contact Josh (lead developer).
