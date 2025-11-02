# ML Prediction Service

**Port**: 8002  
**Purpose**: ML inference and health scoring for DRDO equipment

## Overview

This microservice handles machine learning inference for equipment failure prediction. It loads a trained Random Forest model, processes sensor data, and generates failure probability predictions with severity levels and health scores.

## Features

- ✅ ML-based failure prediction
- ✅ Equipment health score calculation
- ✅ Severity classification (CRITICAL/HIGH/MEDIUM/LOW)
- ✅ Async model inference
- ✅ Prediction result storage in PostgreSQL
- ✅ Redis pub/sub for event-driven architecture
- ✅ Structured JSON logging
- ✅ Health check endpoints with model status
- ✅ OpenAPI/Swagger documentation

## API Endpoints

### Health Checks

#### `GET /health`
Basic health check with model loading status.

**Response**:
```json
{
  "status": "healthy",
  "service": "ml-prediction",
  "timestamp": "2025-01-01T12:00:00Z",
  "model_loaded": true
}
```

#### `GET /health/ready`
Readiness probe with database, Redis, and model status.

### Predictions

#### `POST /api/v1/predict/failure`
Predict equipment failure probability.

**Request Body**:
```json
{
  "equipment_id": "RADAR-LOC-001",
  "temperature": 85.5,
  "vibration": 0.45,
  "pressure": 3.2,
  "humidity": 65.0,
  "voltage": 220.0
}
```

**Response** (200 OK):
```json
{
  "prediction_id": "pred-123-456",
  "equipment_id": "RADAR-LOC-001",
  "failure_probability": 0.750,
  "severity": "HIGH",
  "health_score": 35.5,
  "days_until_failure": 15,
  "confidence": "high",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

#### `GET /api/v1/health-score/{equipment_id}`
Get current health score for equipment.

**Response**:
```json
{
  "equipment_id": "RADAR-LOC-001",
  "health_score": 35.5,
  "status": "POOR",
  "last_prediction": "2025-01-01T12:00:00Z",
  "trend": "stable"
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVICE_NAME` | No | ml-prediction | Service identifier |
| `PORT` | No | 8002 | Service port |
| `DATABASE_URL` | **Yes** | - | PostgreSQL connection string |
| `REDIS_URL` | **Yes** | - | Redis connection string |
| `MODEL_PATH` | No | models/failure_predictor_v1.pkl | ML model file path |
| `MODEL_METADATA_PATH` | No | models/model_metadata_v1.json | Model metadata path |
| `CRITICAL_THRESHOLD` | No | 0.8 | Critical severity threshold |
| `HIGH_THRESHOLD` | No | 0.6 | High severity threshold |
| `MEDIUM_THRESHOLD` | No | 0.4 | Medium severity threshold |

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Trained ML model (or use mock model for development)

### Setup

1. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
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
uvicorn app.main:app --reload --port 8002
```

5. **Access API documentation**
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## ML Model

### Model Training

The service expects a trained scikit-learn Random Forest model. To train:

```python
from sklearn.ensemble import RandomForestClassifier
import joblib

# Train model (see training scripts)
model = RandomForestClassifier(n_estimators=100, max_depth=10)
model.fit(X_train, y_train)

# Save model
joblib.dump(model, 'models/failure_predictor_v1.pkl')
```

### Model Metadata

Create `models/model_metadata_v1.json`:
```json
{
  "model_type": "RandomForestClassifier",
  "version": "1.0",
  "accuracy": 0.87,
  "features": ["temperature", "vibration", "pressure", "humidity", "voltage"],
  "training_date": "2025-01-01"
}
```

### Mock Model

For development without a trained model, the service uses a mock model that generates predictions based on sensor reading heuristics.

## Severity Levels

| Severity | Failure Probability | Days Until Failure |
|----------|--------------------|--------------------|
| CRITICAL | ≥ 80% | 7 days |
| HIGH | 60-79% | 15 days |
| MEDIUM | 40-59% | 30 days |
| LOW | < 40% | 60 days |

## Health Score

Health score is calculated on a scale of 0-100:
- **90-100**: Excellent condition
- **70-89**: Good condition
- **50-69**: Fair condition (monitoring recommended)
- **30-49**: Poor condition (maintenance needed)
- **0-29**: Critical condition (immediate action required)

## Event Publishing

When predictions are generated, events are published to Redis:

**Channel**: `prediction_channel`

**Event Format**:
```json
{
  "event_type": "prediction_generated",
  "prediction_id": "pred-123",
  "equipment_id": "RADAR-LOC-001",
  "failure_probability": 0.75,
  "severity": "HIGH",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_main.py::TestPredictionEndpoints -v
```

## Docker

### Build Image
```bash
docker build -t drdo/ml-prediction:latest .
```

### Run Container
```bash
docker run -p 8002:8002 \
  -v $(pwd)/models:/app/models \
  --env-file .env \
  drdo/ml-prediction:latest
```

## Performance

- **Target Response Time**: <200ms for prediction
- **Model Inference**: <50ms on average
- **Throughput**: 500+ predictions per second
- **Concurrent Requests**: Handles 100+ concurrent requests

## Troubleshooting

### Model Not Loading
- Verify model file exists at `MODEL_PATH`
- Check file permissions
- Ensure scikit-learn version compatibility

### Low Prediction Accuracy
- Retrain model with more data
- Feature engineering improvements
- Hyperparameter tuning

### High Memory Usage
- Reduce model complexity
- Use model quantization
- Limit concurrent workers

---

**Service Version**: 1.0.0  
**Last Updated**: 2025-01-01
