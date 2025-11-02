# Sensor Data Ingestion Service

Production-ready microservice for ingesting sensor data from DRDO defense equipment. Built with FastAPI, PostgreSQL, Redis, and following 12-factor app principles.

## 🎯 Service Overview

**Domain**: Data Collection & Preprocessing  
**Port**: 8001  
**Version**: 1.0.0

### Responsibilities

- Accept sensor readings from equipment via REST API
- Validate sensor data against defined constraints
- Store sensor data in PostgreSQL database
- Publish validated data to Redis queue for ML prediction service
- Provide query endpoints for historical data retrieval
- Health checks for Kubernetes deployment

## 📋 Features

✅ **REST API** with OpenAPI documentation  
✅ **Async PostgreSQL** with connection pooling  
✅ **Redis queue** for event-driven architecture  
✅ **Request ID tracking** for distributed tracing  
✅ **Structured JSON logging** to stdout  
✅ **Health & readiness probes** for Kubernetes  
✅ **Comprehensive validation** with Pydantic  
✅ **Error handling** with custom exceptions  
✅ **Batch ingestion** support (up to 100 readings)  
✅ **Docker & docker-compose** ready  
✅ **Test coverage** with pytest

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────┐
│  Sensor Ingestion API   │
│     (FastAPI)           │
└───┬──────────────┬──────┘
    │              │
    │ Write        │ Publish
    ▼              ▼
┌────────┐    ┌─────────┐
│ PostgreSQL   │  Redis  │
│ (Storage)│    │ (Queue) │
└──────────┘    └────┬────┘
                     │ Consume
                     ▼
                ┌────────────┐
                │ ML Service │
                └────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### 1. Local Development (without Docker)

```bash
# Clone repository
cd services/sensor-ingestion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env with your database and Redis URLs
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/drdo_maintenance
# REDIS_URL=redis://localhost:6379/0

# Run the service
python -m uvicorn app.main:app --reload --port 8001
```

### 2. Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, API)
docker-compose up -d

# View logs
docker-compose logs -f sensor-ingestion

# Stop services
docker-compose down
```

### 3. Verify Installation

```bash
# Check health
curl http://localhost:8001/health

# View API documentation
open http://localhost:8001/docs
```

## 📡 API Endpoints

### Health Checks

```http
GET /health
GET /health/ready
```

### Sensor Data Ingestion

#### Ingest Single Reading

```http
POST /api/v1/sensors/ingest
Content-Type: application/json

{
  "equipment_id": "RADAR-LOC-001",
  "temperature": 85.5,
  "vibration": 0.45,
  "pressure": 3.2,
  "humidity": 65.0,
  "voltage": 220.0
}
```

**Response (201 Created):**
```json
{
  "reading_id": "123e4567-e89b-12d3-a456-426614174000",
  "equipment_id": "RADAR-LOC-001",
  "status": "received",
  "timestamp": "2025-11-01T18:30:00Z",
  "message": "Sensor data ingested successfully"
}
```

#### Ingest Batch

```http
POST /api/v1/sensors/ingest/batch
Content-Type: application/json

