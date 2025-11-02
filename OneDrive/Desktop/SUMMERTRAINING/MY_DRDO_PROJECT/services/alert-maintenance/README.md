# Alert & Maintenance Service

Microservice for managing equipment failure alerts and maintenance task scheduling for the DRDO Equipment Maintenance Prediction System.

## 🎯 Overview

This service handles:
- **Equipment Failure Alerts**: Creating, tracking, and managing alerts from ML predictions
- **Maintenance Task Management**: Scheduling, assigning, and tracking maintenance tasks
- **Database Operations**: Full CRUD operations with PostgreSQL using SQLAlchemy async
- **Email Notifications**: Sending alerts to maintenance teams (via Celery)
- **Task Automation**: Automatic maintenance task creation from critical alerts

## 📦 Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL with asyncpg driver
- **ORM**: SQLAlchemy 2.0 (async)
- **Cache/Queue**: Redis + Celery for async tasks
- **Validation**: Pydantic v2
- **Testing**: pytest with async support

## 🗄️ Database Schema

### Tables

1. **alerts** - Equipment failure alerts
   - id, equipment_id, severity, failure_probability
   - status (ACTIVE, ACKNOWLEDGED, RESOLVED)
   - timestamps for creation, acknowledgment, resolution

2. **maintenance_tasks** - Scheduled maintenance tasks
   - id, equipment_id, task_type, priority
   - status (SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, OVERDUE)
   - scheduling, cost estimates, assignments

3. **maintenance_history** - Audit trail of all maintenance activities

## 🚀 Getting Started

### Prerequisites

```bash
# PostgreSQL 14+
# Redis 6+
# Python 3.11+
```

### Installation

```bash
# Navigate to service directory
cd services/alert-maintenance

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# IMPORTANT: Update DATABASE_URL, REDIS_URL, SMTP settings
```

### Database Setup

```bash
# Method 1: Auto-create tables on startup
# Tables are created automatically when the service starts

# Method 2: Use Alembic migrations (recommended for production)
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Running the Service

```bash
# Development mode
uvicorn app.main:app --reload --port 8003

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8003 --workers 4
```

### Docker Deployment

```bash
# Build image
docker build -t alert-maintenance-service:latest .

# Run container
docker run -d \
  --name alert-maintenance \
  -p 8003:8003 \
  --env-file .env \
  alert-maintenance-service:latest
```

## 📡 API Endpoints

### Health Check
```
GET  /health              - Service health check
GET  /health/ready        - Readiness probe
GET  /health/db           - Database health check
```

### Alerts
```
POST   /api/v1/alerts                    - Create new alert
GET    /api/v1/alerts                    - List all alerts
GET    /api/v1/alerts/{id}               - Get alert by ID
PATCH  /api/v1/alerts/{id}               - Update alert
DELETE /api/v1/alerts/{id}               - Delete alert
GET    /api/v1/alerts/equipment/{eq_id}  - Get alerts by equipment
POST   /api/v1/alerts/{id}/acknowledge   - Acknowledge alert
POST   /api/v1/alerts/{id}/resolve       - Resolve alert
GET    /api/v1/alerts/statistics         - Alert statistics
```

### Maintenance Tasks
```
POST   /api/v1/tasks                     - Create new task
GET    /api/v1/tasks                     - List all tasks
GET    /api/v1/tasks/{id}                - Get task by ID
PATCH  /api/v1/tasks/{id}                - Update task
DELETE /api/v1/tasks/{id}                - Delete task
GET    /api/v1/tasks/equipment/{eq_id}   - Get tasks by equipment
POST   /api/v1/tasks/{id}/assign         - Assign task
POST   /api/v1/tasks/{id}/complete       - Complete task
GET    /api/v1/tasks/statistics          - Task statistics
```

## 📝 Example Usage

### Create Alert

```bash
curl -X POST "http://localhost:8003/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-LOC-001",
    "severity": "CRITICAL",
    "failure_probability": 0.82,
    "days_until_failure": 7,
    "recommended_action": "Schedule immediate maintenance",
    "health_score": 18.0,
    "confidence": "high"
  }'
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "equipment_id": "RADAR-LOC-001",
  "severity": "CRITICAL",
  "failure_probability": 0.82,
  "days_until_failure": 7,
  "recommended_action": "Schedule immediate maintenance",
  "status": "ACTIVE",
  "created_at": "2025-11-02T10:30:00Z",
  "health_score": 18.0,
  "confidence": "high"
}
```

### Create Maintenance Task

```bash
curl -X POST "http://localhost:8003/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-LOC-001",
    "task_type": "PREVENTIVE",
    "priority": "CRITICAL",
    "scheduled_date": "2025-11-09T08:00:00Z",
    "title": "Emergency cooling system maintenance",
    "estimated_duration_hours": 4,
    "cost_estimate": 5000.0,
    "assigned_to": "maintenance-team-a@drdo.gov.in",
    "alert_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

