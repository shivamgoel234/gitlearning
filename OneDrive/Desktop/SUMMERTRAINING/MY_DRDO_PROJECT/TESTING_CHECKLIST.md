# DRDO Equipment Maintenance System - Testing Checklist

## 📋 Overview

This document provides a comprehensive testing checklist to ensure production readiness of the DRDO Equipment Maintenance Prediction System.

**Target Coverage**: 70%+ code coverage  
**Testing Framework**: pytest  
**Last Updated**: 2025-11-02

---

## ✅ Pre-Deployment Testing Checklist

### 1. Unit Tests (Minimum 70% Coverage)

#### Sensor Ingestion Service
- [ ] `test_sensor_validation()` - Validate sensor data constraints
- [ ] `test_equipment_id_format()` - Validate equipment ID format
- [ ] `test_temperature_range()` - Temperature within -50 to 200°C
- [ ] `test_vibration_range()` - Vibration within 0 to 2.0 mm/s
- [ ] `test_pressure_range()` - Pressure within 0 to 10.0 bar
- [ ] `test_database_insert()` - Database insertion works
- [ ] `test_redis_publish()` - Redis event publishing works
- [ ] `test_duplicate_reading()` - Handle duplicate readings
- [ ] `test_invalid_json()` - Reject malformed JSON
- [ ] `test_missing_required_fields()` - Reject incomplete data

**Command**: 
```bash
pytest services/sensor-ingestion/tests/ --cov=app --cov-report=html
```

#### ML Prediction Service
- [ ] `test_model_loading()` - ML model loads successfully
- [ ] `test_prediction_accuracy()` - Predictions within expected range
- [ ] `test_severity_classification()` - Correct severity assignment
- [ ] `test_health_score_calculation()` - Health score 0-100 range
- [ ] `test_confidence_scoring()` - Confidence levels accurate
- [ ] `test_invalid_sensor_data()` - Handle invalid input gracefully
- [ ] `test_model_version()` - Model version tracking works
- [ ] `test_feature_scaling()` - Feature scaling applied correctly
- [ ] `test_prediction_time()` - Response time < 500ms
- [ ] `test_concurrent_predictions()` - Handle multiple requests

**Command**:
```bash
pytest services/ml-prediction/tests/ --cov=app --cov-report=html
```

#### Alert & Maintenance Service
- [ ] `test_alert_generation()` - Alerts created for HIGH/CRITICAL
- [ ] `test_no_alert_for_low_severity()` - No alerts for LOW/MEDIUM
- [ ] `test_ml_service_integration()` - ML service calls work
- [ ] `test_celery_task_queuing()` - Email tasks queued correctly
- [ ] `test_maintenance_scheduling()` - Tasks scheduled properly
- [ ] `test_alert_lifecycle()` - Active → Acknowledged → Resolved
- [ ] `test_database_transactions()` - ACID properties maintained
- [ ] `test_ml_service_timeout()` - Handle ML service timeouts
- [ ] `test_duplicate_alerts()` - Prevent duplicate alerts
- [ ] `test_alert_filtering()` - Severity filtering works

**Command**:
```bash
pytest services/alert-maintenance/tests/ --cov=app --cov-report=html
```

#### Dashboard Service
- [ ] `test_data_fetching()` - API client fetches data
- [ ] `test_api_timeout_handling()` - Handle service timeouts
- [ ] `test_empty_data_handling()` - Display gracefully with no data
- [ ] `test_cache_expiration()` - Cache TTL works correctly
- [ ] `test_chart_rendering()` - Charts render without errors
- [ ] `test_health_check()` - Health check endpoints work
- [ ] `test_service_reconnection()` - Reconnect after failure
- [ ] `test_data_validation()` - Validate API responses
- [ ] `test_error_messages()` - User-friendly error messages
- [ ] `test_refresh_functionality()` - Manual refresh works

**Command**:
```bash
pytest services/dashboard/tests/ --cov=app --cov-report=html
```

---

### 2. Integration Tests (All Services Communicate)

- [ ] **End-to-End Sensor to Alert Flow**
  ```bash
  # Test complete workflow: Ingest → ML → Alert → Email
  pytest tests/integration/test_e2e_workflow.py -v
  ```

- [ ] **Database Integration**
  - [ ] PostgreSQL connection from all services
  - [ ] Data persistence across restarts
  - [ ] Transaction rollback on errors
  - [ ] Connection pool management

- [ ] **Redis Integration**
  - [ ] Redis connection from services
  - [ ] Message queue functionality
  - [ ] Cache operations
  - [ ] Pub/sub messaging

- [ ] **Inter-Service Communication**
  - [ ] Alert service calls ML service successfully
  - [ ] Dashboard calls all services successfully
  - [ ] HTTP timeouts handled gracefully
  - [ ] Retry logic works

- [ ] **Celery Worker Integration**
  - [ ] Tasks queued successfully
  - [ ] Tasks executed asynchronously
  - [ ] Failed tasks retry correctly
  - [ ] Task results stored

