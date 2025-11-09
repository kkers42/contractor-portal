# Contractor Portal - Feature Roadmap

**Repository:** [kkers42/contractor-portal](https://github.com/kkers42/contractor-portal)
**Last Updated:** November 1, 2025
**Status:** Planning Phase for Major Feature Additions

---

## Overview

This document outlines the expanded feature set for the Contractor Portal, organized by implementation phases and complexity. Features range from weather integration to AI-powered scheduling and third-party API integrations.

---

## Feature Categories

### 🌤️ Weather Integration
### 📁 Document Management
### 🤖 AI/ML Scheduling & Optimization
### 🚨 Smart Alerts & Notifications
### 📍 GPS & Location Tracking
### 💬 AI Chatbot Assistant
### 🔌 Third-Party Integrations (QuickBooks, Jobber, etc.)
### 🔗 MCP (Model Context Protocol) Integration

---

## Phase 1: Weather Integration (2-3 weeks)

### Feature 1.1: Weather API Integration
**Priority:** High
**Complexity:** Medium
**Dependencies:** None

#### Implementation Details:
- **API Options:**
  - OpenWeatherMap (Free tier: 1000 calls/day)
  - WeatherAPI.com (Free tier: 1M calls/month)
  - NOAA/NWS (Free, US only, no key required)
  - Tomorrow.io (Free tier available)

#### Features:
- [ ] **Current weather for properties**
  - Temperature, precipitation, wind speed
  - Display on property detail pages
  - Cache weather data (15-minute refresh)

- [ ] **Weather-based service recommendations**
  - Snow removal alerts (when snowfall > 2 inches)
  - Lawn mowing delays (rain forecasts)
  - Salt/de-icing recommendations (freezing temps)

- [ ] **Automated weather reports**
  - Daily weather summary email to managers
  - Weekly forecast for all properties
  - Storm alerts (severe weather warnings)

- [ ] **Historical weather logging**
  - Record weather at time of service
  - Add weather data to operations logs
  - Include in service reports

#### Database Schema Changes:
```sql
-- Add weather column to operations logs
ALTER TABLE winter_ops_logs ADD COLUMN weather_conditions JSON;
ALTER TABLE green_services ADD COLUMN weather_conditions JSON;

-- Weather cache table
CREATE TABLE weather_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    weather_data JSON NOT NULL,
    forecast_data JSON,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (property_id) REFERENCES locations(id),
    INDEX idx_property_expiry (property_id, expires_at)
);

-- Weather alerts table
CREATE TABLE weather_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type ENUM('snow', 'storm', 'freeze', 'heat', 'wind') NOT NULL,
    severity ENUM('watch', 'warning', 'advisory') NOT NULL,
    location_ids JSON,  -- Array of affected property IDs
    alert_data JSON,
    starts_at DATETIME,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_active (expires_at, severity)
);
```

#### Backend Implementation:
```python
# New file: services/weather_service.py
from typing import Dict, List
import requests
from datetime import datetime, timedelta

class WeatherService:
    def __init__(self, api_key: str, provider: str = "openweathermap"):
        self.api_key = api_key
        self.provider = provider

    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """Fetch current weather for coordinates"""
        pass

    def get_forecast(self, lat: float, lon: float, days: int = 7) -> List[Dict]:
        """Get weather forecast"""
        pass

    def check_service_conditions(self, weather_data: Dict, service_type: str) -> Dict:
        """Determine if weather is suitable for service"""
        # Returns: {suitable: bool, reason: str, recommendation: str}
        pass

    def get_severe_alerts(self, lat: float, lon: float) -> List[Dict]:
        """Check for severe weather alerts"""
        pass

# New routes: routes/weather_routes.py
@router.get("/weather/property/{property_id}")
def get_property_weather(property_id: int):
    """Get current weather for a property"""
    pass

@router.get("/weather/alerts")
def get_active_alerts():
    """Get all active weather alerts"""
    pass

@router.post("/weather/notify")
def send_weather_notifications():
    """Trigger weather-based notifications"""
    pass
```

#### Frontend Integration:
- Weather widget on property cards
- Weather icon in operations logs
- Alert banner on dashboard for severe weather

#### Cost Estimate:
- Free tier sufficient for <100 properties
- Paid tier: $40-100/month for unlimited calls

---

## Phase 2: Document Management (2-4 weeks)

### Feature 2.1: Property Document Storage
**Priority:** High
**Complexity:** Medium
**Dependencies:** File storage solution

#### Implementation Details:
- **Storage Options:**
  - Local filesystem (simple, no cost)
  - AWS S3 (scalable, ~$0.023/GB/month)
  - Azure Blob Storage (similar pricing to S3)
  - Google Cloud Storage (similar pricing)
  - Self-hosted MinIO (S3-compatible, free)

#### Features:
- [ ] **Property map uploads**
  - Support: .png, .jpg, .jpeg, .pdf, .svg
  - Display on property detail page
  - Zoom/pan functionality for large maps
  - Multiple maps per property (zones, layouts, etc.)

- [ ] **Document library per property**
  - Word docs (.docx), Excel (.xlsx), text files
  - Property contracts, service agreements
  - Equipment specifications
  - Historical records

- [ ] **Document versioning**
  - Track document revisions
  - View previous versions
  - Restore older versions

- [ ] **Access control**
  - Admins: Full access
  - Managers: View and upload for assigned properties
  - Users: View only assigned properties

- [ ] **Document search**
  - Search by filename
  - Filter by file type
  - Filter by property
  - Tag-based organization

#### Database Schema:
```sql
CREATE TABLE property_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    document_type ENUM('map', 'contract', 'spreadsheet', 'manual', 'photo', 'other') NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size INT,  -- bytes
    mime_type VARCHAR(100),
    uploaded_by INT,  -- user_id
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    parent_document_id INT,  -- for versioning
    tags JSON,  -- ['winter-2024', 'zone-a', etc.]
    metadata JSON,  -- additional file info
    FOREIGN KEY (property_id) REFERENCES locations(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (parent_document_id) REFERENCES property_documents(id),
    INDEX idx_property (property_id),
    INDEX idx_type (document_type),
    INDEX idx_uploaded (uploaded_at)
);
```

#### Backend Implementation:
```python
# services/document_service.py
from fastapi import UploadFile
import aiofiles
from pathlib import Path

class DocumentService:
    UPLOAD_DIR = Path("data/property_documents")
    ALLOWED_EXTENSIONS = {
        'images': ['.png', '.jpg', '.jpeg', '.gif', '.svg'],
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.csv'],
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    async def upload_document(
        self,
        file: UploadFile,
        property_id: int,
        document_type: str,
        uploaded_by: int
    ) -> Dict:
        """Handle document upload"""
        # Validate file type and size
        # Generate secure filename
        # Save to disk or S3
        # Create database record
        pass

    def get_property_documents(self, property_id: int, document_type: str = None) -> List[Dict]:
        """Retrieve all documents for a property"""
        pass

    def delete_document(self, document_id: int, user_id: int) -> bool:
        """Delete document (with permission check)"""
        pass

# routes/document_routes.py
@router.post("/property/{property_id}/documents/upload")
async def upload_document(
    property_id: int,
    file: UploadFile,
    document_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Upload a document to a property"""
    pass

@router.get("/property/{property_id}/documents")
def get_documents(property_id: int):
    """Get all documents for a property"""
    pass

@router.get("/documents/{document_id}/download")
def download_document(document_id: int):
    """Download a document"""
    pass
```

#### Frontend Implementation:
- Drag-and-drop upload interface
- Document gallery with thumbnails
- Inline preview for images/PDFs
- Download button for other file types

#### Security Considerations:
- [ ] Validate file types (prevent executable uploads)
- [ ] Scan uploads for malware (ClamAV integration)
- [ ] Sanitize filenames (prevent path traversal)
- [ ] Check file size limits
- [ ] Authenticate all downloads

---

## Phase 3: AI/ML Scheduling & Optimization (4-8 weeks)

### Feature 3.1: ML-Powered Service Scheduling
**Priority:** Medium
**Complexity:** High
**Dependencies:** Historical data, Python ML libraries

#### Implementation Details:
- **ML Libraries:**
  - scikit-learn (traditional ML)
  - TensorFlow/PyTorch (deep learning - overkill for this)
  - Prophet (time series forecasting by Facebook)
  - XGBoost (gradient boosting)

#### Features:
- [ ] **Predictive service scheduling**
  - Analyze historical service patterns
  - Predict when properties will need service
  - Factor in weather forecasts
  - Consider seasonal variations

- [ ] **Contractor assignment optimization**
  - Route optimization (traveling salesman problem)
  - Skill matching (contractor capabilities vs job requirements)
  - Workload balancing across contractors
  - Minimize travel time between properties

- [ ] **Resource allocation**
  - Salt/material usage predictions
  - Equipment scheduling
  - Labor hour forecasting

- [ ] **Demand forecasting**
  - Predict busy periods based on historical data
  - Weather-based surge predictions
  - Seasonal adjustment

#### Algorithm Approach:
```python
# services/ml_scheduler.py
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd

class MLScheduler:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()

    def train_model(self, historical_data: pd.DataFrame):
        """
        Train ML model on historical service data

        Features:
        - Property location (lat/lon)
        - Property size
        - Service type
        - Weather conditions (temp, precip, wind)
        - Day of week, month, season
        - Days since last service
        - Historical service frequency

        Target:
        - Service needed (binary)
        - Days until next service (regression)
        """
        pass

    def predict_service_needs(self, date_range: tuple) -> List[Dict]:
        """
        Predict which properties need service in date range
        Returns: [{property_id, predicted_date, confidence, service_type}]
        """
        pass

    def optimize_routes(self, services: List[Dict], contractors: List[Dict]) -> Dict:
        """
        Optimize contractor routes for a day
        Uses nearest neighbor + genetic algorithm for TSP
        Returns: {contractor_id: [ordered list of property_ids], total_distance, estimated_time}
        """
        pass

    def assign_contractors(self, pending_services: List[Dict]) -> List[Dict]:
        """
        Assign contractors to services based on:
        - Location proximity
        - Skill match
        - Current workload
        - Historical performance
        """
        pass

# Background job (runs nightly)
@scheduler.scheduled_job('cron', hour=2)  # 2 AM daily
def generate_service_predictions():
    """Generate next 14 days of service predictions"""
    ml_scheduler = MLScheduler()
    predictions = ml_scheduler.predict_service_needs(days=14)
    # Store in database for review by managers
    pass
```

#### Database Schema:
```sql
CREATE TABLE ml_service_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    predicted_service_date DATE NOT NULL,
    service_type ENUM('snow', 'lawn', 'other') NOT NULL,
    confidence_score DECIMAL(5,4),  -- 0.0000 to 1.0000
    factors JSON,  -- What influenced the prediction
    weather_forecast JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'scheduled', 'completed', 'cancelled', 'incorrect') DEFAULT 'pending',
    FOREIGN KEY (property_id) REFERENCES locations(id),
    INDEX idx_date_confidence (predicted_service_date, confidence_score),
    INDEX idx_property (property_id)
);

CREATE TABLE contractor_routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id INT NOT NULL,
    route_date DATE NOT NULL,
    route_order JSON,  -- [{property_id, estimated_arrival, service_duration}]
    total_distance_km DECIMAL(10,2),
    estimated_duration_minutes INT,
    optimization_score DECIMAL(5,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contractor_id) REFERENCES users(id),
    INDEX idx_contractor_date (contractor_id, route_date)
);
```

#### Training Data Collection:
- Start collecting data now for future ML training
- Minimum 6 months of data recommended
- Need: service dates, weather, property info, outcomes

#### Cost/Resources:
- Computation: Run on server (CPU fine, no GPU needed)
- Training time: 5-30 minutes depending on data size
- Prediction time: < 1 second per property

---

## Phase 4: Smart Alerts & Notifications (2-3 weeks)

### Feature 4.1: Intelligent Alert System
**Priority:** High
**Complexity:** Medium
**Dependencies:** Weather integration, ML predictions (optional)

#### Features:
- [ ] **Service deadline alerts**
  - Alert managers when property needs service by deadline
  - Escalating alerts (24hr, 12hr, 2hr before deadline)
  - Highlight properties without assigned contractor

- [ ] **Unassigned service alerts**
  - Notify when service request has no contractor assigned
  - Auto-assign based on availability and location (with ML)
  - Send SMS to nearby available contractors

- [ ] **Weather-triggered alerts**
  - Snow alert: "6 inches predicted, 15 properties need plowing"
  - Freeze alert: "Temperatures dropping, pre-salt recommended"
  - Storm alert: "Severe weather incoming, review schedules"

- [ ] **Contractor location alerts**
  - Notify manager when contractor arrives at property
  - Alert if contractor is running late
  - Geofence-based check-in

- [ ] **Multi-channel notifications**
  - Email (non-urgent)
  - SMS (urgent)
  - Push notifications (mobile app - future)
  - In-app notifications (bell icon)

#### Database Schema:
```sql
CREATE TABLE alert_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    rule_type ENUM('deadline', 'weather', 'unassigned', 'location', 'custom') NOT NULL,
    conditions JSON,  -- Rule logic
    notification_channels JSON,  -- ['email', 'sms', 'push']
    recipients JSON,  -- User roles or specific user IDs
    enabled BOOLEAN DEFAULT TRUE,
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type_enabled (rule_type, enabled)
);

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    alert_rule_id INT,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type ENUM('info', 'warning', 'error', 'success') DEFAULT 'info',
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    channels_sent JSON,  -- ['email', 'sms']
    read_at DATETIME,
    actioned_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (alert_rule_id) REFERENCES alert_rules(id),
    INDEX idx_user_read (user_id, read_at),
    INDEX idx_created (created_at)
);
```

#### Backend Implementation:
```python
# services/alert_service.py
from typing import List, Dict
from datetime import datetime, timedelta

class AlertService:
    def __init__(self, email_service, sms_service):
        self.email = email_service
        self.sms = sms_service

    def check_deadline_alerts(self):
        """Check for services approaching deadlines"""
        # Query services with deadlines in next 24 hours
        # Check if contractor assigned
        # Send alerts if not
        pass

    def check_unassigned_services(self):
        """Find services without contractors"""
        # Query services older than 30 minutes with no contractor
        # Alert managers
        # Optionally suggest contractors
        pass

    def process_weather_alerts(self, weather_alerts: List[Dict]):
        """Process weather alerts and notify relevant users"""
        # Determine affected properties
        # Identify contractors who should be alerted
        # Send notifications
        pass

    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        channels: List[str],
        priority: str = 'medium'
    ):
        """Send notification via specified channels"""
        pass

# Background jobs
@scheduler.scheduled_job('interval', minutes=15)
def check_alerts():
    """Run alert checks every 15 minutes"""
    alert_service = AlertService(email, sms)
    alert_service.check_deadline_alerts()
    alert_service.check_unassigned_services()
```

#### SMS Integration:
- **Providers:**
  - Twilio (Most popular, $0.0079/SMS)
  - AWS SNS ($0.00645/SMS)
  - MessageBird (International, similar pricing)
- **Implementation:** Simple REST API calls

---

## Phase 5: GPS & Location Tracking (3-4 weeks)

### Feature 5.1: Real-Time Contractor Tracking
**Priority:** Medium
**Complexity:** High
**Dependencies:** Mobile app or web geolocation

#### Implementation Options:
1. **Web-based (Simple):**
   - Use browser geolocation API
   - Contractors share location from their phone browser
   - Updates every 1-5 minutes

2. **Mobile app (Advanced):**
   - Native iOS/Android app
   - Background location tracking
   - More accurate, better battery optimization

#### Features:
- [ ] **Real-time contractor location**
  - See all contractors on a map
  - Filter by status (working, traveling, available)
  - Click contractor to see details and route

- [ ] **Geofenced check-in/out**
  - Auto check-in when entering property geofence
  - Auto check-out when leaving
  - Track time on-site automatically

- [ ] **Route tracking**
  - Record contractor's path throughout day
  - Calculate actual travel time between properties
  - Compare to optimal route

- [ ] **Location history**
  - Replay contractor's day
  - Verify service completion
  - Calculate mileage for reimbursement

- [ ] **Privacy controls**
  - Only track during work hours
  - Contractor can pause tracking (with notification to manager)
  - Data retention limits (30-90 days)

#### Database Schema:
```sql
CREATE TABLE contractor_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id INT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy_meters INT,
    speed_kmh DECIMAL(5,2),
    heading DECIMAL(5,2),  -- 0-360 degrees
    altitude_meters INT,
    recorded_at DATETIME NOT NULL,
    status ENUM('working', 'traveling', 'available', 'unavailable') DEFAULT 'available',
    battery_level INT,  -- percent
    FOREIGN KEY (contractor_id) REFERENCES users(id),
    INDEX idx_contractor_time (contractor_id, recorded_at),
    INDEX idx_recorded (recorded_at)
) ENGINE=InnoDB;

-- Optimize for time-series data
-- Consider partitioning by month after 1 year

CREATE TABLE geofences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    center_lat DECIMAL(10, 8) NOT NULL,
    center_lon DECIMAL(11, 8) NOT NULL,
    radius_meters INT DEFAULT 100,
    FOREIGN KEY (property_id) REFERENCES locations(id),
    INDEX idx_property (property_id)
);
```

#### Backend Implementation:
```python
# services/location_service.py
from typing import Tuple, List
from datetime import datetime
import math

class LocationService:
    def update_contractor_location(
        self,
        contractor_id: int,
        lat: float,
        lon: float,
        accuracy: int = None,
        status: str = 'available'
    ):
        """Record contractor location update"""
        # Save to database
        # Check if within any geofences
        # Trigger events if entering/exiting property
        pass

    def get_contractor_locations(self, contractor_ids: List[int] = None) -> List[Dict]:
        """Get latest location for contractors"""
        # Return most recent location for each contractor
        pass

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two GPS points (Haversine formula)"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        # Haversine formula implementation
        pass

    def check_geofence(self, lat: float, lon: float, property_id: int) -> bool:
        """Check if location is within property geofence"""
        pass

    def get_location_history(
        self,
        contractor_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """Get contractor's location history for a time range"""
        pass

# WebSocket endpoint for real-time updates
from fastapi import WebSocket

@router.websocket("/ws/locations")
async def location_websocket(websocket: WebSocket):
    """Stream real-time location updates"""
    await websocket.accept()
    # Stream location updates as they come in
    # Client can filter by contractor_id
    pass

# REST endpoints
@router.post("/contractors/{contractor_id}/location")
def update_location(contractor_id: int, lat: float, lon: float):
    """Contractor updates their location"""
    pass

@router.get("/contractors/locations")
def get_all_locations():
    """Get current locations of all contractors"""
    pass
```

#### Frontend Implementation:
- Google Maps or Mapbox integration
- Real-time updates via WebSocket
- Contractor pins on map with status colors
- Property boundaries shown as circles/polygons

#### Privacy & Legal:
- [ ] Contractor consent required (terms of service)
- [ ] Clear tracking hours (only during shifts)
- [ ] Data retention policy (auto-delete after 90 days)
- [ ] Comply with local laws (GDPR, CCPA)

---

## Phase 6: AI Chatbot Assistant (3-5 weeks)

### Feature 6.1: Contractor Support Chatbot
**Priority:** Low
**Complexity:** High
**Dependencies:** None (self-hosted LLM)

#### Implementation Options:

1. **Open Source LLMs (Self-Hosted):**
   - **Ollama** (Recommended)
     - Easy to deploy
     - Runs locally
     - Models: Llama 3, Mistral, Codellama
     - Free, no API costs
   - **LM Studio**
   - **GPT4All**
   - **LocalAI**

2. **Cloud LLMs (API-based):**
   - OpenAI GPT-4 ($0.03/1K tokens)
   - Anthropic Claude ($0.02/1K tokens)
   - Cheaper but recurring costs

#### Features:
- [ ] **FAQ answering**
  - "How do I log a service?"
  - "What properties am I assigned to today?"
  - "How do I upload photos?"

- [ ] **Natural language queries**
  - "Show me my schedule for tomorrow"
  - "What's the weather for property X?"
  - "How much salt did I use last week?"

- [ ] **Guided workflows**
  - Walk contractors through creating ops logs
  - Help troubleshoot common issues
  - Explain application features

- [ ] **Contextual assistance**
  - Understands user role (Admin, Manager, User)
  - Knows user's current page
  - Can access user's data for personalized responses

#### Ollama Integration:
```python
# services/chatbot_service.py
import requests
from typing import List, Dict

class ChatbotService:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3"  # or mistral, codellama
        self.system_prompt = """
        You are a helpful assistant for the Contractor Portal.
        You help contractors and managers with:
        - Logging services
        - Checking schedules
        - Understanding reports
        - Navigating the application

        Be concise, friendly, and professional.
        If you don't know something, admit it and suggest asking a manager.
        """

    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Send message to chatbot and get response"""
        messages = [{"role": "system", "content": self.system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        response = requests.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False
            }
        )

        return response.json()["message"]["content"]

    def chat_with_context(
        self,
        user_message: str,
        user_role: str,
        user_data: Dict,
        page_context: str = None
    ) -> str:
        """Chat with user-specific context"""
        # Augment system prompt with user context
        context_prompt = f"""
        User role: {user_role}
        Current page: {page_context}
        User has access to: {user_data.get('assigned_properties', 'N/A')}
        """

        # Add context to message
        enhanced_message = f"{context_prompt}\n\nUser question: {user_message}"
        return self.chat(enhanced_message)

# routes/chatbot_routes.py
@router.post("/chatbot/message")
def send_message(
    message: str,
    conversation_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Send message to chatbot"""
    chatbot = ChatbotService()

    # Load conversation history if exists
    history = get_conversation_history(conversation_id) if conversation_id else None

    # Get response with user context
    response = chatbot.chat_with_context(
        message,
        user_role=current_user['role'],
        user_data=current_user,
        page_context=request.headers.get('Referer')
    )

    # Save conversation
    save_conversation_message(conversation_id, message, response)

    return {"response": response}
```

#### Database Schema:
```sql
CREATE TABLE chatbot_conversations (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    user_id INT NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_message_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_time (user_id, last_message_at)
);

CREATE TABLE chatbot_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES chatbot_conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id, created_at)
);
```

#### Frontend Implementation:
- Floating chat button (bottom right corner)
- Popup chat window
- Typing indicators
- Conversation history

#### Ollama Setup:
```bash
# Install Ollama on server
curl -fsSL https://ollama.com/install.sh | sh

# Pull model (one-time)
ollama pull llama3

# Run Ollama service
ollama serve  # Runs on port 11434

# Test
curl http://localhost:11434/api/chat -d '{
  "model": "llama3",
  "messages": [{"role": "user", "content": "Hello!"}]
}'
```

#### Cost:
- **Free** with Ollama (self-hosted)
- Requires: ~8GB RAM, ~4GB disk per model
- CPU sufficient (GPU optional for faster responses)

---

## Phase 7: Third-Party API Integrations (4-6 weeks)

### Feature 7.1: QuickBooks Integration
**Priority:** High
**Complexity:** High
**Dependencies:** QuickBooks Developer Account

#### Features:
- [ ] **Invoice generation from operations logs**
  - Convert completed services to invoices
  - One-click "Create Invoice" button
  - Map services to QuickBooks items

- [ ] **Customer sync**
  - Sync properties with QuickBooks customers
  - Two-way sync (QB → Portal, Portal → QB)
  - Avoid duplicates

- [ ] **Payment tracking**
  - Sync invoice payment status
  - Show paid/unpaid in portal
  - Payment reminders

- [ ] **Expense tracking**
  - Import QuickBooks expenses
  - Match to operations (salt purchases, equipment)

#### QuickBooks API:
```python
# services/quickbooks_service.py
from intuitlib.client import AuthClient
from quickbooks import QuickBooks

class QuickBooksIntegration:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.auth_client = AuthClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri='http://yourapp.com/callback',
            environment='production'
        )
        self.qb_client = None

    def authenticate(self):
        """Authenticate with QuickBooks"""
        # OAuth 2.0 flow
        pass

    def create_invoice(self, operations_log: Dict) -> str:
        """Create invoice in QuickBooks from operations log"""
        from quickbooks.objects.invoice import Invoice
        from quickbooks.objects.detailline import SalesItemLine

        invoice = Invoice()
        invoice.CustomerRef = self.get_customer_ref(operations_log['property_id'])

        line = SalesItemLine()
        line.Amount = operations_log['calculated_cost']
        line.Description = f"Snow removal service - {operations_log['date']}"
        invoice.Line.append(line)

        invoice.save(qb=self.qb_client)
        return invoice.Id

    def sync_customers(self):
        """Sync customers between QB and Portal"""
        pass

    def get_invoice_status(self, invoice_id: str) -> str:
        """Check payment status of invoice"""
        pass

# routes/integrations/quickbooks_routes.py
@router.get("/integrations/quickbooks/connect")
def connect_quickbooks():
    """Initiate QuickBooks OAuth"""
    pass

@router.post("/operations/{log_id}/create-invoice")
def create_invoice_from_log(log_id: int):
    """Create QuickBooks invoice from operations log"""
    pass
```

#### Database Schema:
```sql
CREATE TABLE integration_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    integration_name VARCHAR(50) NOT NULL,
    credentials JSON NOT NULL,  -- Encrypted tokens
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE quickbooks_sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sync_type ENUM('customer', 'invoice', 'payment', 'expense') NOT NULL,
    portal_id INT,  -- ID in our system
    quickbooks_id VARCHAR(255),  -- ID in QuickBooks
    sync_direction ENUM('to_qb', 'from_qb') NOT NULL,
    status ENUM('success', 'failed', 'pending') NOT NULL,
    error_message TEXT,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_portal (portal_id, sync_type),
    INDEX idx_qb (quickbooks_id)
);
```

### Feature 7.2: Jobber Integration
**Priority:** Medium
**Complexity:** Medium
**Dependencies:** Jobber API access

#### Features:
- [ ] **Job sync**
  - Import jobs from Jobber
  - Create jobs in Jobber from portal
  - Sync job status

- [ ] **Schedule sync**
  - Import Jobber schedules
  - Two-way calendar sync

- [ ] **Client sync**
  - Sync client lists

#### Jobber API:
Similar structure to QuickBooks integration

### Feature 7.3: Other Potential Integrations
- **Stripe/PaymentIntent** - Online payment processing
- **ServiceTitan** - Field service management
- **Google Calendar** - Schedule sync
- **Slack** - Team notifications
- **Zapier** - Connect to 5000+ apps without custom code

---

## Phase 8: MCP (Model Context Protocol) Integration (2-4 weeks)

### Feature 8.1: MCP Server Implementation
**Priority:** Low
**Complexity:** Medium
**Dependencies:** Understanding of MCP protocol

#### What is MCP?
Model Context Protocol is Anthropic's open protocol for connecting AI systems to data sources. It allows AI assistants (like Claude) to securely access your application data.

#### Use Cases:
- [ ] **Claude Desktop integration**
  - Managers can ask Claude about their properties
  - "Show me all snow removal logs for January"
  - "Which properties haven't been serviced this week?"

- [ ] **AI-powered reporting**
  - Natural language report generation
  - "Create a summary of all winter operations"

- [ ] **Data analysis**
  - Ask questions about trends
  - Get insights from historical data

#### Implementation:
```python
# mcp_server.py
from mcp.server import MCPServer
from mcp.types import Tool, Resource

class ContractorPortalMCP(MCPServer):
    def __init__(self):
        super().__init__(name="contractor-portal")

        # Define available tools
        self.register_tool(
            Tool(
                name="get_properties",
                description="Get list of all properties",
                parameters={}
            )
        )

        self.register_tool(
            Tool(
                name="get_operations_logs",
                description="Get operations logs with filters",
                parameters={
                    "start_date": "string",
                    "end_date": "string",
                    "property_id": "integer"
                }
            )
        )

        self.register_tool(
            Tool(
                name="generate_report",
                description="Generate a report by type",
                parameters={
                    "report_type": "string",  # product, property, user
                    "filters": "object"
                }
            )
        )

    async def handle_tool_call(self, tool_name: str, parameters: dict):
        """Execute tool and return results"""
        if tool_name == "get_properties":
            return await self.get_properties()
        elif tool_name == "get_operations_logs":
            return await self.get_operations_logs(**parameters)
        # ... etc

    async def get_properties(self):
        """Fetch properties from database"""
        from db import fetch_query
        return fetch_query("SELECT * FROM locations")

    async def get_operations_logs(self, start_date=None, end_date=None, property_id=None):
        """Fetch operations logs with filters"""
        # Build query based on filters
        pass

# Start MCP server
if __name__ == "__main__":
    server = ContractorPortalMCP()
    server.run(port=5000)
```

#### Configuration:
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_USER": "contractor",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

#### Security:
- [ ] Authentication required for MCP access
- [ ] Rate limiting
- [ ] Audit logging of AI queries
- [ ] Row-level security (users only see their data)

---

## Implementation Priority Summary

### Pre-Launch (Before Monday)
**Nothing from this roadmap** - Focus on security hardening from LAUNCH_CHECKLIST.md

### Post-Launch Phase 1 (Weeks 1-4)
1. **Weather Integration** - High value, medium complexity
2. **Document Management** - High value, medium complexity
3. **Smart Alerts** - High value, medium complexity

### Post-Launch Phase 2 (Weeks 5-12)
4. **GPS Tracking** - Medium value, high complexity
5. **AI/ML Scheduling** - Medium value, high complexity (needs data)
6. **QuickBooks Integration** - High value, high complexity

### Post-Launch Phase 3 (Weeks 13-20)
7. **Chatbot** - Low value, high complexity
8. **Other Integrations** (Jobber, Stripe, etc.)
9. **MCP Integration** - Low value, medium complexity

---

## Cost Estimates

### Monthly Recurring Costs:
- Weather API: $0-100/month (depending on scale)
- File Storage (S3): ~$5-20/month for 100GB
- SMS (Twilio): ~$100/month for 1000 messages
- QuickBooks API: Free (included with QB subscription)
- AI Chatbot (Ollama): $0 (self-hosted)
- GPS Tracking: $0 (web-based) or $500+ (mobile app development)

**Total: ~$105-220/month for all features**

### One-Time Development Costs:
- Weather: 40-60 hours
- Documents: 40-80 hours
- ML Scheduling: 80-160 hours
- Alerts: 40-60 hours
- GPS: 60-80 hours (web) or 200-400 hours (mobile app)
- Chatbot: 60-100 hours
- QuickBooks: 80-120 hours
- MCP: 40-80 hours

**Total: 440-1140 developer hours**

---

## Technology Stack Requirements

### New Python Libraries:
```txt
# requirements.txt additions

# Weather
requests>=2.31.0
python-cachetools>=5.3.0

# ML/AI
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
prophet>=1.1.0  # For time series forecasting

# File handling
aiofiles>=23.1.0
python-magic>=0.4.27  # File type detection
pillow>=10.0.0  # Image processing

# SMS
twilio>=8.5.0

# QuickBooks
python-quickbooks>=0.9.0
intuitlib>=1.3.0

# Background jobs
apscheduler>=3.10.0

# WebSockets (GPS tracking)
websockets>=11.0.0

# Chatbot (if using Ollama)
# No additional library needed - just HTTP requests
```

### Infrastructure Requirements:
- **Server RAM:** Increase from 4GB to 8GB (for ML and chatbot)
- **Storage:** Add 50-100GB for documents and ML models
- **CPU:** Current should be sufficient
- **Ollama:** Dedicated server or separate container (8GB RAM minimum)

---

## Questions to Consider

Before starting implementation:

1. **Weather:**
   - Which weather provider? (OpenWeatherMap vs WeatherAPI)
   - How often should we update weather? (15 min? 1 hour?)
   - Historical weather needed? (costs extra)

2. **Documents:**
   - Local storage or cloud (S3)? Local is free but harder to scale
   - Maximum file size? (Recommend 50MB)
   - Who can delete documents? (Admins only? Original uploader?)

3. **AI/ML:**
   - When to start? (Need 6+ months of historical data)
   - Manual review required before auto-scheduling?
   - What confidence threshold for predictions? (70%? 80%?)

4. **GPS:**
   - Web-based or mobile app? (Web is simpler, app is better)
   - Track 24/7 or only during work hours?
   - How long to retain location data? (30 days? 90 days?)

5. **Chatbot:**
   - Ollama self-hosted or pay for OpenAI API?
   - Which model? (Llama3 is good balance of speed/quality)
   - Should it have access to user data? (Requires security considerations)

6. **Integrations:**
   - QuickBooks Online or Desktop? (API only works with Online)
   - Who manages integration credentials? (Admins only)
   - Real-time sync or batch (nightly)?

---

## Next Steps

1. **Review and prioritize** these features with stakeholders
2. **Test current functionality** (from your request)
3. **Complete pre-launch security tasks** (LAUNCH_CHECKLIST.md)
4. **Launch on Monday**
5. **Start Phase 1 features** (Weather, Documents, Alerts)

Would you like me to start implementing any of these features now, or should we focus on testing and launch prep?
