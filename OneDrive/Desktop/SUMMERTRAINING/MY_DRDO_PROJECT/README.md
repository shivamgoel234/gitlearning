# DRDO Equipment Maintenance Prediction System

Production-ready microservices-based AI system for predictive maintenance of DRDO defense equipment.

## 🎯 System Architecture

**Architecture Type**: Microservices (4 independent services)  
**Programming Language**: Python 3.11+  
**Primary Frameworks**: FastAPI, Scikit-learn, SQLAlchemy, Streamlit  
**Infrastructure**: Docker, PostgreSQL, Redis, Kubernetes-ready  
**Design Patterns**: Domain-Driven Design, Dependency Injection, CQRS, Event-Driven

### Services Overview

| Service | Port | Purpose | Database |
|---------|------|---------|----------|
| **sensor-data-ingestion-service** | 8001 | Data collection & validation | PostgreSQL |
| **ml-prediction-service** | 8002 | ML inference & health scoring | PostgreSQL |
| **alert-maintenance-service** | 8003 | Alert generation & scheduling | PostgreSQL |
| **dashboard-service** | 8004 | Visualization & reporting | Read-only access |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd MY_DRDO_PROJECT
```

2. **Set up environment variables**
```bash
# Copy environment templates for each service
cp sensor-data-ingestion-service/.env.example sensor-data-ingestion-service/.env
cp ml-prediction-service/.env.example ml-prediction-service/.env
cp alert-maintenance-service/.env.example alert-maintenance-service/.env
cp dashboard-service/.env.example dashboard-service/.env

# Edit .env files with your configuration
```

3. **Start all services with Docker Compose**
```bash
docker-compose up -d
```

4. **Verify services are running**
```bash
# Check health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### Running Individual Services Locally

```bash
# Navigate to service directory
cd sensor-data-ingestion-service

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn app.main:app --reload --port 8001
```

## 📊 API Documentation

Once services are running, access Swagger UI documentation:

- Sensor Ingestion: http://localhost:8001/docs
- ML Prediction: http://localhost:8002/docs
- Alert Maintenance: http://localhost:8003/docs
- Dashboard: http://localhost:8004/docs

## 🏗️ Project Structure

```
MY_DRDO_PROJECT/
├── sensor-data-ingestion-service/     # Port 8001
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── database.py
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── ml-prediction-service/             # Port 8002
├── alert-maintenance-service/         # Port 8003
├── dashboard-service/                 # Port 8004
├── shared/                            # Shared utilities
│   ├── __init__.py
│   ├── validators.py
│   └── constants.py
├── scripts/                           # Deployment scripts
│   ├── init_db.py
│   └── seed_data.py
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 🧪 Testing

```bash
# Run tests for all services
docker-compose run sensor-ingestion pytest tests/ --cov=app

# Or test individual service
cd sensor-data-ingestion-service
pytest tests/ -v --cov=app --cov-report=html
```

## 🔧 Configuration

All services follow 12-factor app methodology with environment-based configuration.

### Required Environment Variables

Each service requires:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SERVICE_NAME` - Service identifier
- `PORT` - Service port number
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)

See individual service README.md files for complete configuration details.

## 📈 Monitoring

### Health Checks

All services implement:
- `/health` - Basic health check
- `/health/ready` - Readiness probe (database connectivity)
- `/metrics` - Prometheus metrics (optional)

### Logging

All services use structured JSON logging to stdout:
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "service": "sensor-ingestion",
  "message": "Sensor data received",
  "equipment_id": "RADAR-001"
}
```

## 🚢 Deployment

### Docker Compose (Development/Staging)

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Kubernetes (Production)

```bash
# Build images
docker build -t drdo/sensor-ingestion:latest sensor-data-ingestion-service/
docker build -t drdo/ml-prediction:latest ml-prediction-service/
docker build -t drdo/alert-maintenance:latest alert-maintenance-service/
docker build -t drdo/dashboard:latest dashboard-service/

# Apply Kubernetes manifests
kubectl apply -f k8s/
```

## 🔐 Security

- All services run as non-root users in Docker containers
- Secrets managed via environment variables (never committed)
- Database connections use connection pooling with SSL
- API endpoints protected with rate limiting
- Input validation using Pydantic models

## 📝 Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Make changes**: Follow coding standards in WARP.md
3. **Format code**: `black app/ tests/ && isort app/ tests/`
4. **Run linter**: `flake8 app/ tests/`
5. **Type check**: `mypy app/`
6. **Run tests**: `pytest tests/ --cov=app`
7. **Commit changes**: `git commit -m "feat: description"`
8. **Push and create PR**: `git push origin feature/your-feature`

## 🤝 Contributing

1. Follow 12-factor app principles
2. Maintain service independence
3. Use type hints on all functions
4. Write Google-style docstrings
5. Achieve minimum 70% test coverage
6. Use async/await for I/O operations
7. Log using structured JSON format

## 📚 Documentation

- [12-Factor App Methodology](https://12factor.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic V2](https://docs.pydantic.dev/latest/)

## 📧 Project Metadata

**Project Name**: DRDO Equipment Maintenance Prediction System  
**Tech Stack**: Python 3.11, FastAPI, PostgreSQL, Redis, Scikit-learn, Docker  
**Purpose**: DRDO summer training project on ML-powered predictive maintenance  
**Target**: 85%+ prediction accuracy, <200ms response time, 99.5% availability

## 📄 License

Proprietary - DRDO Internal Use Only

---

**Last Updated**: 2025-01-01  
**Version**: 1.0.0
