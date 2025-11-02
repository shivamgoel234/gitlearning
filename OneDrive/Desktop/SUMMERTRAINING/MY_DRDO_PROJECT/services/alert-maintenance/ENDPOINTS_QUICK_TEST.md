# Alert & Maintenance Service - Quick Endpoint Testing Guide

## Prerequisites
```bash
# 1. Ensure PostgreSQL and Redis are running
# 2. Ensure ML Prediction service is running on port 8002
# 3. Set environment variables (or use .env file)

# Start the service
cd services/alert-maintenance
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

---

## 🟢 ENDPOINT 1: Health Check

**Description:** Basic health check to verify service is running

```bash
curl http://localhost:8003/health
```

**Expected Response:**
```json
{
  "service": "alert-maintenance-service",
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-02T10:30:00.123456"
}
```

---

## 🔴 ENDPOINT 2: Generate Alert (MAIN ENDPOINT)

**Description:** Sends sensor data to ML service, gets prediction, creates alert if HIGH/CRITICAL

### Test Case 1: CRITICAL Alert (High failure probability)
```bash
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=RADAR-001&temperature=95.5&vibration=0.85&pressure=4.2&humidity=75.0&voltage=245.0"
```

### Test Case 2: HIGH Alert (Moderate failure probability)
```bash
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=AIRCRAFT-BASE-042&temperature=88.0&vibration=0.65&pressure=3.8&humidity=70.0&voltage=235.0"
```

### Test Case 3: No Alert (Low severity - should return 404)
```bash
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=NAVAL-PORT-003&temperature=45.5&vibration=0.25&pressure=2.1&humidity=50.0&voltage=220.0"
```

**Expected Response (CRITICAL):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "equipment_id": "RADAR-001",
  "severity": "CRITICAL",
  "failure_probability": 0.82,
  "days_until_failure": 7,
  "recommended_action": "URGENT: Schedule immediate maintenance - equipment likely to fail within 7 days. Initiate emergency procedures.",
  "status": "ACTIVE",
  "created_at": "2025-11-02T10:30:00Z",
  "acknowledged_at": null,
  "acknowledged_by": null,
  "resolved_at": null,
  "resolved_by": null,
  "notes": null,
  "health_score": 18.0,
  "confidence": "high",
  "source": "ml_prediction",
  "alert_type": "predictive"
}
```

**Expected Response (No Alert):**
```json
{
  "detail": "No alert needed (severity LOW/MEDIUM - only HIGH/CRITICAL generate alerts)"
}
```

---

## 🟡 ENDPOINT 3: Get Active Alerts

**Description:** Retrieve all active alerts with optional severity filter

### Get All Active Alerts
```bash
curl "http://localhost:8003/api/v1/alerts/active"
```

### Get Only CRITICAL Alerts
```bash
curl "http://localhost:8003/api/v1/alerts/active?severity=CRITICAL"
```

### Get Only HIGH Alerts
```bash
curl "http://localhost:8003/api/v1/alerts/active?severity=HIGH"
```

### Get Limited Results (max 10)
```bash
curl "http://localhost:8003/api/v1/alerts/active?limit=10"
```

**Expected Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "equipment_id": "RADAR-001",
    "severity": "CRITICAL",
    "failure_probability": 0.82,
    "days_until_failure": 7,
    "recommended_action": "URGENT: Schedule immediate maintenance...",
    "status": "ACTIVE",
    "created_at": "2025-11-02T10:30:00Z",
    "acknowledged_at": null,
    "acknowledged_by": null,
    "resolved_at": null,
    "resolved_by": null,
    "notes": null,
    "health_score": 18.0,
    "confidence": "high",
    "source": "ml_prediction",
    "alert_type": "predictive"
  }
]
```

---

## 🔵 ENDPOINT 4: Schedule Maintenance Task

**Description:** Create a new maintenance task for equipment

### Minimal Request (Required Fields Only)
```bash
curl -X POST "http://localhost:8003/api/v1/maintenance/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-001",
    "task_type": "PREVENTIVE",
    "priority": "HIGH",
    "scheduled_date": "2025-11-10T10:00:00Z"
  }'
```

### Full Request (All Fields)
```bash
curl -X POST "http://localhost:8003/api/v1/maintenance/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-001",
    "task_type": "PREVENTIVE",
    "priority": "CRITICAL",
    "scheduled_date": "2025-11-09T08:00:00Z",
    "title": "Emergency cooling system maintenance",
    "description": "Replace cooling system filters due to predicted failure",
    "estimated_duration_hours": 4,
    "cost_estimate": 5000.0,
    "assigned_to": "maintenance-team-a@drdo.gov.in",
    "notes": "High priority - equipment showing signs of imminent failure",
    "alert_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Emergency Task