{
  "readings": [
    {
      "equipment_id": "RADAR-LOC-001",
      "temperature": 85.5,
      "vibration": 0.45,
      "pressure": 3.2
    },
    {
      "equipment_id": "RADAR-LOC-002",
      "temperature": 78.2,
      "vibration": 0.38,
      "pressure": 3.0
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "reading_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "123e4567-e89b-12d3-a456-426614174001"
  ],
  "errors": []
}
```

#### Get Latest Readings

```http
GET /api/v1/sensors/{equipment_id}/latest?limit=10
```

**Response (200 OK):**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "count": 5,
  "readings": [
    {
      "reading_id": "...",
      "temperature": 85.5,
      "vibration": 0.45,
      "pressure": 3.2,
      "timestamp": "2025-11-01T18:30:00Z"
    }
  ]
}
```

## 🔧 Configuration

All configuration via environment variables (see `.env.example`):

### Required Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
REDIS_URL=redis://host:port/db
```

### Optional Variables

```bash
# Service
PORT=8001
DEBUG=False
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Validation
MIN_TEMPERATURE=-50.0
MAX_TEMPERATURE=200.0
MIN_VIBRATION=0.0
MAX_VIBRATION=2.0
```

## 📊 Validation Rules

### Equipment ID Format
- Pattern: `TYPE-LOCATION-NNN`
- Examples: `RADAR-LOC-001`, `AIRCRAFT-BASE-042`
- Automatically converted to uppercase

### Sensor Ranges

| Sensor | Min | Max | Unit |
|--------|-----|-----|------|
| Temperature | -50.0 | 200.0 | °C |
| Vibration | 0.0 | 2.0 | mm/s |
| Pressure | 0.0 | 10.0 | bar |
| Humidity | 0.0 | 100.0 | % |
| Voltage | 0.0 | 500.0 | V |

### Business Rules

- All zeros (temp, vibration, pressure) → Sensor failure error
- High temp (>150°C) + high vibration (>1.5 mm/s) → Warning logged
- High temp (>100°C) + low pressure (<0.5 bar) → Warning logged

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py -v

# View coverage report
open htmlcov/index.html
```

## 🐳 Docker

### Build Image

```bash
docker build -t sensor-ingestion:latest .
```

### Run Container

```bash
docker run -p 8001:8001 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e REDIS_URL="redis://..." \
  sensor-ingestion:latest
```

## 📈 Monitoring

### Logs

Structured JSON logs to stdout:

```json
{
  "timestamp": "2025-11-01T18:30:00Z",
  "level": "INFO",
  "service": "sensor-ingestion-service",
  "message": "Sensor data stored",
  "reading_id": "123e4567...",
  "equipment_id": "RADAR-LOC-001"
}
```

### Metrics

Health check provides:
- Service status
- Database connectivity
- Redis connectivity
- Uptime in seconds

## 🔒 Security

- ✅ Non-root user in Docker
- ✅ No hardcoded credentials
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Input validation with Pydantic
- ✅ CORS configuration
- ✅ Request ID tracking

## 🚢 Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sensor-ingestion
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: sensor-ingestion
        image: sensor-ingestion:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
```

## 📚 Project Structure

```
services/sensor-ingestion/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app & endpoints
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── schemas.py           # SQLAlchemy models
│   ├── services.py          # Business logic
│   ├── database.py          # Database connection
│   ├── dependencies.py      # Dependency injection
│   ├── middleware.py        # Custom middleware
│   ├── exceptions.py        # Custom exceptions
│   └── logger.py            # Logging configuration
├── tests/
│   └── test_main.py         # Integration tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## 🔗 Integration

### Consuming from Redis Queue

ML Prediction Service consumes messages:

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)

while True:
    # Blocking pop from queue
    _, message = r.brpop('sensor_data_queue')
    data = json.loads(message)
    
    # Process sensor data
    reading_id = data['reading_id']
    equipment_id = data['equipment_id']
    # Run ML prediction...
```

## 🐛 Troubleshooting

### Database Connection Fails

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify connection string
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
```

### Redis Connection Fails

```bash
# Check Redis is running
redis-cli ping

# Verify connection string
REDIS_URL=redis://localhost:6379/0
```

### Import Errors

```bash
# Ensure you're in the service directory
cd services/sensor-ingestion

# Run from parent directory
python -m uvicorn app.main:app
```

## 📞 Support

For issues, questions, or contributions, please refer to the main project repository.

## 📄 License

Part of the DRDO Equipment Maintenance Prediction System.

---

**Service Status**: ✅ Production Ready  
**Last Updated**: 2025-11-02  
**Maintainer**: DRDO Summer Training Project
