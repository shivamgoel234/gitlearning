# ML Prediction Service

**Port**: 8002  
**Domain**: Machine Learning Inference & Health Scoring  
**Technology Stack**: FastAPI, Scikit-learn, PostgreSQL, Redis, SQLAlchemy

---

## 📋 Overview

The ML Prediction Service is the core intelligence layer of the DRDO Equipment Maintenance Prediction System. It consumes sensor data events, performs real-time ML inference, calculates equipment health scores, and publishes prediction results.

### Key Responsibilities

- ✅ Subscribe to sensor data events from Redis pub/sub
- ✅ Load and manage trained ML models (Random Forest)
- ✅ Perform real-time failure probability predictions
- ✅ Calculate normalized equipment health scores (0-100)
- ✅ Classify severity levels (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Store predictions in PostgreSQL
- ✅ Publish prediction events to downstream services
- ✅ Provide prediction history and analytics endpoints

---

## 🏗️ Architecture

```
┌─────────────────────────┐
│  Sensor Ingestion       │
│  Service (Port 8001)    │
└────────┬────────────────┘
         │ Redis Pub/Sub
         │ (sensor_data_channel)
         ▼
┌──────────────────────────────────────┐
│  ML Prediction Service              │
│  (FastAPI on Port 8002)              │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Event Subscriber              │ │
│  │  - Redis listener              │ │
│  └──────────┬─────────────────────┘ │
│             │                        │
│  ┌──────────▼─────────────────────┐ │
│  │  ML Inference Engine           │ │
│  │  - Load model (.pkl)           │ │
│  │  - Feature preparation         │ │
│  │  - Predict failure probability │ │
│  │  - Calculate health score      │ │
│  └──────────┬─────────────────────┘ │
│             │                        │
│  ┌──────────▼──────┬──────────┐    │
│  │                 │           │    │
│  │  PostgreSQL     │  Redis    │    │
│  │  (Predictions)  │  (Events) │    │
│  └─────────────────┴───────────┘    │
└──────────────────────────────────────┘
         │
         │ Redis Pub/Sub
         │ (prediction_channel)
         ▼
┌─────────────────────┐
│  Alert & Maintenance│
│  Service (Port 8003)│
└─────────────────────┘
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
  "service": "ml-prediction",
  "model_loaded": true,
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### `GET /health/ready`
Readiness probe with model and database check.

**Response:**
```json
{
  "status": "ready",
  "service": "ml-prediction",
  "timestamp": "2025-01-01T12:00:00Z",
  "database": "connected",
  "redis": "connected",
  "model_loaded": true,
  "model_version": "1.0"
}
```

### Prediction Operations

#### `POST /api/v1/predictions/predict`
Perform manual prediction for equipment.

**Request Body:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "sensor_data": {
    "temperature": 95.5,
    "vibration": 0.85,
    "pressure": 4.2,
    "humidity": 72.0,
    "voltage": 215.0
  }
}
```

**Success Response (200 OK):**
```json
{
  "prediction_id": "pred-uuid-12345",
  "equipment_id": "RADAR-LOC-001",
  "timestamp": "2025-01-01T12:00:00Z",
  "failure_probability": 0.73,
  "health_score": 42.5,
  "severity": "HIGH",
  "days_until_failure": 15,
  "confidence": "high",
  "recommendations": [
    "Schedule maintenance inspection within 15 days",
    "Monitor vibration levels closely",
    "Check cooling system"
  ]
}
```

#### `GET /api/v1/predictions/{equipment_id}/latest?limit=10`
Retrieve latest predictions for specific equipment.

**Response:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "count": 10,
  "predictions": [
    {
      "prediction_id": "pred-uuid-1",
      "timestamp": "2025-01-01T12:00:00Z",
      "failure_probability": 0.73,
      "health_score": 42.5,
      "severity": "HIGH"
    }
  ]
}
```

#### `GET /api/v1/predictions/{equipment_id}/health-trend?days=7`
Get health score trend over time.

**Parameters:**
- `days` (query): Number of days to retrieve (default: 7, max: 90)

**Response:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "period_days": 7,
  "data_points": 168,
  "trend": "declining",
  "health_scores": [
    {"timestamp": "2025-01-01T00:00:00Z", "score": 75.2},
    {"timestamp": "2025-01-01T01:00:00Z", "score": 74.8}
  ],
  "average_score": 65.3,
  "min_score": 42.5,
  "max_score": 85.7
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | No | ml-prediction | Service identifier |
| `PORT` | No | 8002 | Service port |
| `DATABASE_URL` | **Yes** | - | PostgreSQL async connection string |
| `REDIS_URL` | **Yes** | - | Redis connection string |
| `MODEL_PATH` | **Yes** | - | Path to trained model file (.pkl) |
| `MODEL_VERSION` | No | 1.0 | Model version identifier |
| `LOG_LEVEL` | No | INFO | Logging level |
| `DEBUG` | No | False | Enable debug mode |
| `PREDICTION_CONFIDENCE_THRESHOLD` | No | 0.7 | Confidence threshold |
| `REDIS_SUBSCRIBE_CHANNEL` | No | sensor_data_channel | Input channel |
| `REDIS_PUBLISH_CHANNEL` | No | prediction_channel | Output channel |

### Example .env File

```bash
# Service Configuration
SERVICE_NAME=ml-prediction
PORT=8002
DEBUG=False

# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://drdo_user:drdo_password@localhost:5432/drdo_maintenance

# Redis (REQUIRED)
REDIS_URL=redis://localhost:6379/0

# ML Model (REQUIRED)
MODEL_PATH=models/failure_predictor_v1.pkl
MODEL_VERSION=1.0

# Logging
LOG_LEVEL=INFO

# Prediction Settings
PREDICTION_CONFIDENCE_THRESHOLD=0.7
REDIS_SUBSCRIBE_CHANNEL=sensor_data_channel
REDIS_PUBLISH_CHANNEL=prediction_channel

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
- Trained ML model file (`.pkl`)

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

3. **Train ML model (if needed):**
```powershell
# Run from project root
python scripts/train_model.py
# Model will be saved to models/failure_predictor_v1.pkl
```

4. **Configure environment:**
```powershell
cp .env.example .env
# Set MODEL_PATH to your trained model location
```

5. **Run service:**
```powershell
uvicorn app.main:app --reload --port 8002
```

6. **Access API documentation:**
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

---

## 🧪 Testing

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test
pytest tests/test_inference.py -v
```

**Test Coverage Target:** 70%+

---

## 🤖 Machine Learning Model

### Model Type
**Random Forest Classifier**

### Features (5 inputs)
1. `temperature` (°C)
2. `vibration` (mm/s)
3. `pressure` (bar)
4. `humidity` (%)
5. `voltage` (V)

### Target Variable
Binary classification: `failure` (0 = normal, 1 = failure imminent)

### Model Metadata (Example)
```json
{
  "model_type": "RandomForestClassifier",
  "version": "1.0",
  "accuracy": 0.87,
  "precision": 0.84,
  "recall": 0.89,
  "f1_score": 0.86,
  "training_samples": 50000,
  "test_samples": 12500,
  "features": ["temperature", "vibration", "pressure", "humidity", "voltage"],
  "random_seed": 42,
  "trained_at": "2025-01-01T10:00:00Z"
}
```

### Model Training
See `scripts/train_model.py` for training pipeline:
- Data preprocessing
- Feature engineering
- Train-test split (80/20)
- Cross-validation (5-fold)
- Model serialization with `joblib`

---

## 📊 Health Score Calculation

Equipment health scores are calculated as:

```
health_score = 100 × (1 - failure_probability)
```

### Health Score Interpretation

| Score Range | Status | Action Required |
|-------------|--------|-----------------|
| 90-100 | Excellent | Routine monitoring |
| 70-89 | Good | Continue monitoring |
| 50-69 | Fair | Schedule preventive maintenance |
| 30-49 | Poor | Maintenance required soon |
| 0-29 | Critical | Immediate action required |

---

## 🔴 Severity Classification

Severity is determined by failure probability:

| Severity | Probability Range | Days Until Failure | Action |
|----------|------------------|-------------------|--------|
| CRITICAL | > 80% | 7 days | Immediate intervention |
| HIGH | 60-80% | 15 days | Schedule urgent maintenance |
| MEDIUM | 40-60% | 30 days | Plan maintenance |
| LOW | < 40% | 60+ days | Monitor regularly |

---

## 📦 Database Schema

### Table: `predictions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | Prediction identifier (UUID) |
| `equipment_id` | VARCHAR(50) | NOT NULL, INDEX | Equipment identifier |
| `timestamp` | TIMESTAMP | NOT NULL, INDEX | Prediction timestamp (UTC) |
| `failure_probability` | FLOAT | NOT NULL | Probability (0.0-1.0) |
| `health_score` | FLOAT | NOT NULL | Health score (0-100) |
| `severity` | VARCHAR(20) | NOT NULL | CRITICAL/HIGH/MEDIUM/LOW |
| `days_until_failure` | INTEGER | NOT NULL | Estimated days |
| `confidence` | VARCHAR(20) | NOT NULL | high/medium/low |
| `model_version` | VARCHAR(20) | NOT NULL | Model version used |
| `sensor_data` | JSONB | NULLABLE | Input sensor readings |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |

### Indexes
- Primary key on `id`
- Index on `equipment_id`
- Index on `timestamp`
- Composite index on `(equipment_id, timestamp)`
- Index on `severity` for alert filtering

---

## 📡 Event Processing

### Subscribed Events

**Channel:** `sensor_data_channel`

**Event Format:**
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

### Published Events

**Channel:** `prediction_channel`

**Event Format:**
```json
{
  "event_type": "prediction_completed",
  "prediction_id": "pred-uuid-12345",
  "equipment_id": "RADAR-LOC-001",
  "timestamp": "2025-01-01T12:00:00Z",
  "failure_probability": 0.73,
  "health_score": 42.5,
  "severity": "HIGH",
  "days_until_failure": 15
}
```

---

## ⚡ Performance

### Benchmarks

- **Inference Latency**: <50ms per prediction
- **Throughput**: 500+ predictions/second
- **Model Load Time**: <2 seconds on startup
- **Memory Usage**: ~200MB (includes loaded model)

### Optimization

1. **Model Caching**: Model loaded once at startup
2. **Async I/O**: All database and Redis operations async
3. **Batch Processing**: Supports batch prediction requests
4. **Connection Pooling**: Database connections reused

---

## 🐛 Troubleshooting

### Model Not Loading
```
Error: Model file not found
```
**Solution:**
- Verify MODEL_PATH in .env points to valid .pkl file
- Train model: `python scripts/train_model.py`
- Check file permissions

### Prediction Errors
```
Error: Feature mismatch
```
**Solution:**
- Ensure all 5 sensor values provided
- Check sensor value ranges match training data
- Verify model version compatibility

---

## 📝 Logging

Structured JSON logs:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "service": "ml-prediction",
  "message": "Prediction completed",
  "equipment_id": "RADAR-LOC-001",
  "failure_probability": 0.73,
  "severity": "HIGH",
  "inference_time_ms": 42.5
}
```

---

## 🔗 Related Services

- **Sensor Ingestion Service** (Port 8001): Provides sensor data
- **Alert Maintenance Service** (Port 8003): Consumes predictions
- **Dashboard Service** (Port 8004): Visualizes predictions

---

**Service Version:** 1.0.0  
**Last Updated:** 2025-01-02  
**Maintainer:** DRDO Development Team