**Command**:
```bash
pytest tests/integration_tests.py -v --tb=short
```

---

### 3. Load Tests (Handle 1000 req/sec)

- [ ] **Sensor Ingestion Load Test**
  - [ ] 100 requests/sec sustained for 5 minutes
  - [ ] 1000 requests/sec burst for 30 seconds
  - [ ] Response time < 200ms at p95
  - [ ] No data loss under load
  - [ ] Graceful degradation

- [ ] **ML Prediction Load Test**
  - [ ] 50 requests/sec sustained
  - [ ] Prediction time < 500ms
  - [ ] Model concurrency handling
  - [ ] Memory stable under load

- [ ] **Alert Service Load Test**
  - [ ] Handle 100 alerts/sec
  - [ ] Database write performance
  - [ ] Celery queue not overwhelmed

- [ ] **Dashboard Load Test**
  - [ ] 500 concurrent users
  - [ ] Page load < 3 seconds
  - [ ] Cache hit rate > 80%

**Command**:
```bash
pytest tests/load_tests.py -v --durations=10
```

**Manual Load Testing** (using locust):
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8001
```

---

### 4. Security Tests (SQL Injection, XSS)

- [ ] **SQL Injection Prevention**
  - [ ] Parameterized queries only
  - [ ] No string concatenation in SQL
  - [ ] ORM protection verified
  - [ ] Input sanitization

- [ ] **XSS Prevention**
  - [ ] Output encoding
  - [ ] Content Security Policy headers
  - [ ] User input sanitization

- [ ] **Authentication & Authorization** (if implemented)
  - [ ] JWT token validation
  - [ ] Expired token rejection
  - [ ] Authorization checks

- [ ] **Container Security**
  - [ ] Running as non-root user
  - [ ] No secrets in environment
  - [ ] Minimal base images
  - [ ] No unnecessary ports exposed

- [ ] **API Security**
  - [ ] Rate limiting works
  - [ ] CORS configured correctly
  - [ ] HTTPS enforced (production)

**Command**:
```bash
pytest tests/security_tests.py -v
```

**Manual Security Scan**:
```bash
# Scan Docker images for vulnerabilities
docker scan drdo-sensor-ingestion:latest
docker scan drdo-ml-prediction:latest
docker scan drdo-alert-maintenance:latest
docker scan drdo-dashboard:latest
```

---

### 5. Database Tests (Backup/Restore)

- [ ] **Backup Procedures**
  - [ ] Manual backup creates valid dump
  - [ ] Automated backup scheduled
  - [ ] Backup file integrity verified
  - [ ] Backup retention policy

- [ ] **Restore Procedures**
  - [ ] Restore from backup successful
  - [ ] Data integrity after restore
  - [ ] Service reconnects after restore
  - [ ] No data loss

- [ ] **Migration Tests**
  - [ ] Schema migrations apply cleanly
  - [ ] Rollback migrations work
  - [ ] No data corruption

**Commands**:
```bash
# Backup test
make db-backup

# Restore test
docker-compose exec -T postgres psql -U drdo -d equipment_maintenance < backup.sql

# Verify data
docker-compose exec postgres psql -U drdo -d equipment_maintenance -c "SELECT COUNT(*) FROM sensor_data;"
```

---

### 6. API Response Tests (All Endpoints)

- [ ] **HTTP Status Codes**
  - [ ] 200 OK for successful GET
  - [ ] 201 Created for successful POST
  - [ ] 400 Bad Request for invalid data
  - [ ] 404 Not Found for missing resources
  - [ ] 422 Validation Error for schema violations
  - [ ] 500 Internal Server Error handled gracefully
  - [ ] 503 Service Unavailable when down

- [ ] **Response Schemas**
  - [ ] All responses match OpenAPI spec
  - [ ] Required fields present
  - [ ] Data types correct
  - [ ] Timestamps in ISO 8601 format

- [ ] **Response Times**
  - [ ] Health checks < 100ms
  - [ ] Sensor ingestion < 200ms
  - [ ] ML prediction < 500ms
  - [ ] Alert generation < 1s
  - [ ] Dashboard load < 3s

**Command**:
```bash
pytest tests/api_response_tests.py -v --tb=line
```

---

### 7. Error Handling Tests (Graceful Failures)

- [ ] **Service Failures**
  - [ ] Database down: Services return 503
  - [ ] Redis down: Graceful degradation
  - [ ] ML service down: Alert service handles timeout
  - [ ] Network errors: Retry with exponential backoff

- [ ] **Data Errors**
  - [ ] Invalid JSON: 400 Bad Request
  - [ ] Missing fields: 422 Validation Error
  - [ ] Out of range values: 422 with details
  - [ ] Malformed equipment ID: Rejected

- [ ] **Resource Exhaustion**
  - [ ] Database connection pool full: Queuing
  - [ ] Memory limit reached: Graceful shutdown
  - [ ] Disk full: Logging stops, service continues
  - [ ] CPU throttling: Performance degradation

- [ ] **Logging & Monitoring**
  - [ ] All errors logged with stack trace
  - [ ] Error rates tracked
  - [ ] Alerts on critical errors
  - [ ] Health checks report issues

**Command**:
```bash
pytest tests/error_handling_tests.py -v --tb=short
```

---

### 8. Health Check Tests (All Services)

- [ ] **Individual Service Health**
  - [ ] `GET /health` returns 200 OK
  - [ ] Response includes service name
  - [ ] Response includes version
  - [ ] Response includes timestamp
  - [ ] Database connection status included

- [ ] **Dependency Checks**
  - [ ] Sensor service checks PostgreSQL & Redis
  - [ ] ML service checks model loading
  - [ ] Alert service checks ML service availability
  - [ ] Dashboard checks all downstream services

- [ ] **Docker Health Checks**
  - [ ] Container marked healthy after startup
  - [ ] Unhealthy containers restart automatically
  - [ ] Health check interval appropriate (30s)
  - [ ] Timeout not too aggressive (10s)

**Commands**:
```bash
# Test all health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/_stcore/health

