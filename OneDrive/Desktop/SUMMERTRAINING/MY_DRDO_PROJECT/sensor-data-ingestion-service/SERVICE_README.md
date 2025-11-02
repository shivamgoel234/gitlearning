# Sensor Data Ingestion Service

**Port**: 8001  
**Domain**: Data Collection and Preprocessing  
**Technology Stack**: FastAPI, PostgreSQL, Redis, SQLAlchemy

---

## 📋 Overview

The Sensor Data Ingestion Service is the entry point for all equipment sensor data in the DRDO Equipment Maintenance Prediction System. It handles real-time data collection, validation, storage, and event publishing.

### Key Responsibilities

- ✅ Accept sensor readings from IoT devices and equipment
- ✅ Validate data against DRDO sensor constraints
- ✅ Validate equipment ID format (TYPE-LOCATION-NUMBER)
- ✅ Store validated readings in PostgreSQL
- ✅ Publish events to Redis for downstream services
- ✅ Provide query endpoints for historical data
- ✅ Implement health checks for monitoring

---

## 🏗️ Architecture

```
┌─────────────────┐
│  IoT Devices/   │
│  Equipment      │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────────────────────────┐
│  Sensor Data Ingestion Service     │
│  (FastAPI on Port 8001)             │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  API Layer (main.py)         │  │
│  │  - /api/v1/sensors/ingest    │  │
│  │  - /health, /health/ready    │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼───────────────────┐  │
│  │  Service Layer (services.py) │  │
│  │  - Validation logic          │  │
│  │  - Business rules            │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│  ┌──────────▼──────┬──────────┐   │
│  │                 │           │   │
│  │  PostgreSQL     │  Redis    │   │
│  │  (Storage)      │  (Events) │   │
│  └─────────────────┴───────────┘   │
└─────────────────────────────────────┘
         │
         │ Redis Pub/Sub
         ▼
┌─────────────────────┐
│  ML Prediction      │
│  Service            │
└─────────────────────┘
```

---

## 🚀 API Endpoints

### Health Checks

#### `GET /health`
Basic health check without dependencies.

**Response:**
```json
{
  "status": "healthy",
  "service": "sensor-ingestion",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### `GET /health/ready`
Readiness probe with database and Redis connectivity check.

**Response:**
```json
{
  "status": "ready",
  "service": "sensor-ingestion",
  "timestamp": "2025-01-01T12:00:00Z",
  "database": "connected",
  "redis": "connected"
}
```

### Sensor Data Operations

#### `POST /api/v1/sensors/ingest`
Ingest sensor data from equipment.

**Request Body:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "temperature": 85.5,
  "vibration": 0.45,
  "pressure": 3.2,
  "humidity": 65.0,
  "voltage": 220.0,
  "source": "iot-sensor-01",
  "notes": "Regular monitoring"
}
```

**Field Validation:**
- `equipment_id`: Must match pattern `TYPE-LOCATION-NUMBER` (e.g., RADAR-LOC-001)
- `temperature`: -50.0 to 200.0 °C
- `vibration`: 0.0 to 2.0 mm/s
- `pressure`: 0.0 to 10.0 bar
- `humidity`: 0.0 to 100.0 % (optional)
- `voltage`: 0.0 to 500.0 V (optional)

**Success Response (201 Created):**
```json
{
  "reading_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "equipment_id": "RADAR-LOC-001",
  "timestamp": "2025-01-01T12:00:00Z",
  "status": "received"
}
```

