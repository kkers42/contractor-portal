# System Architecture Overview

**Last Updated**: 2025-12-23

## System Overview

The Contractor Portal is a full-stack web application for managing snow removal operations, built with:
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/JavaScript (vanilla JS, no framework)
- **Database**: MySQL
- **Server**: Ubuntu Linux (72.61.0.186)
- **Web Server**: Nginx (reverse proxy) → Uvicorn (ASGI server)
- **Process Manager**: systemd

---

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.x
- **ASGI Server**: Uvicorn
- **Authentication**: JWT tokens (30-day expiry)
- **Password Hashing**: bcrypt
- **Database Driver**: mysql-connector-python

### Frontend
- **Language**: Vanilla JavaScript (ES6+)
- **Styling**: CSS (green terminal theme)
- **No framework** - pure HTML/CSS/JS for simplicity

### Database
- **RDBMS**: MySQL 8.x
- **Database Name**: `contractor_portal`
- **User**: `contractor`
- **Host**: localhost (same server)

### Infrastructure
- **Server OS**: Ubuntu Linux
- **IP**: 72.61.0.186
- **Domain**: snow-contractor.com
- **SSL**: Let's Encrypt (via Nginx)
- **Service**: systemd unit `contractor-portal.service`

---

## Directory Structure

```
/opt/contractor-portal/          # Production server
├── venv/                         # Python virtual environment
├── app/                          # Application code
│   ├── main.py                   # FastAPI app entry point
│   ├── auth.py                   # Authentication logic
│   ├── db.py                     # Database connection
│   ├── routes/                   # API route handlers
│   │   ├── auth_routes.py
│   │   ├── property_routes.py
│   │   ├── ops_routes.py
│   │   ├── sms_routes.py
│   │   ├── ai_routes.py
│   │   ├── winter_event_routes.py
│   │   ├── assignment_routes.py
│   │   └── ... (more routes)
│   ├── services/                 # Background services
│   │   └── monitoring_agent.py   # Claude-powered monitoring
│   └── static/                   # Frontend files
│       ├── login.html
│       ├── AdminDashboard.html
│       ├── ManagerDashboard.html
│       ├── UserDashboard.html
│       ├── UserProfile.html
│       └── ... (50+ HTML pages)
└── .env                          # Environment variables

r:\Contractor App\               # Development (local)
├── app/                         # Same structure as server
├── docs/                        # Documentation
├── workflows/                   # This folder - workflow docs
└── monitoring-agent.service     # Systemd service file
```

---

## Network Architecture

```
Internet
    ↓
[Cloudflare DNS] → snow-contractor.com
    ↓
[Nginx :443] (SSL termination)
    ↓
[Nginx Reverse Proxy]
    ↓
[Uvicorn :8000] (FastAPI app)
    ↓
[MySQL :3306] (Database)
```

### Port Mapping
- **443** (HTTPS) → Public-facing (Nginx)
- **80** (HTTP) → Redirects to 443
- **8000** → Internal only (Uvicorn listens on 127.0.0.1:8000)
- **3306** → Internal only (MySQL)

---

## Data Flow

### User Request Flow
```
User Browser
    ↓ (HTTPS)
Nginx (SSL termination)
    ↓ (HTTP)
Uvicorn/FastAPI
    ↓
Route Handler (routes/*.py)
    ↓
Database Query (db.py)
    ↓
MySQL Database
    ↓
Response (JSON or HTML)
    ↓
User Browser
```

### Authentication Flow
```
1. User enters email/password at /static/login.html
2. POST to /api/login/ with credentials
3. auth_routes.py validates against users table
4. If valid: create JWT token (30-day expiry)
5. Return token to frontend
6. Frontend stores token in localStorage
7. All subsequent requests include: Authorization: Bearer <token>
8. Backend validates token via get_current_user() dependency
```

---

## Core Components

### 1. FastAPI Application (main.py)
- Entry point for the entire backend
- Registers all route modules
- Configures CORS
- Runs on Uvicorn ASGI server

### 2. Authentication System (auth.py)
- JWT token creation and validation
- Password hashing with bcrypt
- OAuth2 password bearer scheme
- `get_current_user()` dependency for protected routes

### 3. Database Layer (db.py)
- MySQL connection pooling
- `execute_query()` - for INSERT/UPDATE/DELETE
- `fetch_query()` - for SELECT queries
- Automatic reconnection on connection loss

### 4. Route Modules (routes/*.py)
Each route file handles a specific domain:
- **auth_routes.py**: User management, login, profile
- **property_routes.py**: Properties, addresses, locations
- **ops_routes.py**: Winter ops logs (tickets)
- **sms_routes.py**: SMS messaging with Twilio + ChatGPT
- **ai_routes.py**: AI suggestions (ChatGPT)
- **winter_event_routes.py**: Snow storm events
- **assignment_routes.py**: Property assignments
- **report_routes.py**: Excel report generation

### 5. Frontend (static/*.html)
- Static HTML pages served by Nginx
- JavaScript handles API calls
- No build process - direct deployment
- Shared config.js for API base URL

---

## Key External Integrations

### 1. OpenAI (ChatGPT)
- **API Key**: Stored in environment variable `OPENAI_API_KEY`
- **Used For**:
  - SMS message interpretation (sms_routes.py)
  - AI chatbot suggestions (ai_routes.py)
- **Model**: gpt-4o-mini

### 2. Anthropic (Claude)
- **API Key**: `ANTHROPIC_API_KEY` (for monitoring agent)
- **Used For**:
  - Monitoring and diagnostics (monitoring_agent.py)
  - Self-healing automation
  - Bug report generation