# Docker health status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Health}}"
```

---

### 9. Docker Tests (Image Builds, Runs)

- [ ] **Image Building**
  - [ ] All 4 services build successfully
  - [ ] Multi-stage builds work
  - [ ] No build errors or warnings
  - [ ] Image sizes reasonable (<500MB each)
  - [ ] BuildKit optimizations applied

- [ ] **Image Security**
  - [ ] Running as non-root user (appuser:1000)
  - [ ] No secrets in layers
  - [ ] Minimal base images (python:3.11-slim)
  - [ ] Security scan passes

- [ ] **Container Runtime**
  - [ ] All containers start successfully
  - [ ] Services accessible on correct ports
  - [ ] Resource limits enforced
  - [ ] Health checks pass
  - [ ] Logging works

- [ ] **Networking**
  - [ ] Services communicate on drdo_network
  - [ ] DNS resolution works (service names)
  - [ ] Port bindings correct
  - [ ] No unexpected external access

- [ ] **Volumes**
  - [ ] PostgreSQL data persists
  - [ ] Redis data persists (AOF)
  - [ ] ML models mounted read-only
  - [ ] Volume permissions correct

**Commands**:
```bash
# Build test
.\scripts\docker-build.ps1

# Run test
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs --tail=50

# Security scan
docker scan --accept-license drdo-sensor-ingestion:latest

# Resource usage
docker stats --no-stream
```

---

### 10. Documentation Tests (All Examples Work)

- [ ] **README Examples**
  - [ ] Quick start works
  - [ ] All curl commands execute
  - [ ] Make commands work
  - [ ] PowerShell scripts work

- [ ] **API Documentation**
  - [ ] All endpoints documented
  - [ ] Request examples valid
  - [ ] Response examples match reality
  - [ ] Error examples accurate

- [ ] **Code Examples**
  - [ ] Python examples run without errors
  - [ ] Dependencies all listed
  - [ ] Configuration examples valid

- [ ] **Deployment Guide**
  - [ ] Docker Compose steps work
  - [ ] Environment variables documented
  - [ ] Troubleshooting steps accurate

**Manual Verification**:
```bash
# Test README Quick Start
git clone <repo>
cd equipment-maintenance
docker-compose build
docker-compose up -d
curl http://localhost:8001/health
```

---

## 📊 Coverage Reports

### Generate Coverage Report

```bash
# All services
pytest services/*/tests/ --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

### Minimum Coverage Requirements

| Service | Minimum Coverage | Current Status |
|---------|------------------|----------------|
| Sensor Ingestion | 70% | ⬜ Pending |
| ML Prediction | 70% | ⬜ Pending |
| Alert & Maintenance | 70% | ⬜ Pending |
| Dashboard | 60% | ⬜ Pending |
| **Overall** | **70%** | **⬜ Pending** |

---

## 🚀 Automated Testing

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build images
        run: docker-compose build
      - name: Run tests
        run: docker-compose run sensor-ingestion pytest tests/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## ✅ Final Production Checklist

Before deploying to production:

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Load tests meet requirements
- [ ] Security scan passes
- [ ] Database backup/restore tested
- [ ] All API endpoints tested
- [ ] Error handling verified
- [ ] Health checks working
- [ ] Docker images built and scanned
- [ ] Documentation verified
- [ ] 70%+ code coverage achieved
- [ ] Performance benchmarks met
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Secrets management configured
- [ ] Environment variables documented
- [ ] Rollback procedure documented
- [ ] Team trained on deployment

---

## 📞 Support

For testing questions:

1. Review this checklist
2. Check test logs: `pytest -v --tb=short`
3. Review coverage reports
4. Contact QA team

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-11-02  
**Status**: ✅ Ready for Testing
