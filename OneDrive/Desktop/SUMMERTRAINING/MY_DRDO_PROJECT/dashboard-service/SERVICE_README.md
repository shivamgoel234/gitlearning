# Dashboard Service

**Port**: 8004  
**Domain**: Data Visualization & Reporting  
**Technology Stack**: FastAPI, Streamlit, PostgreSQL (Read-Only), Redis

---

## 📋 Overview

The Dashboard Service is the visualization and reporting layer of the DRDO Equipment Maintenance Prediction System. It aggregates data from all microservices and provides comprehensive dashboards, analytics, and reports.

### Key Responsibilities

- ✅ Aggregate data from sensor, prediction, alert, and maintenance services
- ✅ Provide real-time equipment health monitoring dashboard
- ✅ Display alert statistics and trends
- ✅ Show maintenance task schedules and completion rates
- ✅ Generate downloadable reports (PDF/CSV)
- ✅ Visualize time-series sensor data and predictions
- ✅ Provide fleet-wide health overview
- ✅ Implement user authentication and role-based access (future enhancement)

---

## 🏗️ Architecture

```
┌────────────────────────────────────────┐
│  Dashboard Service (Port 8004)         │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │  FastAPI Backend (main.py)       │ │
│  │  - REST API endpoints            │ │
│  │  - Data aggregation              │ │
│  └──────────┬───────────────────────┘ │
│             │                          │
│  ┌──────────▼───────────────────────┐ │
│  │  Business Logic (services.py)    │ │
│  │  - Query all microservices       │ │
│  │  - Aggregate statistics          │ │
│  │  - Generate reports              │ │
│  └──────────┬───────────────────────┘ │
│             │                          │
│  ┌──────────▼──────┬──────────┐      │
│  │                 │           │      │
│  │  PostgreSQL     │  Redis    │      │
│  │  (Read-Only)    │  (Cache)  │      │
│  └─────────────────┴───────────┘      │
└────────────────────────────────────────┘
         │
         │ HTTP/REST calls
         ▼
┌────────────────────────────────────────┐
│  Other Services                        │
│  - Sensor Ingestion (8001)             │
│  - ML Prediction (8002)                │
│  - Alert Maintenance (8003)            │
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
  "service": "dashboard",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### `GET /health/ready`
Readiness probe with database check.

**Response:**
```json
{
  "status": "ready",
  "service": "dashboard",
  "timestamp": "2025-01-01T12:00:00Z",
  "database": "connected"
}
```

### Dashboard Data Endpoints

#### `GET /api/v1/dashboard/overview`
Get system-wide overview statistics.

**Response:**
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "total_equipment": 150,
  "active_alerts": 23,
  "critical_alerts": 5,
  "high_alerts": 18,
  "pending_maintenance": 42,
  "average_fleet_health": 72.5,
  "equipment_by_severity": {
    "CRITICAL": 5,
    "HIGH": 18,
    "MEDIUM": 37,
    "LOW": 90
  }
}
```

#### `GET /api/v1/dashboard/equipment/{equipment_id}/details`
Get detailed information for specific equipment.

**Response:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "current_health_score": 65.3,
  "current_severity": "MEDIUM",
  "latest_sensor_reading": {
    "timestamp": "2025-01-01T12:00:00Z",
    "temperature": 85.5,
    "vibration": 0.45,
    "pressure": 3.2,
    "humidity": 65.0,
    "voltage": 220.0
  },
  "latest_prediction": {
    "timestamp": "2025-01-01T12:05:00Z",
    "failure_probability": 0.45,
    "health_score": 65.3,
    "severity": "MEDIUM",
    "days_until_failure": 30
  },
  "active_alerts": [
    {
      "alert_id": "alert-123",
      "severity": "MEDIUM",
      "message": "Elevated temperature detected",
      "created_at": "2025-01-01T11:00:00Z",
      "status": "active"
    }
  ],
  "scheduled_maintenance": [
    {
      "task_id": "task-456",
      "task_type": "preventive",
      "scheduled_date": "2025-01-05T10:00:00Z",
      "priority": "medium"
    }
  ]
}
```

#### `GET /api/v1/dashboard/alerts/active`
List all active alerts across fleet.

**Query Parameters:**
- `severity` (optional): Filter by severity
- `equipment_id` (optional): Filter by equipment
- `limit` (optional, default: 100)

**Response:**
```json
{
  "count": 23,
  "alerts": [
    {
      "alert_id": "alert-123",
      "equipment_id": "RADAR-LOC-001",
      "severity": "CRITICAL",
      "message": "85% failure probability detected",
      "created_at": "2025-01-01T12:00:00Z",
      "status": "active"
    }
  ]
}
```

#### `GET /api/v1/dashboard/maintenance/upcoming?days=7`
Get upcoming maintenance tasks.

**Parameters:**
- `days` (query): Number of days ahead to retrieve (default: 7)

**Response:**
```json
{
  "period_days": 7,
  "count": 15,
  "tasks": [
    {
      "task_id": "task-456",
      "equipment_id": "RADAR-LOC-001",
      "task_type": "preventive",
      "priority": "high",
      "scheduled_date": "2025-01-05T10:00:00Z",
      "status": "scheduled"
    }
  ]
}
```

#### `GET /api/v1/dashboard/health-trend?period=7d`
Get fleet-wide health trend.

**Parameters:**
- `period` (query): Time period (7d, 30d, 90d)

**Response:**
```json
{
  "period": "7d",
  "data_points": 168,
  "trend": "declining",
  "health_scores": [
    {"timestamp": "2025-01-01T00:00:00Z", "average_score": 75.2},
    {"timestamp": "2025-01-01T01:00:00Z", "average_score": 74.8}
  ],
  "average_score": 72.5,
  "min_score": 30.5,
  "max_score": 95.7
}
```

### Analytics Endpoints

#### `GET /api/v1/analytics/sensor-statistics/{equipment_id}?days=30`
Get sensor statistics for equipment.

**Response:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "period_days": 30,
  "statistics": {
    "temperature": {
      "mean": 85.3,
      "median": 84.7,
      "std": 5.2,
      "min": 72.5,
      "max": 98.3
    },
    "vibration": {
      "mean": 0.45,
      "median": 0.43,
      "std": 0.12,
      "min": 0.20,
      "max": 0.85
    }
  }
}
```