### 3. Twilio (SMS)
- **Credentials**:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_PHONE_NUMBER`
- **Used For**:
  - Sending SMS to contractors
  - Receiving SMS via webhook
- **Webhook**: POST to /sms/webhook

### 4. Weather API
- **API Key**: Configured in APISettings.html
- **Used For**:
  - Weather forecasts per property
  - Zero tolerance account alerts

### 5. N8N (Workflow Automation)
- **Webhook URL**: Configured in monitoring agent
- **Used For**:
  - Receiving monitoring alerts
  - Creating GitHub issues
  - Sending Discord/Email notifications
  - Logging to Google Sheets

### 6. Google OAuth
- **Used For**: User login (optional)
- **Credentials**: Google Cloud Console
- **Flow**: OAuth 2.0 authorization code flow

---

## Environment Variables

Located in `/opt/contractor-portal/.env`:

```bash
# Database
DB_HOST=localhost
DB_USER=contractor
DB_PASSWORD=Bimmer325i
DB_NAME=contractor_portal

# JWT
JWT_SECRET_KEY=<secret>
JWT_EXPIRE_MINUTES=43200  # 30 days

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic (for monitoring)
ANTHROPIC_API_KEY=sk-ant-...

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# N8N
N8N_WEBHOOK_URL=https://...

# Weather API
WEATHER_API_KEY=...

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://snow-contractor.com/auth/google/callback
```

---

## Systemd Services

### contractor-portal.service
```ini
[Unit]
Description=Contractor Portal (Uvicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/contractor-portal/app
ExecStart=/opt/contractor-portal/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Management**:
```bash
systemctl start contractor-portal
systemctl stop contractor-portal
systemctl restart contractor-portal
systemctl status contractor-portal
journalctl -u contractor-portal -f  # View logs
```

### monitoring-agent.service
```ini
[Unit]
Description=Contractor Portal Monitoring Agent (Claude-Powered)
After=network.target contractor-portal.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/contractor-portal/app
Environment="ANTHROPIC_API_KEY=sk-ant-..."
Environment="N8N_WEBHOOK_URL=https://..."
ExecStart=/opt/contractor-portal/venv/bin/python3 /opt/contractor-portal/app/services/monitoring_agent.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

---

## Deployment Process

### Initial Setup
```bash
# 1. Clone/upload code to server
scp -r "r:\Contractor App\app" root@72.61.0.186:/opt/contractor-portal/

# 2. Create virtual environment
cd /opt/contractor-portal
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
nano .env  # Add all environment variables

# 5. Setup systemd service
cp contractor-portal.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable contractor-portal
systemctl start contractor-portal

# 6. Verify
systemctl status contractor-portal
curl http://localhost:8000
```

### Code Updates
```bash
# From local machine (r:\Contractor App)
scp app/routes/auth_routes.py root@72.61.0.186:/opt/contractor-portal/app/routes/auth_routes.py
scp app/static/UserProfile.html root@72.61.0.186:/opt/contractor-portal/app/static/UserProfile.html

# On server
systemctl restart contractor-portal
systemctl status contractor-portal
```

---

## Security

### Authentication
- JWT tokens with 30-day expiry
- bcrypt password hashing (salt rounds: 12)
- OAuth2 bearer token scheme

### HTTPS
- SSL certificates from Let's Encrypt
- Automatic renewal via certbot
- Nginx enforces HTTPS redirect

### Database
- MySQL user with limited permissions
- Password-protected (not root)
- Local access only (no remote connections)

### API Keys
- Stored in environment variables (not in code)
- Not committed to git
- Restricted to server-side only

---

## Monitoring & Logging

### Application Logs
```bash
# Real-time logs
journalctl -u contractor-portal -f

# Last 100 lines
journalctl -u contractor-portal -n 100

# Logs from today
journalctl -u contractor-portal --since today
```

### Nginx Logs
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Monitoring Agent
- Runs every 5 minutes
- Checks: web server, API, database, disk, memory
- Auto-repairs safe issues
- Reports to N8N for manual issues
- See: `docs/MONITORING_SETUP.md`

---

## Performance

### Database Connection Pooling
- Persistent connections
- Automatic reconnection
- Query optimization for large datasets

### Caching
- Browser cache control headers
- Static file caching via Nginx

### Scalability
- Single server setup (current)
- Can scale to load balancer + multiple app servers
- Database can be moved to separate server

---

## Backup Strategy

### Database Backups
```bash
# Manual backup
mysqldump -u contractor -p contractor_portal > backup_$(date +%Y%m%d).sql

# Restore
mysql -u contractor -p contractor_portal < backup_20251223.sql
```

### Code Backups
- Git repository (version control)
- Local development copy: `r:\Contractor App`
- Server production copy: `/opt/contractor-portal`

---

## Troubleshooting

### Service Won't Start
```bash
systemctl status contractor-portal
journalctl -u contractor-portal -n 50
# Check for import errors, port conflicts
```

### Database Connection Errors
```bash
mysql -u contractor -p contractor_portal
# Verify credentials in .env match database
```

### 502 Bad Gateway
```bash
# Uvicorn not running
systemctl restart contractor-portal

# Check Nginx config
nginx -t
systemctl restart nginx
```

### Logs Not Showing
```bash
# Uvicorn might be buffering
# Add --log-level debug to ExecStart in service file
```

---

## Related Documentation

- [MONITORING_SETUP.md](../docs/MONITORING_SETUP.md) - Monitoring agent setup
- [DISCORD_SETUP.md](../docs/DISCORD_SETUP.md) - Discord notifications
- [JOSH_TODO.md](../JOSH_TODO.md) - Current tasks and status
- [README.md](../README.md) - Project overview