## 🔧 Configuration Options

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string (asyncpg)
- `DB_POOL_SIZE`: Connection pool size (default: 10)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 20)
- `DB_POOL_RECYCLE`: Recycle connections after N seconds (default: 3600)

### Alert Configuration
- `ALERT_CRITICAL_THRESHOLD`: Threshold for CRITICAL alerts (default: 0.8)
- `ALERT_HIGH_THRESHOLD`: Threshold for HIGH alerts (default: 0.6)
- `ALERT_MEDIUM_THRESHOLD`: Threshold for MEDIUM alerts (default: 0.4)
- `AUTO_CREATE_TASKS`: Auto-create tasks from alerts (default: True)

### Email Configuration
- `EMAIL_ENABLED`: Enable email notifications (default: True)
- `EMAIL_FROM`: Sender email address
- `EMAIL_TO`: Primary recipient email
- `SMTP_HOST`: SMTP server hostname
- `SMTP_PORT`: SMTP server port (default: 587)

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_alerts.py -v

# Run integration tests only
pytest tests/ -m integration -v
```

## 📊 Database Indexes

The service uses composite indexes for optimal query performance:

- `idx_equipment_status` - Alert/Task queries by equipment and status
- `idx_severity_created` - Alert queries by severity and creation date
- `idx_priority_scheduled` - Task queries by priority and schedule
- `idx_assigned_status` - Task queries by assignment and status

## 🔐 Security Considerations

1. **Database Credentials**: Store in environment variables, never commit
2. **Email Credentials**: Use app-specific passwords for Gmail
3. **API Keys**: Implement authentication for production (JWT/OAuth2)
4. **Input Validation**: All inputs validated via Pydantic models
5. **SQL Injection**: Protected by SQLAlchemy parameterized queries

## 🚨 Error Handling

The service implements comprehensive error handling:
- Database connection errors
- Validation errors (422)
- Not found errors (404)
- Internal server errors (500)
- Structured error responses with timestamps

## 📈 Monitoring & Logging

- Structured JSON logging
- Health check endpoints for Kubernetes
- Database connection pool statistics
- Request/response logging
- Error tracking with stack traces

## 🔄 Integration with Other Services

### ML Prediction Service
- Receives prediction results
- Creates alerts for high-risk equipment

### Sensor Ingestion Service
- Queries equipment history
- Validates equipment IDs

### Dashboard Service
- Provides data for visualization
- Real-time alert updates

## 📚 API Documentation

Once the service is running, access:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc
- **OpenAPI Schema**: http://localhost:8003/api/v1/openapi.json

## 🛠️ Development

### Code Style
- Black for formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint
flake8 app/ tests/

# Type check
mypy app/
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📦 Project Structure

```
services/alert-maintenance/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connection
│   ├── schemas.py         # SQLAlchemy models
│   ├── models.py          # Pydantic models
│   ├── main.py            # FastAPI application
│   ├── services.py        # Business logic
│   └── utils.py           # Utility functions
├── tests/
│   ├── test_alerts.py
│   ├── test_tasks.py
│   └── test_database.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🤝 Contributing

1. Follow the coding standards defined in project WARP.md
2. Write tests for new features
3. Update API documentation
4. Use conventional commits

## 📄 License

DRDO Internal Use Only

## 👥 Contact

For questions or support, contact the DRDO IT team.

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-02  
**Service Port**: 8003
