# Alert & Maintenance Service - Quick Start Guide

## 🚀 What This Service Does

The Alert & Maintenance microservice:
1. ✅ Receives sensor data from equipment
2. ✅ Calls ML Prediction service to get failure predictions
3. ✅ Creates alerts for HIGH/CRITICAL severity failures
4. ✅ Sends email notifications (via Celery)
5. ✅ Schedules maintenance tasks

---

## 📁 Project Structure

```
services/alert-maintenance/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # 🔥 FastAPI app with 4 core endpoints
│   ├── config.py             # Configuration from environment variables
│   ├── database.py           # Async SQLAlchemy database setup
│   ├── schemas.py            # Database models (AlertDB, MaintenanceTaskDB)
│   ├── models.py             # Pydantic request/response models
│   ├── services.py           # Business logic (AlertGenerationService)
│   ├── celery_app.py         # Celery configuration
│   └── tasks.py              # Background tasks (send_email_alert)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── run.sh                    # Linux/Mac startup script
├── run.bat                   # Windows startup script
├── ENDPOINTS_QUICK_TEST.md   # Testing guide
└── README_QUICKSTART.md      # This file
```

---

## ⚡ Quick Start (3 Steps)

### Step 1: Setup Environment

```bash
# Navigate to service directory
cd services/alert-maintenance

# Copy environment template
cp .env.example .env

# Edit .env with your settings
# REQUIRED: DATABASE_URL, REDIS_URL
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### Step 3: Run the Service

**Option A: Using startup script (recommended)**
```bash
./run.sh      # Linux/Mac
run.bat       # Windows
```

**Option B: Direct command**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

**Service is ready when you see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8003 (Press CTRL+C to quit)
INFO:     Started reloader process
```

---

## 🔗 The 4 Core Endpoints

### 1. 🟢 Health Check
```bash
curl http://localhost:8003/health
```

### 2. 🔴 Generate Alert (Main Endpoint)
```bash
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=RADAR-001&temperature=95.5&vibration=0.85&pressure=4.2"
```
**What it does:**
- Sends sensor data to ML service (port 8002)
- Gets failure prediction
- Creates alert if severity is HIGH or CRITICAL
- Queues email notification
- Returns alert details

### 3. 🟡 Get Active Alerts
```bash
curl "http://localhost:8003/api/v1/alerts/active"
curl "http://localhost:8003/api/v1/alerts/active?severity=CRITICAL"
```

### 4. 🔵 Schedule Maintenance
```bash
curl -X POST "http://localhost:8003/api/v1/maintenance/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-001",
    "task_type": "PREVENTIVE",
    "priority": "HIGH",
    "scheduled_date": "2025-11-10T10:00:00Z"
  }'
```

---

## 📚 Interactive Documentation

Once running, access auto-generated API docs:

- **Swagger UI:** http://localhost:8003/docs
- **ReDoc:** http://localhost:8003/redoc

These provide:
- ✅ Full API documentation
- ✅ Interactive testing interface
- ✅ Request/response schemas
- ✅ Try-it-out functionality

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://drdo:drdo123@localhost:5432/equipment_maintenance

# Redis (REQUIRED for Celery)
REDIS_URL=redis://localhost:6379/0

# ML Service URL (REQUIRED)
ML_PREDICTION_SERVICE_URL=http://localhost:8002
```

### Optional Environment Variables

```bash
# Service
SERVICE_NAME=alert-maintenance-service
SERVICE_VERSION=1.0.0
PORT=8003
DEBUG=False

# Email (for notifications)
EMAIL_ENABLED=True
EMAIL_FROM=alerts@drdo.gov.in
EMAIL_TO=maintenance@drdo.gov.in

# Alert Thresholds
ALERT_CRITICAL_THRESHOLD=0.8
ALERT_HIGH_THRESHOLD=0.6
ALERT_MEDIUM_THRESHOLD=0.4
```

---

## 🧪 Testing the Service

### Complete Test Flow

```bash
# 1. Health check
curl http://localhost:8003/health