```bash
curl -X POST "http://localhost:8003/api/v1/maintenance/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "AIRCRAFT-BASE-042",
    "task_type": "EMERGENCY",
    "priority": "CRITICAL",
    "scheduled_date": "2025-11-02T14:00:00Z",
    "title": "URGENT: Engine component failure",
    "estimated_duration_hours": 8,
    "cost_estimate": 15000.0
  }'
```

**Expected Response:**
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "equipment_id": "RADAR-001",
  "task_type": "PREVENTIVE",
  "priority": "CRITICAL",
  "scheduled_date": "2025-11-09T08:00:00Z",
  "status": "SCHEDULED",
  "title": "Emergency cooling system maintenance",
  "description": "Replace cooling system filters due to predicted failure",
  "assigned_to": "maintenance-team-a@drdo.gov.in",
  "assigned_at": null,
  "completed_date": null,
  "estimated_duration_hours": 4,
  "actual_duration_hours": null,
  "cost_estimate": 5000.0,
  "actual_cost": null,
  "notes": "High priority - equipment showing signs of imminent failure",
  "completion_notes": null,
  "alert_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-11-02T10:30:00Z",
  "updated_at": "2025-11-02T10:30:00Z",
  "created_by": null
}
```

---

## 🌐 Interactive API Documentation

Once the service is running, access the auto-generated API docs:

### Swagger UI (Recommended)
```
http://localhost:8003/docs
```

### ReDoc (Alternative)
```
http://localhost:8003/redoc
```

---

## 🧪 Testing Workflow

### Complete Test Flow
```bash
# 1. Health check
curl http://localhost:8003/health

# 2. Generate alert for equipment
curl -X POST "http://localhost:8003/api/v1/alerts/generate?equipment_id=RADAR-001&temperature=95.5&vibration=0.85&pressure=4.2"

# 3. View active alerts
curl "http://localhost:8003/api/v1/alerts/active"

# 4. Schedule maintenance for the alert
curl -X POST "http://localhost:8003/api/v1/maintenance/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-001",
    "task_type": "PREVENTIVE",
    "priority": "CRITICAL",
    "scheduled_date": "2025-11-09T08:00:00Z",
    "title": "Address CRITICAL alert",
    "alert_id": "[USE_ALERT_ID_FROM_STEP_2]"
  }'
```

---

## 🐛 Troubleshooting

### Service Not Starting
```bash
# Check if port 8003 is already in use
lsof -i :8003  # Linux/Mac
netstat -ano | findstr :8003  # Windows

# Check database connection
psql -U drdo -d equipment_maintenance -h localhost -p 5432

# Check Redis connection
redis-cli ping
```

### ML Service Connection Error
```bash
# Verify ML service is running
curl http://localhost:8002/health

# Check ML service URL in .env
echo $ML_PREDICTION_SERVICE_URL
```

### Database Connection Error
```bash
# Check DATABASE_URL format
# Should be: postgresql+asyncpg://user:password@host:port/database
echo $DATABASE_URL
```

---

## 📊 Test Data Examples

### Valid Equipment IDs (DRDO Format)
- `RADAR-LOC-001`
- `AIRCRAFT-BASE-042`
- `NAVAL-PORT-003`
- `MISSILE-SITE-007`
- `TANK-DEPOT-015`

### Sensor Value Ranges
- **Temperature:** -50.0 to 200.0 °C
- **Vibration:** 0.0 to 2.0 mm/s
- **Pressure:** 0.0 to 10.0 bar
- **Humidity:** 0.0 to 100.0 %
- **Voltage:** 0.0 to 500.0 V

### Task Types
- `ROUTINE` - Regular scheduled maintenance
- `PREVENTIVE` - Preventive maintenance based on predictions
- `CORRECTIVE` - Fix identified issues
- `EMERGENCY` - Urgent critical repairs

### Priority Levels
- `LOW` - Can be scheduled flexibly
- `MEDIUM` - Should be done within timeframe
- `HIGH` - Important, schedule soon
- `CRITICAL` - Urgent, immediate attention

---

## 🎯 Success Criteria

✅ **Service is working correctly if:**

1. Health check returns 200 OK
2. Generate alert creates alert for high sensor values (HIGH/CRITICAL)
3. Generate alert returns 404 for normal sensor values (LOW/MEDIUM)
4. Get active alerts returns list of alerts
5. Schedule maintenance creates task and returns 201 Created
6. Email notification is queued (check Celery logs)

---

**Last Updated:** 2025-11-02  
**Service Version:** 1.0.0  
**Port:** 8003