**Error Response (422 Validation Error):**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid equipment ID format",
  "details": {
    "field": "equipment_id",
    "constraint": "Must match pattern TYPE-LOCATION-NUMBER"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### `GET /api/v1/sensors/{equipment_id}/latest?limit=10`
Retrieve latest sensor readings for specific equipment.

**Parameters:**
- `equipment_id` (path): Equipment identifier (e.g., RADAR-LOC-001)
- `limit` (query): Number of readings to return (default: 10, max: 100)

**Response:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "count": 10,
  "readings": [
    {
      "id": "uuid-1",
      "timestamp": "2025-01-01T12:00:00Z",
      "temperature": 85.5,
      "vibration": 0.45,
      "pressure": 3.2,
      "humidity": 65.0,
      "voltage": 220.0
    }
  ]
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | No | sensor-ingestion | Service identifier |
| `PORT` | No | 8001 | Service port |
| `DATABASE_URL` | **Yes** | - | PostgreSQL async connection string |
| `REDIS_URL` | **Yes** | - | Redis connection string |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DEBUG` | No | False | Enable debug mode |
| `MIN_TEMPERATURE` | No | -50.0 | Minimum valid temperature (°C) |
| `MAX_TEMPERATURE` | No | 200.0 | Maximum valid temperature (°C) |
| `MIN_VIBRATION` | No | 0.0 | Minimum valid vibration (mm/s) |
| `MAX_VIBRATION` | No | 2.0 | Maximum valid vibration (mm/s) |
| `MIN_PRESSURE` | No | 0.0 | Minimum valid pressure (bar) |
| `MAX_PRESSURE` | No | 10.0 | Maximum valid pressure (bar) |
| `CORS_ORIGINS` | No | * | Allowed CORS origins |
| `DB_POOL_SIZE` | No | 10 | Database connection pool size |
| `DB_MAX_OVERFLOW` | No | 20 | Max overflow connections |

### Example .env File

```bash
# Service Configuration
SERVICE_NAME=sensor-ingestion
PORT=8001
DEBUG=False

# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://drdo_user:drdo_password@localhost:5432/drdo_maintenance

# Redis (REQUIRED)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO

# Sensor Constraints
MIN_TEMPERATURE=-50.0
MAX_TEMPERATURE=200.0
MIN_VIBRATION=0.0
MAX_VIBRATION=2.0
MIN_PRESSURE=0.0
MAX_PRESSURE=10.0

# CORS
CORS_ORIGINS=*

# Database Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
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
.\venv\Scripts\Activate.ps1  # Windows
```

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Configure environment:**
```powershell
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize database:**
```powershell
# Ensure PostgreSQL is running
docker-compose up -d postgres

# Tables are created automatically on first run
```

5. **Run service:**
```powershell
uvicorn app.main:app --reload --port 8001
```

6. **Access API documentation:**
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 🧪 Testing

### Run Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_main.py -v

# Run only integration tests
pytest tests/ -m integration
```

### Test Coverage

Target: **70%+ code coverage**

Current test suites:
- `test_main.py`: API endpoint tests
- `test_services.py`: Business logic tests
- `test_models.py`: Pydantic validation tests

---

## 📦 Database Schema

### Table: `sensor_data`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | Unique reading identifier (UUID) |
| `equipment_id` | VARCHAR(50) | NOT NULL, INDEX | Equipment identifier |
| `timestamp` | TIMESTAMP | NOT NULL, INDEX | Reading timestamp (UTC) |
| `temperature` | FLOAT | NOT NULL | Temperature in °C |
| `vibration` | FLOAT | NOT NULL | Vibration in mm/s |
| `pressure` | FLOAT | NOT NULL | Pressure in bar |
| `humidity` | FLOAT | NULLABLE | Humidity in % |
| `voltage` | FLOAT | NULLABLE | Voltage in V |
| `source` | VARCHAR(50) | NULLABLE | Data source identifier |
| `notes` | TEXT | NULLABLE | Additional notes |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |

### Indexes

- Primary key on `id`
- Index on `equipment_id` for fast lookups
- Index on `timestamp` for time-series queries
- Composite index on `(equipment_id, timestamp)` for equipment history

---

## 📡 Event Publishing

When sensor data is successfully ingested, an event is published to Redis pub/sub:

**Channel:** `sensor_data_channel`

**Event Format:**
```json
{
  "event_type": "sensor_data_received",
  "reading_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "equipment_id": "RADAR-LOC-001",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": {
    "temperature": 85.5,
    "vibration": 0.45,
    "pressure": 3.2,
    "humidity": 65.0,
    "voltage": 220.0
  }
}
```

**Subscribers:**
- ML Prediction Service (processes readings for failure prediction)

---

## 🔒 Validation Rules

### Equipment ID Format

**Pattern:** `TYPE-LOCATION-NUMBER`

**Examples:**
- ✅ `RADAR-LOC-001`
- ✅ `AIRCRAFT-BASE-042`
- ✅ `NAVAL-PORT-123`
- ❌ `radar001` (lowercase)
- ❌ `RADAR_001` (underscore)
- ❌ `R-1` (too short)

### Sensor Constraints

| Sensor | Min | Max | Unit |
|--------|-----|-----|------|
| Temperature | -50.0 | 200.0 | °C |
| Vibration | 0.0 | 2.0 | mm/s |
| Pressure | 0.0 | 10.0 | bar |
| Humidity | 0.0 | 100.0 | % |
| Voltage | 0.0 | 500.0 | V |

---

## 📊 Performance

### Benchmarks

- **Target Response Time**: <100ms for ingestion
- **Database Connection Pool**: 10 base connections, 20 max overflow
- **Concurrent Requests**: Handles 100+ concurrent requests
- **Throughput**: 1000+ readings per second

### Optimization Tips

1. **Database Connection Pooling**: Already configured with SQLAlchemy
2. **Redis Pipeline**: Batch Redis operations when possible
3. **Async Operations**: All I/O operations use async/await
4. **Index Usage**: Queries optimized with proper indexes

---

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Failed
```
Error: could not connect to server
```
**Solution:**
- Verify PostgreSQL is running: `docker ps | grep postgres`
- Check DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/db`
- Verify credentials and database exists

#### Redis Connection Failed
```
Error: Connection refused
```
**Solution:**
- Verify Redis is running: `docker ps | grep redis`
- Check REDIS_URL format: `redis://host:port/db`
- Test connection: `redis-cli ping`

#### Validation Errors
```
422 Unprocessable Entity: Invalid equipment ID
```
**Solution:**
- Ensure equipment ID follows pattern: `TYPE-LOCATION-NUMBER`
- All letters must be uppercase
- Number must be exactly 3 digits
- Example: `RADAR-LOC-001`

---

## 📝 Logging

All logs are output in structured JSON format:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "service": "sensor-ingestion",
  "message": "Sensor data ingested",
  "module": "services",
  "function": "ingest_sensor_data",
  "equipment_id": "RADAR-LOC-001"
}
```

---

## 🔗 Related Services

- **ML Prediction Service** (Port 8002): Consumes sensor data events for predictions
- **Alert Maintenance Service** (Port 8003): Uses sensor data for alert generation
- **Dashboard Service** (Port 8004): Visualizes sensor data history

---

**Service Version:** 1.0.0  
**Last Updated:** 2025-01-02  
**Maintainer:** DRDO Development Team
