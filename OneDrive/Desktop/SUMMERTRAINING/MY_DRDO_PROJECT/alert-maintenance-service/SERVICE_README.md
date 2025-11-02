# Alert & Maintenance Service

**Port**: 8003  
**Domain**: Alert Generation & Maintenance Scheduling  
**Technology Stack**: FastAPI, PostgreSQL, Redis, Celery, SQLAlchemy

---

## 📋 Overview

The Alert & Maintenance Service manages the action layer of the DRDO Equipment Maintenance Prediction System. It consumes ML predictions, generates alerts, sends notifications, and schedules maintenance tasks.

### Key Responsibilities

- ✅ Subscribe to prediction events from ML service
- ✅ Generate alerts for HIGH and CRITICAL severities
- ✅ Send email/SMS notifications (via Celery tasks)
- ✅ Schedule and track maintenance tasks
- ✅ Provide alert acknowledgment and resolution workflows
- ✅ Generate daily maintenance reports
- ✅ Implement periodic task scheduling (Celery Beat)
- ✅ Alert escalation for unacknowledged critical issues

---

## 🏗️ Architecture

```
┌──────────────────────────┐
│  ML Prediction Service   │
│  (Port 8002)             │
└─────────┬────────────────┘
          │ Redis Pub/Sub
          │ (prediction_channel)
          ▼
┌────────────────────────────────────────┐
│  Alert & Maintenance Service          │
│  (FastAPI on Port 8003)                │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  Event Subscriber                │ │
│  │  - Prediction listener           │ │
│  └──────────┬───────────────────────┘ │
│             │                          │
│  ┌──────────▼───────────────────────┐ │
│  │  Alert Engine                    │ │
│  │  - Severity classification       │ │
│  │  - Alert creation                │ │
│  │  - Deduplication logic           │ │
│  └──────────┬───────────────────────┘ │
│             │                          │
│  ┌──────────▼───────────────────────┐ │
│  │  Celery Task Queue               │ │
│  │  - Email notifications           │ │
│  │  - SMS alerts                    │ │
│  │  - Maintenance scheduling        │ │
│  │  - Daily reports                 │ │
│  │  - Cleanup jobs                  │ │
│  └──────────┬───────────────────────┘ │
│             │                          │
│  ┌──────────▼──────┬──────────┐      │
│  │                 │           │      │
│  │  PostgreSQL     │  Redis    │      │
│  │  (Alerts/Tasks) │  (Celery) │      │
│  └─────────────────┴───────────┘      │
└────────────────────────────────────────┘
```

---

## 🚀 API Endpoints

### Health Checks

#### `GET /health`
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "alert-maintenance",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### `GET /health/ready`
Readiness probe with dependencies check.

**Response:**
```json
{
  "status": "ready",
  "service": "alert-maintenance",
  "timestamp": "2025-01-01T12:00:00Z",
  "database": "connected",
  "redis": "connected",
  "celery": "running"
}
```

### Alert Operations

#### `GET /api/v1/alerts?equipment_id=RADAR-LOC-001&status=active`
List alerts with optional filtering.

**Query Parameters:**
- `equipment_id` (optional): Filter by equipment
- `status` (optional): active | acknowledged | resolved
- `severity` (optional): CRITICAL | HIGH | MEDIUM | LOW
- `limit` (optional, default: 50, max: 200)

**Response:**
```json
{
  "count": 25,
  "alerts": [
    {
      "alert_id": "alert-uuid-123",
      "equipment_id": "RADAR-LOC-001",
      "severity": "CRITICAL",
      "message": "85% failure probability detected",
      "status": "active",
      "created_at": "2025-01-01T12:00:00Z",
      "acknowledged_at": null
    }
  ]
}
```

#### `POST /api/v1/alerts/{alert_id}/acknowledge`
Acknowledge an alert.

**Request Body:**
```json
{
  "acknowledged_by": "technician-123",
  "notes": "Maintenance team notified"
}
```

**Response:**
```json
{
  "alert_id": "alert-uuid-123",
  "status": "acknowledged",
  "acknowledged_at": "2025-01-01T12:15:00Z",
  "acknowledged_by": "technician-123"
}
```

#### `POST /api/v1/alerts/{alert_id}/resolve`
Mark alert as resolved.

**Request Body:**
```json
{
  "resolved_by": "technician-123",
  "resolution_notes": "Replaced faulty cooling fan",
  "maintenance_completed": true
}
```

**Response:**
```json
{
  "alert_id": "alert-uuid-123",
  "status": "resolved",
  "resolved_at": "2025-01-02T08:30:00Z",
  "resolved_by": "technician-123"
}
```

### Maintenance Operations

#### `POST /api/v1/maintenance/schedule`
Schedule maintenance task.