#### `GET /api/v1/analytics/alert-statistics?start_date=2025-01-01&end_date=2025-01-31`
Get alert statistics for date range.

**Response:**
```json
{
  "period": "2025-01-01 to 2025-01-31",
  "total_alerts": 150,
  "by_severity": {
    "CRITICAL": 20,
    "HIGH": 45,
    "MEDIUM": 60,
    "LOW": 25
  },
  "acknowledged_rate": 0.87,
  "average_resolution_time_hours": 24.5,
  "top_equipment_by_alerts": [
    {"equipment_id": "RADAR-LOC-001", "alert_count": 15},
    {"equipment_id": "AIRCRAFT-BASE-042", "alert_count": 12}
  ]
}
```

### Report Generation

#### `POST /api/v1/reports/generate`
Generate downloadable report.

**Request Body:**
```json
{
  "report_type": "maintenance_summary",
  "format": "pdf",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "include_charts": true
}
```

**Response:**
```json
{
  "report_id": "report-uuid-789",
  "status": "generated",
  "download_url": "/api/v1/reports/download/report-uuid-789",
  "generated_at": "2025-01-01T12:00:00Z",
  "expires_at": "2025-01-08T12:00:00Z"
}
```

#### `GET /api/v1/reports/download/{report_id}`
Download generated report file.

**Response:** Binary file (PDF/CSV)

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | No | dashboard | Service identifier |
| `PORT` | No | 8004 | Service port |
| `DATABASE_URL` | **Yes** | - | PostgreSQL connection string (read-only) |
| `REDIS_URL` | No | - | Redis connection string (for caching) |
| `LOG_LEVEL` | No | INFO | Logging level |
| `DEBUG` | No | False | Enable debug mode |
| `CACHE_TTL_SECONDS` | No | 300 | Cache time-to-live (5 minutes) |
| `SENSOR_SERVICE_URL` | **Yes** | - | Sensor ingestion service URL |
| `ML_SERVICE_URL` | **Yes** | - | ML prediction service URL |
| `ALERT_SERVICE_URL` | **Yes** | - | Alert maintenance service URL |

### Example .env File

```bash
# Service Configuration
SERVICE_NAME=dashboard
PORT=8004
DEBUG=False

# Database (REQUIRED - Read-Only User)
DATABASE_URL=postgresql+asyncpg://dashboard_user:read_password@localhost:5432/drdo_maintenance

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO

# Caching
CACHE_TTL_SECONDS=300

# Microservice URLs (REQUIRED)
SENSOR_SERVICE_URL=http://localhost:8001
ML_SERVICE_URL=http://localhost:8002
ALERT_SERVICE_URL=http://localhost:8003

# Database Pool (Read-Only)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

---

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (read-only access)
- Redis 7+ (optional, for caching)
- Other microservices running (8001, 8002, 8003)

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
# Set service URLs to running microservices
```

4. **Run FastAPI backend:**
```powershell
uvicorn app.main:app --reload --port 8004
```

5. **Access API documentation:**
- Swagger UI: http://localhost:8004/docs
- ReDoc: http://localhost:8004/redoc

---

## 🧪 Testing

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test
pytest tests/test_dashboard.py -v
```

**Test Coverage Target:** 70%+

---

## 🎨 Streamlit Dashboard (Optional Enhancement)

For a richer UI experience, you can add a Streamlit dashboard:

**File:** `streamlit_app.py` (create in dashboard-service root)

```python
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Dashboard configuration
st.set_page_config(page_title="DRDO Equipment Monitor", layout="wide")
st.title("🛡️ DRDO Equipment Maintenance Dashboard")

# Fetch overview data
overview = requests.get("http://localhost:8004/api/v1/dashboard/overview").json()

