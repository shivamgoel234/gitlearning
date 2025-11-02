# DRDO Equipment Maintenance Prediction System - Deployment Guide

**Version:** 1.0  
**Last Updated:** 2025-01-02  
**Author:** DRDO DevOps Team

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Database Setup](#database-setup)
7. [Environment Configuration](#environment-configuration)
8. [Service Startup Order](#service-startup-order)
9. [Health Checks & Monitoring](#health-checks--monitoring)
10. [Backup & Recovery](#backup--recovery)
11. [Scaling Strategies](#scaling-strategies)
12. [Troubleshooting](#troubleshooting)
13. [Production Checklist](#production-checklist)

---

## Overview

This document provides comprehensive deployment instructions for the DRDO Equipment Maintenance Prediction System across different environments:

- **Local Development**: Windows/Mac/Linux development machines
- **Staging**: Docker Compose on cloud VM
- **Production**: Kubernetes cluster on AWS/GCP/Azure

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Application runtime |
| PostgreSQL | 15+ | Primary database |
| Redis | 7+ | Message broker & caching |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Local orchestration |
| Kubernetes | 1.28+ | Production orchestration |
| Git | 2.40+ | Version control |

### Hardware Requirements

**Development:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB

**Production (per node):**
- CPU: 8 cores
- RAM: 32 GB
- Disk: 100 GB SSD

---

## Local Development Setup

### 1. Clone Repository

```powershell
# Clone the project
git clone https://github.com/drdo/equipment-maintenance.git
cd equipment-maintenance
```

### 2. Install Python Dependencies

```powershell
# Create virtual environment for each service
cd sensor-data-ingestion-service
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Repeat for other services
```

### 3. Install PostgreSQL

**Option A: Docker (Recommended for Development)**

```powershell
docker run --name drdo-postgres \
  -e POSTGRES_USER=drdo_user \
  -e POSTGRES_PASSWORD=drdo_password \
  -e POSTGRES_DB=drdo_maintenance \
  -p 5432:5432 \
  -d postgres:15-alpine
```

**Option B: Native Installation**

Download from: https://www.postgresql.org/download/

```sql
-- Create database and user
CREATE DATABASE drdo_maintenance;
CREATE USER drdo_user WITH PASSWORD 'drdo_password';
GRANT ALL PRIVILEGES ON DATABASE drdo_maintenance TO drdo_user;
```

### 4. Install Redis

**Docker (Recommended):**

```powershell
docker run --name drdo-redis \
  -p 6379:6379 \
  -d redis:7-alpine
```

**Native Installation:**

Download from: https://redis.io/download

### 5. Configure Environment Variables

```powershell
# Create .env file for each service
cd sensor-data-ingestion-service
cp .env.example .env

# Edit .env with your configuration
notepad .env  # Windows
nano .env  # Linux/Mac
```

**Example .env:**

```bash
SERVICE_NAME=sensor-ingestion
PORT=8001
DATABASE_URL=postgresql+asyncpg://drdo_user:drdo_password@localhost:5432/drdo_maintenance
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
DEBUG=True
```

### 6. Initialize Database

```powershell
# Tables are created automatically on first service startup
# OR run migrations manually:
cd sensor-data-ingestion-service
python -m app.database.init_db
```

### 7. Train ML Model

```powershell
# Run training script from project root
cd <project_root>
python scripts/train_model.py

# Model saved to: models/failure_predictor_v1.pkl
```

### 8. Start Services

**Terminal 1 - Sensor Ingestion:**
```powershell
cd sensor-data-ingestion-service
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001
```

**Terminal 2 - ML Prediction:**
```powershell
cd ml-prediction-service
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8002
```

**Terminal 3 - Alert & Maintenance:**
```powershell
cd alert-maintenance-service
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8003
```

**Terminal 4 - Celery Worker:**
```powershell
cd alert-maintenance-service
.\start_celery_worker.ps1
```

**Terminal 5 - Celery Beat:**
```powershell
cd alert-maintenance-service
.\start_celery_beat.ps1
```

**Terminal 6 - Dashboard:**
```powershell
cd dashboard-service
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8004
```

### 9. Verify Installation

```powershell
# Check service health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# Access API documentation
# Open browser: http://localhost:8001/docs
```

---

## Docker Deployment

### 1. Build Docker Images

**Build all services:**

```bash
# From project root
cd sensor-data-ingestion-service
docker build -t drdo/sensor-ingestion:latest .

cd ../ml-prediction-service
docker build -t drdo/ml-prediction:latest .

cd ../alert-maintenance-service
docker build -t drdo/alert-maintenance:latest .

cd ../dashboard-service
docker build -t drdo/dashboard:latest .
```

### 2. Docker Compose Setup

**Create docker-compose.yml in project root:**

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: drdo-postgres
    environment:
      POSTGRES_USER: drdo_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: drdo_maintenance
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U drdo_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - drdo-network

  # Redis
  redis:
    image: redis:7-alpine
    container_name: drdo-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - drdo-network

  # Sensor Ingestion Service
  sensor-ingestion:
    image: drdo/sensor-ingestion:latest
    container_name: sensor-ingestion
    environment:
      DATABASE_URL: postgresql+asyncpg://drdo_user:${POSTGRES_PASSWORD}@postgres:5432/drdo_maintenance
      REDIS_URL: redis://redis:6379/0
      PORT: 8001
      LOG_LEVEL: INFO
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - drdo-network
    restart: unless-stopped

  # ML Prediction Service
  ml-prediction:
    image: drdo/ml-prediction:latest
    container_name: ml-prediction
    environment:
      DATABASE_URL: postgresql+asyncpg://drdo_user:${POSTGRES_PASSWORD}@postgres:5432/drdo_maintenance
      REDIS_URL: redis://redis:6379/0
      MODEL_PATH: /app/models/failure_predictor_v1.pkl
      PORT: 8002
      LOG_LEVEL: INFO
    ports:
      - "8002:8002"
    volumes:
      - ./models:/app/models:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - drdo-network
    restart: unless-stopped

  # Alert & Maintenance Service
  alert-maintenance:
    image: drdo/alert-maintenance:latest
    container_name: alert-maintenance
    environment:
      DATABASE_URL: postgresql+asyncpg://drdo_user:${POSTGRES_PASSWORD}@postgres:5432/drdo_maintenance
      REDIS_URL: redis://redis:6379/0
      PORT: 8003
      LOG_LEVEL: INFO
    ports:
      - "8003:8003"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - drdo-network
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    image: drdo/alert-maintenance:latest
    container_name: celery-worker
    command: celery -A app.celery_app worker --loglevel=info -Q notifications,maintenance,periodic,reports
    environment:
      DATABASE_URL: postgresql+asyncpg://drdo_user:${POSTGRES_PASSWORD}@postgres:5432/drdo_maintenance
      REDIS_URL: redis://redis:6379/0
      LOG_LEVEL: INFO
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - drdo-network
    restart: unless-stopped

  # Celery Beat
  celery-beat:
    image: drdo/alert-maintenance:latest
    container_name: celery-beat
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://drdo_user:${POSTGRES_PASSWORD}@postgres:5432/drdo_maintenance
      REDIS_URL: redis://redis:6379/0
      LOG_LEVEL: INFO
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - drdo-network
    restart: unless-stopped

  # Dashboard Service
  dashboard:
    image: drdo/dashboard:latest
    container_name: dashboard
    environment:
      DATABASE_URL: postgresql+asyncpg://drdo_user:${POSTGRES_PASSWORD}@postgres:5432/drdo_maintenance
      REDIS_URL: redis://redis:6379/0
      SENSOR_SERVICE_URL: http://sensor-ingestion:8001
      ML_SERVICE_URL: http://ml-prediction:8002
      ALERT_SERVICE_URL: http://alert-maintenance:8003
      PORT: 8004
      LOG_LEVEL: INFO
    ports:
      - "8004:8004"
    depends_on:
      - sensor-ingestion
      - ml-prediction
      - alert-maintenance
    networks:
      - drdo-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  drdo-network:
    driver: bridge
```

### 3. Start with Docker Compose

```bash
# Create .env file for docker-compose
echo "POSTGRES_PASSWORD=secure_password_here" > .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## Kubernetes Deployment

### 1. Prepare Kubernetes Cluster

**Create namespace:**

```bash
kubectl create namespace drdo-maintenance
kubectl config set-context --current --namespace=drdo-maintenance
```

### 2. Create Secrets

```bash
# Database credentials
kubectl create secret generic postgres-secret \
  --from-literal=username=drdo_user \
  --from-literal=password=SECURE_PASSWORD_HERE

# Application secrets
kubectl create secret generic app-secrets \
  --from-literal=database-url=postgresql+asyncpg://drdo_user:PASSWORD@postgres:5432/drdo_maintenance \
  --from-literal=redis-url=redis://redis:6379/0
```

### 3. Deploy PostgreSQL

**postgres-deployment.yaml:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: POSTGRES_DB
          value: drdo_maintenance
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command: ["pg_isready", "-U", "drdo_user"]
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "drdo_user"]
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### 4. Deploy Redis

**redis-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        livenessProbe:
          exec:
            command: ["redis-cli", "ping"]
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command: ["redis-cli", "ping"]
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### 5. Deploy Microservices

**sensor-ingestion-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sensor-ingestion
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sensor-ingestion
  template:
    metadata:
      labels:
        app: sensor-ingestion
    spec:
      containers:
      - name: sensor-ingestion
        image: drdo/sensor-ingestion:latest
        imagePullPolicy: Always
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis-url
        - name: PORT
          value: "8001"
        - name: LOG_LEVEL
          value: "INFO"
        ports:
        - containerPort: 8001
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: sensor-ingestion
spec:
  selector:
    app: sensor-ingestion
  ports:
  - port: 8001
    targetPort: 8001
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sensor-ingestion-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sensor-ingestion
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Repeat similar deployments for:**
- `ml-prediction-deployment.yaml`
- `alert-maintenance-deployment.yaml`
- `dashboard-deployment.yaml`
- `celery-worker-deployment.yaml`
- `celery-beat-deployment.yaml`

### 6. Apply Kubernetes Manifests

```bash
# Deploy infrastructure
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis --timeout=120s

# Deploy application services
kubectl apply -f sensor-ingestion-deployment.yaml
kubectl apply -f ml-prediction-deployment.yaml
kubectl apply -f alert-maintenance-deployment.yaml
kubectl apply -f celery-worker-deployment.yaml
kubectl apply -f celery-beat-deployment.yaml
kubectl apply -f dashboard-deployment.yaml

# Check status
kubectl get pods
kubectl get services
kubectl get hpa
```

### 7. Expose Services (Ingress)

**ingress.yaml:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: drdo-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.drdo-maintenance.example.com
    secretName: drdo-tls-cert
  rules:
  - host: api.drdo-maintenance.example.com
    http:
      paths:
      - path: /api/v1/sensors
        pathType: Prefix
        backend:
          service:
            name: sensor-ingestion
            port:
              number: 8001
      - path: /api/v1/predictions
        pathType: Prefix
        backend:
          service:
            name: ml-prediction
            port:
              number: 8002
      - path: /api/v1/alerts
        pathType: Prefix
        backend:
          service:
            name: alert-maintenance
            port:
              number: 8003
      - path: /api/v1/dashboard
        pathType: Prefix
        backend:
          service:
            name: dashboard
            port:
              number: 8004
```

```bash
kubectl apply -f ingress.yaml
```

---

## Database Setup

### Initial Schema Creation

**database/init.sql:**

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create sensor_data table
CREATE TABLE IF NOT EXISTS sensor_data (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    equipment_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temperature FLOAT NOT NULL,
    vibration FLOAT NOT NULL,
    pressure FLOAT NOT NULL,
    humidity FLOAT,
    voltage FLOAT,
    source VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensor_equipment ON sensor_data(equipment_id);
CREATE INDEX idx_sensor_timestamp ON sensor_data(timestamp);
CREATE INDEX idx_sensor_equipment_timestamp ON sensor_data(equipment_id, timestamp);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    equipment_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    failure_probability FLOAT NOT NULL,
    health_score FLOAT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    days_until_failure INTEGER NOT NULL,
    confidence VARCHAR(20) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    sensor_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prediction_equipment ON predictions(equipment_id);
CREATE INDEX idx_prediction_timestamp ON predictions(timestamp);
CREATE INDEX idx_prediction_severity ON predictions(severity);
CREATE INDEX idx_prediction_equipment_timestamp ON predictions(equipment_id, timestamp);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    equipment_id VARCHAR(50) NOT NULL,
    prediction_id VARCHAR(36),
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    resolution_notes TEXT,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

CREATE INDEX idx_alert_equipment ON alerts(equipment_id);
CREATE INDEX idx_alert_status ON alerts(status);
CREATE INDEX idx_alert_severity ON alerts(severity);
CREATE INDEX idx_alert_created ON alerts(created_at);

-- Create maintenance_tasks table
CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    equipment_id VARCHAR(50) NOT NULL,
    alert_id VARCHAR(36),
    task_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    description TEXT NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    completed_date TIMESTAMP,
    assigned_to VARCHAR(100),
    completed_by VARCHAR(100),
    completion_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

CREATE INDEX idx_task_equipment ON maintenance_tasks(equipment_id);
CREATE INDEX idx_task_status ON maintenance_tasks(status);
CREATE INDEX idx_task_scheduled ON maintenance_tasks(scheduled_date);
```

### Database Backup

**Automated Backup Script:**

```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/backups/drdo-maintenance"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -h localhost -U drdo_user -d drdo_maintenance > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Delete backups older than 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

**Schedule with cron:**

```bash
# Run daily at 2 AM
0 2 * * * /path/to/scripts/backup_database.sh
```

---

## Environment Configuration

### Environment Variables Template

**.env.production:**

```bash
# Service Configuration
SERVICE_NAME=sensor-ingestion
PORT=8001
DEBUG=False

# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://drdo_user:SECURE_PASSWORD@postgres:5432/drdo_maintenance

# Redis (REQUIRED)
REDIS_URL=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Security
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE
API_KEY=GENERATE_RANDOM_API_KEY_HERE

# Performance
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
WORKER_COUNT=4

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

### Generate Secure Secrets

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API key
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Service Startup Order

Proper startup sequence prevents connection errors:

1. **PostgreSQL** (wait until healthy)
2. **Redis** (wait until healthy)
3. **Sensor Ingestion Service**
4. **ML Prediction Service**
5. **Alert & Maintenance Service**
6. **Celery Worker**
7. **Celery Beat**
8. **Dashboard Service**

---

## Health Checks & Monitoring

### Health Check Endpoints

All services expose:
- `/health` - Basic health (no dependencies)
- `/health/ready` - Readiness (checks dependencies)

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'drdo-services'
    static_configs:
      - targets:
        - 'sensor-ingestion:8001'
        - 'ml-prediction:8002'
        - 'alert-maintenance:8003'
        - 'dashboard:8004'
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboards

Import pre-built dashboards from `monitoring/grafana-dashboards/`

---

## Backup & Recovery

### Database Backup

```bash
# Manual backup
pg_dump -h localhost -U drdo_user -d drdo_maintenance | gzip > backup.sql.gz

# Restore from backup
gunzip < backup.sql.gz | psql -h localhost -U drdo_user -d drdo_maintenance
```

### Redis Backup

```bash
# Trigger save
redis-cli SAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backups/redis-backup.rdb
```

---

## Scaling Strategies

### Horizontal Scaling

```bash
# Scale sensor-ingestion to 5 replicas
kubectl scale deployment sensor-ingestion --replicas=5

# Scale with HPA (auto-scaling)
kubectl autoscale deployment sensor-ingestion --min=3 --max=10 --cpu-percent=70
```

### Vertical Scaling

Update resource limits in deployment YAML and reapply.

---

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
kubectl logs -f deployment/sensor-ingestion

# Check events
kubectl get events --sort-by='.metadata.creationTimestamp'
```

#### Database Connection Failed

```bash
# Verify database is running
kubectl exec -it postgres-pod -- psql -U drdo_user -d drdo_maintenance -c "SELECT 1;"

# Test connectivity from service
kubectl exec -it sensor-ingestion-pod -- nc -zv postgres 5432
```

#### High Memory Usage

```bash
# Check resource usage
kubectl top pods

# Increase memory limits
kubectl set resources deployment sensor-ingestion --limits=memory=1Gi
```

---

## Production Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] Secrets stored securely (not in code)
- [ ] Database backups automated
- [ ] ML model trained and uploaded
- [ ] SSL certificates configured
- [ ] Firewall rules configured
- [ ] Monitoring & alerting setup
- [ ] Load testing completed
- [ ] Security audit passed

### Post-Deployment

- [ ] Health checks passing
- [ ] Logs flowing to central system
- [ ] Metrics being collected
- [ ] Alerts configured
- [ ] Backup restoration tested
- [ ] Disaster recovery plan documented
- [ ] On-call rotation established

---

**Document Version:** 1.0  
**Last Tested:** 2025-01-02  
**Support:** devops@drdo.example.com