# 2. Generate critical alert
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=RADAR-001&temperature=95.5&vibration=0.85&pressure=4.2"

# Save the alert ID from response

# 3. View all active alerts
curl "http://localhost:8003/api/v1/alerts/active"

# 4. Schedule maintenance for the alert
curl -X POST "http://localhost:8003/api/v1/maintenance/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-001",
    "task_type": "PREVENTIVE",
    "priority": "CRITICAL",
    "scheduled_date": "2025-11-09T08:00:00Z",
    "title": "Address CRITICAL alert",
    "alert_id": "YOUR_ALERT_ID_HERE"
  }'
```

See `ENDPOINTS_QUICK_TEST.md` for detailed testing examples.

---

## 🐛 Troubleshooting

### Service won't start

**Check port availability:**
```bash
# Windows
netstat -ano | findstr :8003

# Linux/Mac
lsof -i :8003
```

**Check database connection:**
```bash
psql -U drdo -d equipment_maintenance -h localhost -p 5432
```

**Check Redis connection:**
```bash
redis-cli ping
# Should return: PONG
```

### ML service connection error

**Verify ML service is running:**
```bash
curl http://localhost:8002/health
```

### Database error

**Check DATABASE_URL format:**
```bash
# Must be: postgresql+asyncpg://user:password@host:port/database
echo $DATABASE_URL
```

**Create database if needed:**
```bash
createdb -U drdo equipment_maintenance
```

---

## 📊 Architecture Flow

```
┌─────────────────┐
│ Sensor Data     │
│ (Query Params)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Alert & Maintenance Service     │
│ (Port 8003)                     │
│                                  │
│  ┌──────────────────────────┐  │
│  │ POST /alerts/generate    │  │───┐
│  └──────────────────────────┘  │   │
│           │                     │   │
│           ▼                     │   │
│  ┌──────────────────────────┐  │   │
│  │ AlertGenerationService   │  │   │
│  └──────────────────────────┘  │   │
│           │                     │   │
│           ├─── Call ML API      │   │
│           │                     │   │ HTTP POST
│           ├─── Create Alert     │   │
│           │                     │   │
│           └─── Queue Email      │   │
└─────────────────────────────────┘   │
                                      │
         ┌────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ ML Prediction Service           │
│ (Port 8002)                     │
│                                  │
│ Returns:                         │
│  - failure_probability          │
│  - severity (CRITICAL/HIGH)     │
│  - days_until_failure           │
│  - recommended_action           │
└─────────────────────────────────┘
```

---

## 🎯 Success Criteria

Service is working correctly if:

✅ Health check returns 200 OK  
✅ Generate alert creates alert for high sensor values  
✅ Generate alert returns 404 for normal sensor values  
✅ Get active alerts returns list  
✅ Schedule maintenance creates task  
✅ Email notification is queued (check Celery logs)

---

## 📦 Dependencies

**Core:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy[asyncio]` - Async ORM
- `asyncpg` - PostgreSQL async driver
- `pydantic` - Data validation
- `pydantic-settings` - Config management

**Background Tasks:**
- `celery` - Task queue
- `redis` - Message broker

**HTTP Client:**
- `httpx` - Async HTTP requests (to ML service)

**Database:**
- `alembic` - Database migrations (optional)

---

## 🔐 Security Notes

- ❌ NEVER commit `.env` files
- ✅ Use strong database passwords
- ✅ Configure CORS for production
- ✅ Use HTTPS in production
- ✅ Implement authentication (not included in MVP)

---

## 📞 Support

For detailed testing: See `ENDPOINTS_QUICK_TEST.md`  
For Celery setup: See `CELERY_USAGE.md`  
For API docs: http://localhost:8003/docs

---

**Service:** Alert & Maintenance  
**Version:** 1.0.0  
**Port:** 8003  
**Status:** MVP Ready ✅