# Display key metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Equipment", overview["total_equipment"])
col2.metric("Active Alerts", overview["active_alerts"])
col3.metric("Critical Alerts", overview["critical_alerts"], delta_color="inverse")
col4.metric("Fleet Health", f"{overview['average_fleet_health']:.1f}%")

# Equipment severity distribution
st.subheader("Equipment by Severity")
severity_df = pd.DataFrame(list(overview["equipment_by_severity"].items()), 
                           columns=["Severity", "Count"])
fig = px.bar(severity_df, x="Severity", y="Count", color="Severity")
st.plotly_chart(fig)

# Active alerts table
st.subheader("Active Alerts")
alerts = requests.get("http://localhost:8004/api/v1/dashboard/alerts/active").json()
if alerts["count"] > 0:
    alerts_df = pd.DataFrame(alerts["alerts"])
    st.dataframe(alerts_df)
else:
    st.info("No active alerts")
```

**Run Streamlit:**
```powershell
streamlit run streamlit_app.py --server.port 8501
# Access at http://localhost:8501
```

---

## 📊 Data Aggregation

The dashboard service aggregates data by querying:

1. **PostgreSQL Database (Read-Only)**:
   - Sensor readings from `sensor_data` table
   - Predictions from `predictions` table
   - Alerts from `alerts` table
   - Maintenance tasks from `maintenance_tasks` table

2. **Other Microservices (REST APIs)**:
   - Real-time equipment status
   - Latest predictions
   - Alert acknowledgment status

### Caching Strategy

To reduce database load, responses are cached in Redis:
- Overview statistics: 5 minutes TTL
- Equipment details: 2 minutes TTL
- Historical trends: 15 minutes TTL

---

## 📦 Database Access

### Read-Only User Setup

Create a read-only database user for security:

```sql
-- Create read-only user
CREATE USER dashboard_user WITH PASSWORD 'read_password';

-- Grant connection to database
GRANT CONNECT ON DATABASE drdo_maintenance TO dashboard_user;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO dashboard_user;

-- Grant SELECT on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dashboard_user;

-- Grant SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO dashboard_user;
```

---

## 📈 Visualization Examples

### Health Score Trend Chart

```python
# Endpoint: GET /api/v1/dashboard/health-trend?period=7d
# Response visualized as line chart with:
# X-axis: Timestamp
# Y-axis: Average health score
# Color zones: Green (>70), Yellow (50-70), Red (<50)
```

### Alert Distribution Pie Chart

```python
# Endpoint: GET /api/v1/analytics/alert-statistics
# Response visualized as pie chart:
# Slices: CRITICAL (red), HIGH (orange), MEDIUM (yellow), LOW (green)
```

### Equipment Heatmap

```python
# Grid layout showing all equipment with color coding:
# Green: Health score > 70
# Yellow: Health score 50-70
# Orange: Health score 30-50
# Red: Health score < 30
```

---

## 🔄 Real-Time Updates

For real-time dashboard updates, implement WebSocket support:

```python
# TODO: Add WebSocket endpoint for real-time updates
from fastapi import WebSocket

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Push updates every 10 seconds
        overview = await get_overview()
        await websocket.send_json(overview)
        await asyncio.sleep(10)
```

---

## 📄 Report Templates

### Maintenance Summary Report

Includes:
- Total alerts generated
- Alert resolution rate
- Maintenance tasks completed
- Equipment uptime statistics
- Top 10 equipment by alert frequency
- Health score distribution

### Equipment Health Report

Includes:
- Current health scores for all equipment
- Health trend over time
- Sensor reading anomalies
- Predicted maintenance dates
- Recommendations

---

## 🐛 Troubleshooting

### Service Connection Errors
```
Error: Failed to connect to sensor-ingestion service
```
**Solution:**
- Verify other services are running
- Check service URLs in .env
- Test connectivity: `curl http://localhost:8001/health`

### Database Read Errors
```
Error: Permission denied for table sensor_data
```
**Solution:**
- Verify read-only user has SELECT permissions
- Run grant commands above
- Check DATABASE_URL in .env

### Slow Dashboard Loading
**Solution:**
- Enable Redis caching
- Increase CACHE_TTL_SECONDS
- Check database query performance
- Add database indexes on frequently queried columns

---

## 📝 Logging

Structured JSON logs:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "service": "dashboard",
  "message": "Overview data fetched",
  "total_equipment": 150,
  "active_alerts": 23,
  "response_time_ms": 125.3
}
```

---

## 🔗 Related Services

- **Sensor Ingestion Service** (Port 8001): Provides sensor data
- **ML Prediction Service** (Port 8002): Provides predictions
- **Alert Maintenance Service** (Port 8003): Provides alerts and tasks

---

## 🚀 Future Enhancements

- [ ] Add user authentication (JWT tokens)
- [ ] Implement role-based access control (admin, viewer)
- [ ] Add equipment comparison feature
- [ ] Implement custom alert rules configuration
- [ ] Add export to Excel feature
- [ ] Implement email report scheduling
- [ ] Add mobile-responsive UI
- [ ] Implement dark mode theme

---

**Service Version:** 1.0.0  
**Last Updated:** 2025-01-02  
**Maintainer:** DRDO Development Team
