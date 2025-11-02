# Sensor Data Ingestion Service

**Port**: 8001  
**Purpose**: Data collection, validation, and storage for DRDO equipment sensors

## Overview

This microservice handles the ingestion of sensor data from DRDO defense equipment. It validates incoming sensor readings against predefined constraints, stores them in PostgreSQL, and publishes events to Redis for downstream services.

## Features

- ✅ Real-time sensor data ingestion
- ✅ Equipment ID validation (pattern: TYPE-LOCATION-NUMBER)
- ✅ Sensor reading validation against DRDO constraints
- ✅ Async database operations with connection pooling
- ✅ Redis pub/sub for event-driven architecture
- ✅ Structured JSON logging
- ✅ Health check endpoints for monitoring
- ✅ OpenAPI/Swagger documentation

## API Endpoints

### Health Checks

#### `GET /health`
Basic health check without dependencies.

**Response**:
```json
{
  "status": "healthy",
  "service": "sensor-ingestion",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### `GET /health/ready`
Readiness probe with database and Redis connectivity check.

**Response**:
```json
{
  "status": "ready",
  "service": "sensor-ingestion",
  "timestamp": "2025-01-01T12:00:00Z",
  "database": "connected",
  "redis": "connected"
}
```

### Sensor Data

#### `POST /api/v1/sensors/ingest`
Ingest sensor data from equipment.

**Request Body**:
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

**Response** (201 Created):
```json
{
  "reading_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "equipment_id": "RADAR-LOC-001",
  "timestamp": "2025-01-01T12:00:00Z",
  "status": "received"
}
```

#### `GET /api/v1/sensors/{equipment_id}/latest?limit=10`
Retrieve latest sensor readings for specific equipment.

**Response**:
```json
{
  "equipment_id": "RADAR-LOC-001",
  "count": 10,
  "readings": [
    {
      "id": "uuid",
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

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | No | sensor-ingestion | Service identifier |
| `PORT` | No | 8001 | Service port |
| `DATABASE_URL` | **Yes** | - | PostgreSQL connection string |
| `REDIS_URL` | **Yes** | - | Redis connection string |
| `LOG_LEVEL` | No | INFO | Logging level |
| `DEBUG` | No | False | Debug mode |
| `MIN_TEMPERATURE` | No | -50.0 | Minimum valid temperature (°C) |
| `MAX_TEMPERATURE` | No | 200.0 | Maximum valid temperature (°C) |
| `MIN_VIBRATION` | No | 0.0 | Minimum valid vibration (mm/s) |
| `MAX_VIBRATION` | No | 2.0 | Maximum valid vibration (mm/s) |
| `MIN_PRESSURE` | No | 0.0 | Minimum valid pressure (bar) |
| `MAX_PRESSURE` | No | 10.0 | Maximum valid pressure (bar) |

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Setup

1. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run service**
```bash
uvicorn app.main:app --reload --port 8001
```

5. **Access API documentation**
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_main.py -v
```

## Docker

### Build Image
```bash
docker build -t drdo/sensor-ingestion:latest .
```

### Run Container
```bash
docker run -p 8001:8001 --env-file .env drdo/sensor-ingestion:latest
```

## Validation Rules

### Equipment ID
- **Pattern**: `TYPE-LOCATION-NUMBER`
- **Examples**: 
  - ✅ RADAR-LOC-001
  - ✅ AIRCRAFT-BASE-042
  - ❌ radar001
  - ❌ RADAR_001

### Sensor Constraints
| Sensor | Min | Max | Unit |
|--------|-----|-----|------|
| Temperature | -50.0 | 200.0 | °C |
| Vibration | 0.0 | 2.0 | mm/s |
| Pressure | 0.0 | 10.0 | bar |
| Humidity | 0.0 | 100.0 | % |
| Voltage | 0.0 | 500.0 | V |

## Event Publishing

When sensor data is ingested, an event is published to Redis:

**Channel**: `sensor_data_channel`

**Event Format**:
```json
{
  "event_type": "sensor_data_received",
  "reading_id": "uuid",
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

## Logging

All logs are output in structured JSON format to stdout:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "service": "sensor-ingestion",
  "message": "Sensor data ingested",
  "module": "services",
  "function": "ingest_sensor_data"
}
```

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:port/db`
- Check PostgreSQL is running and accessible
- Verify network connectivity and firewall rules

### Redis Connection Issues
- Verify `REDIS_URL` format: `redis://host:port/db`
- Check Redis is running: `redis-cli ping`
- Verify network connectivity

### Validation Errors
- Ensure equipment ID follows pattern: `TYPE-LOCATION-NUMBER`
- Check sensor readings are within valid ranges
- Review validation constraints in `.env` file

## Performance

- **Target Response Time**: <100ms for ingestion
- **Database Connection Pool**: 10 base connections, 20 max overflow
- **Concurrent Requests**: Handles 100+ concurrent requests
- **Throughput**: 1000+ readings per second

## Security

- Non-root user in Docker container
- No hardcoded credentials
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for API access control

---

**Service Version**: 1.0.0  
**Last Updated**: 2025-01-01