**Request Body:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "task_type": "preventive",
  "priority": "high",
  "scheduled_date": "2025-01-05T10:00:00Z",
  "description": "Inspect cooling system and replace filters",
  "assigned_to": "team-alpha"
}
```

**Response:**
```json
{
  "task_id": "task-uuid-456",
  "equipment_id": "RADAR-LOC-001",
  "status": "scheduled",
  "scheduled_date": "2025-01-05T10:00:00Z",
  "created_at": "2025-01-01T12:00:00Z"
}
```

#### `GET /api/v1/maintenance/tasks?status=pending`
List maintenance tasks.

**Query Parameters:**
- `equipment_id` (optional)
- `status` (optional): scheduled | in_progress | completed | cancelled
- `priority` (optional): critical | high | medium | low

**Response:**
```json
{
  "count": 15,
  "tasks": [
    {
      "task_id": "task-uuid-456",
      "equipment_id": "RADAR-LOC-001",
      "task_type": "preventive",
      "priority": "high",
      "status": "scheduled",
      "scheduled_date": "2025-01-05T10:00:00Z",
      "assigned_to": "team-alpha"
    }
  ]
}
```

#### `PATCH /api/v1/maintenance/tasks/{task_id}/status`
Update task status.

**Request Body:**
```json
{
  "status": "completed",
  "completion_notes": "All filters replaced, system tested",
  "completed_by": "technician-123"
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | No | alert-maintenance | Service identifier |
| `PORT` | No | 8003 | Service port |
| `DATABASE_URL` | **Yes** | - | PostgreSQL async connection string |
| `REDIS_URL` | **Yes** | - | Redis connection string |
| `LOG_LEVEL` | No | INFO | Logging level |
| `DEBUG` | No | False | Enable debug mode |
| `REDIS_SUBSCRIBE_CHANNEL` | No | prediction_channel | Input channel |
| `EMAIL_ENABLED` | No | False | Enable email notifications |
| `SMS_ENABLED` | No | False | Enable SMS notifications |
| `ALERT_RETENTION_DAYS` | No | 90 | Days to keep acknowledged alerts |

### Example .env File

```bash
# Service Configuration
SERVICE_NAME=alert-maintenance
PORT=8003
DEBUG=False

# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://drdo_user:drdo_password@localhost:5432/drdo_maintenance

# Redis (REQUIRED - used by Celery too)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO

# Event Channels
REDIS_SUBSCRIBE_CHANNEL=prediction_channel

# Notification Settings
EMAIL_ENABLED=False
SMS_ENABLED=False

# Alert Settings
ALERT_RETENTION_DAYS=90
ALERT_DEDUPLICATION_WINDOW_MINUTES=60

# Database Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

---

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Setup

1. **Create virtual environment:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Configure environment:**
```powershell
cp .env.example .env
```

4. **Run FastAPI service:**
```powershell
uvicorn app.main:app --reload --port 8003
```

5. **Run Celery worker (separate terminal):**
```powershell
.\start_celery_worker.ps1
# OR manually:
celery -A app.celery_app worker --loglevel=info --pool=solo -Q notifications,maintenance,periodic,reports
```

6. **Run Celery Beat scheduler (separate terminal):**
```powershell
.\start_celery_beat.ps1
# OR manually:
celery -A app.celery_app beat --loglevel=info
```

7. **Monitor tasks with Flower (optional):**
```powershell
celery -A app.celery_app flower --port=5555
# Access at http://localhost:5555
```

---

## 🧪 Testing

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test
pytest tests/test_alerts.py -v
```

**Test Coverage Target:** 70%+

---

## ⚙️ Celery Task Queue

### Task Queues

The service uses 4 separate queues for different task types:

1. **notifications**: Email/SMS sending tasks
2. **maintenance**: Maintenance scheduling tasks
3. **periodic**: Cron-like periodic tasks
4. **reports**: Report generation tasks

### Background Tasks

#### Email Notification Task
```python
send_email_notification.delay(
    alert_id="alert-123",
    equipment_id="RADAR-LOC-001",
    severity="CRITICAL",
    message="Immediate action required"
)
```

#### SMS Notification Task
```python
send_sms_notification.delay(
    alert_id="alert-123",
    equipment_id="RADAR-LOC-001",
    severity="CRITICAL",
    phone_numbers=["+91-1234567890"]
)
```

#### Maintenance Scheduling Task
```python
schedule_maintenance_task.delay(
    equipment_id="RADAR-LOC-001",
    task_type="preventive",
    priority="high",
    description="Inspect cooling system"
)
```

### Periodic Tasks (Celery Beat)

| Task | Schedule | Description |
|------|----------|-------------|
| `check_critical_alerts` | Every 5 minutes | Check unacknowledged critical alerts, send escalations |
| `send_daily_maintenance_report` | Daily at 8 AM | Generate and email maintenance summary |
| `cleanup_old_alerts` | Daily at 2 AM | Delete acknowledged alerts older than 90 days |

---

## 📦 Database Schema

### Table: `alerts`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | Alert identifier (UUID) |
| `equipment_id` | VARCHAR(50) | NOT NULL, INDEX | Equipment identifier |
| `prediction_id` | VARCHAR(36) | FOREIGN KEY | Related prediction |
| `severity` | VARCHAR(20) | NOT NULL, INDEX | CRITICAL/HIGH/MEDIUM/LOW |
| `message` | TEXT | NOT NULL | Alert message |
| `status` | VARCHAR(20) | NOT NULL, INDEX | active/acknowledged/resolved |
| `created_at` | TIMESTAMP | NOT NULL, INDEX | Alert creation time |
| `acknowledged_at` | TIMESTAMP | NULLABLE | Acknowledgment time |
| `acknowledged_by` | VARCHAR(100) | NULLABLE | User who acknowledged |
| `resolved_at` | TIMESTAMP | NULLABLE | Resolution time |
| `resolved_by` | VARCHAR(100) | NULLABLE | User who resolved |
| `resolution_notes` | TEXT | NULLABLE | Resolution details |

### Table: `maintenance_tasks`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | Task identifier (UUID) |
| `equipment_id` | VARCHAR(50) | NOT NULL, INDEX | Equipment identifier |
| `alert_id` | VARCHAR(36) | FOREIGN KEY | Related alert (optional) |
| `task_type` | VARCHAR(50) | NOT NULL | preventive/corrective/inspection |
| `priority` | VARCHAR(20) | NOT NULL, INDEX | critical/high/medium/low |
| `status` | VARCHAR(20) | NOT NULL, INDEX | scheduled/in_progress/completed/cancelled |
| `description` | TEXT | NOT NULL | Task description |
| `scheduled_date` | TIMESTAMP | NOT NULL, INDEX | Scheduled time |
| `completed_date` | TIMESTAMP | NULLABLE | Completion time |
| `assigned_to` | VARCHAR(100) | NULLABLE | Assigned team/person |
| `completed_by` | VARCHAR(100) | NULLABLE | Completion user |
| `completion_notes` | TEXT | NULLABLE | Completion details |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation |

---

## 📡 Event Processing

### Subscribed Events

**Channel:** `prediction_channel`

**Event Format:**
```json
{
  "event_type": "prediction_completed",
  "prediction_id": "pred-uuid-12345",
  "equipment_id": "RADAR-LOC-001",
  "timestamp": "2025-01-01T12:00:00Z",
  "failure_probability": 0.85,
  "health_score": 30.5,
  "severity": "CRITICAL",
  "days_until_failure": 7
}
```

### Alert Generation Logic

Alerts are created when:
- Severity is **HIGH** or **CRITICAL**
- No duplicate alert exists for same equipment in last 60 minutes
- Failure probability > 0.6

Notification channels:
- **CRITICAL** severity: Email + SMS
- **HIGH** severity: Email only

---

## 🔔 Notifications

### Email Notification (Placeholder)

Currently logs notification intent. To implement:

```python
# TODO: Configure SMTP settings
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "alerts@drdo.gov.in"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
```

### SMS Notification (Placeholder)

Currently logs notification intent. To implement with Twilio:

```python
# TODO: Configure Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = "+91-1234567890"
```

---

## 📊 Alert Workflow

```
Prediction (severity ≥ HIGH)
    ↓
Check for duplicates (60 min window)
    ↓
Create Alert (status: active)
    ↓
Enqueue Notification Task (Celery)
    ↓
Send Email/SMS
    ↓
Alert remains active until acknowledged
    ↓
Technician acknowledges alert
    ↓
Status: acknowledged
    ↓
Maintenance scheduled
    ↓
Maintenance completed
    ↓
Alert resolved
    ↓
Status: resolved
    ↓
After 90 days: Auto-deleted by cleanup job
```

---

## 🐛 Troubleshooting

### Celery Worker Not Starting
```
Error: Connection refused
```
**Solution:**
- Verify Redis is running
- Check REDIS_URL in .env
- On Windows, use `--pool=solo` flag

### Tasks Not Executing
**Solution:**
- Check Celery worker is running
- Verify queue names match
- Check Celery logs for errors

### Duplicate Alerts
**Solution:**
- Check `ALERT_DEDUPLICATION_WINDOW_MINUTES` setting
- Verify database query in alert creation logic

---

## 📝 Logging

Structured JSON logs:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "service": "alert-maintenance",
  "message": "Alert created",
  "alert_id": "alert-123",
  "equipment_id": "RADAR-LOC-001",
  "severity": "CRITICAL"
}
```

---

## 🔗 Related Services

- **ML Prediction Service** (Port 8002): Provides prediction events
- **Dashboard Service** (Port 8004): Displays alerts and tasks

---

**Service Version:** 1.0.0  
**Last Updated:** 2025-01-02  
**Maintainer:** DRDO Development Team
