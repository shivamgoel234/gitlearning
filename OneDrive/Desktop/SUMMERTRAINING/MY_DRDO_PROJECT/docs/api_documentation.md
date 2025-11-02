# DRDO Equipment Maintenance Prediction System - API Documentation

**Version:** 1.0  
**Last Updated:** 2025-01-02  
**Base URLs:**
- **Development**: `http://localhost:800X`
- **Staging**: `https://staging.drdo-maintenance.example.com`
- **Production**: `https://api.drdo-maintenance.example.com`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Response Formats](#common-response-formats)
4. [Error Handling](#error-handling)
5. [Sensor Ingestion API (Port 8001)](#sensor-ingestion-api-port-8001)
6. [ML Prediction API (Port 8002)](#ml-prediction-api-port-8002)
7. [Alert & Maintenance API (Port 8003)](#alert--maintenance-api-port-8003)
8. [Dashboard API (Port 8004)](#dashboard-api-port-8004)
9. [API Versioning](#api-versioning)
10. [Rate Limiting](#rate-limiting)
11. [Webhooks](#webhooks)

---

## Overview

The DRDO Equipment Maintenance Prediction System exposes four independent RESTful APIs, one for each microservice. All APIs follow consistent patterns and conventions.

### API Design Principles

- **RESTful**: Standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **JSON**: All requests and responses use JSON format
- **Versioned**: All endpoints include API version (`/api/v1/`)
- **Consistent**: Standard error formats across all services
- **Documented**: OpenAPI/Swagger documentation at `/docs`

### OpenAPI Documentation

Each service provides interactive API documentation:

- Sensor Ingestion: `http://localhost:8001/docs`
- ML Prediction: `http://localhost:8002/docs`
- Alert & Maintenance: `http://localhost:8003/docs`
- Dashboard: `http://localhost:8004/docs`

---

## Authentication

### Current Implementation (Development)

No authentication required for development environment.

### Future Implementation (Production)

#### API Key Authentication

```http
GET /api/v1/sensors/ingest
Authorization: Bearer YOUR_API_KEY
```

#### JWT Token Authentication

```http
POST /auth/login
Content-Type: application/json

{
  "username": "technician@drdo.gov.in",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## Common Response Formats

### Success Response

```json
{
  "status": "success",
  "data": {
    // Response data here
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid equipment ID format",
    "details": {
      "field": "equipment_id",
      "constraint": "Must match pattern TYPE-LOCATION-NUMBER"
    }
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Pagination

For endpoints returning lists:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 523,
    "total_pages": 11,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Status Code | Meaning | When Used |
|------------|---------|-----------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily down |

### Error Codes

| Error Code | Description |
|-----------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `NOT_FOUND` | Resource not found |
| `DATABASE_ERROR` | Database operation failed |
| `SERVICE_UNAVAILABLE` | External service unavailable |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Unexpected server error |

---

## Sensor Ingestion API (Port 8001)

### Base URL
`http://localhost:8001/api/v1`

### Endpoints

#### Health Check

**GET** `/health`

Check service health without dependencies.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "sensor-ingestion",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

#### Readiness Check

**GET** `/health/ready`

Check service readiness including database and Redis.

**Response (200 OK):**
```json
{
  "status": "ready",
  "service": "sensor-ingestion",
  "timestamp": "2025-01-01T12:00:00Z",
  "database": "connected",
  "redis": "connected"
}
```

---

#### Ingest Sensor Data

**POST** `/sensors/ingest`

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

**Request Schema:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| equipment_id | string | Yes | Pattern: `^[A-Z]+-[A-Z0-9]+-\\d{3}$` | Equipment identifier |
| temperature | float | Yes | -50.0 to 200.0 | Temperature in °C |
| vibration | float | Yes | 0.0 to 2.0 | Vibration in mm/s |
| pressure | float | Yes | 0.0 to 10.0 | Pressure in bar |
| humidity | float | No | 0.0 to 100.0 | Humidity in % |
| voltage | float | No | 0.0 to 500.0 | Voltage in V |
| source | string | No | Max 50 chars | Data source identifier |
| notes | string | No | Max 500 chars | Additional notes |

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
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid equipment ID format",
    "details": {
      "field": "equipment_id",
      "constraint": "Must match pattern TYPE-LOCATION-NUMBER"
    }
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

#### Get Latest Readings

**GET** `/sensors/{equipment_id}/latest?limit=10`

Retrieve latest sensor readings for specific equipment.

**Path Parameters:**
- `equipment_id` (string, required): Equipment identifier

**Query Parameters:**
- `limit` (integer, optional, default: 10, max: 100): Number of readings

**Success Response (200 OK):**
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
      "voltage": 220.0,
      "source": "iot-sensor-01"
    }
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Equipment RADAR-LOC-999 not found"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## ML Prediction API (Port 8002)

### Base URL
`http://localhost:8002/api/v1`

### Endpoints

#### Health Check

**GET** `/health`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "ml-prediction",
  "model_loaded": true,
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

#### Manual Prediction

**POST** `/predictions/predict`

Perform manual failure prediction for equipment.

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

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| equipment_id | string | Yes | Equipment identifier |
| sensor_data.temperature | float | Yes | Temperature in °C |
| sensor_data.vibration | float | Yes | Vibration in mm/s |
| sensor_data.pressure | float | Yes | Pressure in bar |
| sensor_data.humidity | float | Yes | Humidity in % |
| sensor_data.voltage | float | Yes | Voltage in V |

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

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| prediction_id | string | Unique prediction identifier |
| equipment_id | string | Equipment identifier |
| timestamp | string (ISO 8601) | Prediction time |
| failure_probability | float (0.0-1.0) | Probability of failure |
| health_score | float (0-100) | Equipment health score |
| severity | string | CRITICAL/HIGH/MEDIUM/LOW |
| days_until_failure | integer | Estimated days until failure |
| confidence | string | high/medium/low |
| recommendations | array[string] | Action recommendations |

---

#### Get Prediction History

**GET** `/predictions/{equipment_id}/latest?limit=10`

Retrieve latest predictions for equipment.

**Path Parameters:**
- `equipment_id` (string, required): Equipment identifier

**Query Parameters:**
- `limit` (integer, optional, default: 10, max: 100): Number of predictions

**Success Response (200 OK):**
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
      "severity": "HIGH",
      "days_until_failure": 15
    }
  ]
}
```

---

#### Get Health Trend

**GET** `/predictions/{equipment_id}/health-trend?days=7`

Get equipment health score trend over time.

**Path Parameters:**
- `equipment_id` (string, required): Equipment identifier

**Query Parameters:**
- `days` (integer, optional, default: 7, max: 90): Number of days

**Success Response (200 OK):**
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

## Alert & Maintenance API (Port 8003)

### Base URL
`http://localhost:8003/api/v1`

### Endpoints

#### List Alerts

**GET** `/alerts?equipment_id=RADAR-LOC-001&status=active&severity=CRITICAL&limit=50`

List alerts with optional filtering.

**Query Parameters:**
- `equipment_id` (string, optional): Filter by equipment
- `status` (string, optional): active/acknowledged/resolved
- `severity` (string, optional): CRITICAL/HIGH/MEDIUM/LOW
- `limit` (integer, optional, default: 50, max: 200): Number of results

**Success Response (200 OK):**
```json
{
  "count": 25,
  "alerts": [
    {
      "alert_id": "alert-uuid-123",
      "equipment_id": "RADAR-LOC-001",
      "prediction_id": "pred-uuid-456",
      "severity": "CRITICAL",
      "message": "85% failure probability detected",
      "status": "active",
      "created_at": "2025-01-01T12:00:00Z",
      "acknowledged_at": null,
      "acknowledged_by": null
    }
  ]
}
```

---

#### Acknowledge Alert

**POST** `/alerts/{alert_id}/acknowledge`

Acknowledge an active alert.

**Path Parameters:**
- `alert_id` (string, required): Alert identifier

**Request Body:**
```json
{
  "acknowledged_by": "technician-123",
  "notes": "Maintenance team notified"
}
```

**Success Response (200 OK):**
```json
{
  "alert_id": "alert-uuid-123",
  "status": "acknowledged",
  "acknowledged_at": "2025-01-01T12:15:00Z",
  "acknowledged_by": "technician-123"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVALID_STATE",
    "message": "Alert is already acknowledged or resolved"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

#### Resolve Alert

**POST** `/alerts/{alert_id}/resolve`

Mark alert as resolved after maintenance completion.

**Path Parameters:**
- `alert_id` (string, required): Alert identifier

**Request Body:**
```json
{
  "resolved_by": "technician-123",
  "resolution_notes": "Replaced faulty cooling fan",
  "maintenance_completed": true
}
```

**Success Response (200 OK):**
```json
{
  "alert_id": "alert-uuid-123",
  "status": "resolved",
  "resolved_at": "2025-01-02T08:30:00Z",
  "resolved_by": "technician-123"
}
```

---

#### Schedule Maintenance

**POST** `/maintenance/schedule`

Schedule a maintenance task for equipment.

**Request Body:**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "task_type": "preventive",
  "priority": "high",
  "scheduled_date": "2025-01-05T10:00:00Z",
  "description": "Inspect cooling system and replace filters",
  "assigned_to": "team-alpha"
}
```

**Request Schema:**

| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| equipment_id | string | Yes | - | Equipment identifier |
| task_type | string | Yes | preventive/corrective/inspection | Type of maintenance |
| priority | string | Yes | critical/high/medium/low | Task priority |
| scheduled_date | string (ISO 8601) | Yes | - | Scheduled time |
| description | string | Yes | Max 500 chars | Task description |
| assigned_to | string | No | Max 100 chars | Assigned team/person |

**Success Response (201 Created):**
```json
{
  "task_id": "task-uuid-456",
  "equipment_id": "RADAR-LOC-001",
  "status": "scheduled",
  "scheduled_date": "2025-01-05T10:00:00Z",
  "created_at": "2025-01-01T12:00:00Z"
}
```

---

#### List Maintenance Tasks

**GET** `/maintenance/tasks?equipment_id=RADAR-LOC-001&status=scheduled&priority=high`

List maintenance tasks with optional filtering.

**Query Parameters:**
- `equipment_id` (string, optional): Filter by equipment
- `status` (string, optional): scheduled/in_progress/completed/cancelled
- `priority` (string, optional): critical/high/medium/low
- `limit` (integer, optional, default: 50): Number of results

**Success Response (200 OK):**
```json
{
  "count": 15,
  "tasks": [
    {
      "task_id": "task-uuid-456",
      "equipment_id": "RADAR-LOC-001",
      "task_type": "preventive",
      "priority": "high",
      "status": "scheduled",
      "scheduled_date": "2025-01-05T10:00:00Z",
      "description": "Inspect cooling system",
      "assigned_to": "team-alpha"
    }
  ]
}
```

---

#### Update Task Status

**PATCH** `/maintenance/tasks/{task_id}/status`

Update maintenance task status.

**Path Parameters:**
- `task_id` (string, required): Task identifier

**Request Body:**
```json
{
  "status": "completed",
  "completion_notes": "All filters replaced, system tested",
  "completed_by": "technician-123"
}
```

**Success Response (200 OK):**
```json
{
  "task_id": "task-uuid-456",
  "status": "completed",
  "completed_date": "2025-01-05T14:30:00Z",
  "completed_by": "technician-123"
}
```

---

## Dashboard API (Port 8004)

### Base URL
`http://localhost:8004/api/v1`

### Endpoints

#### Get System Overview

**GET** `/dashboard/overview`

Get system-wide overview statistics.

**Success Response (200 OK):**
```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "total_equipment": 150,
  "active_alerts": 23,
  "critical_alerts": 5,
  "high_alerts": 18,
  "pending_maintenance": 42,
  "average_fleet_health": 72.5,
  "equipment_by_severity": {
    "CRITICAL": 5,
    "HIGH": 18,
    "MEDIUM": 37,
    "LOW": 90
  }
}
```

---

#### Get Equipment Details

**GET** `/dashboard/equipment/{equipment_id}/details`

Get comprehensive details for specific equipment.

**Path Parameters:**
- `equipment_id` (string, required): Equipment identifier

**Success Response (200 OK):**
```json
{
  "equipment_id": "RADAR-LOC-001",
  "current_health_score": 65.3,
  "current_severity": "MEDIUM",
  "latest_sensor_reading": {
    "timestamp": "2025-01-01T12:00:00Z",
    "temperature": 85.5,
    "vibration": 0.45,
    "pressure": 3.2,
    "humidity": 65.0,
    "voltage": 220.0
  },
  "latest_prediction": {
    "timestamp": "2025-01-01T12:05:00Z",
    "failure_probability": 0.45,
    "health_score": 65.3,
    "severity": "MEDIUM",
    "days_until_failure": 30
  },
  "active_alerts": [
    {
      "alert_id": "alert-123",
      "severity": "MEDIUM",
      "message": "Elevated temperature detected",
      "created_at": "2025-01-01T11:00:00Z",
      "status": "active"
    }
  ],
  "scheduled_maintenance": [
    {
      "task_id": "task-456",
      "task_type": "preventive",
      "scheduled_date": "2025-01-05T10:00:00Z",
      "priority": "medium"
    }
  ]
}
```

---

#### Get Alert Statistics

**GET** `/analytics/alert-statistics?start_date=2025-01-01&end_date=2025-01-31`

Get alert statistics for date range.

**Query Parameters:**
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)

**Success Response (200 OK):**
```json
{
  "period": "2025-01-01 to 2025-01-31",
  "total_alerts": 150,
  "by_severity": {
    "CRITICAL": 20,
    "HIGH": 45,
    "MEDIUM": 60,
    "LOW": 25
  },
  "acknowledged_rate": 0.87,
  "average_resolution_time_hours": 24.5,
  "top_equipment_by_alerts": [
    {"equipment_id": "RADAR-LOC-001", "alert_count": 15},
    {"equipment_id": "AIRCRAFT-BASE-042", "alert_count": 12}
  ]
}
```

---

#### Generate Report

**POST** `/reports/generate`

Generate downloadable report.

**Request Body:**
```json
{
  "report_type": "maintenance_summary",
  "format": "pdf",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "include_charts": true
}
```

**Request Schema:**

| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| report_type | string | Yes | maintenance_summary/equipment_health | Report type |
| format | string | Yes | pdf/csv | Output format |
| start_date | string | Yes | YYYY-MM-DD | Report start date |
| end_date | string | Yes | YYYY-MM-DD | Report end date |
| include_charts | boolean | No | true/false | Include visualizations |

**Success Response (200 OK):**
```json
{
  "report_id": "report-uuid-789",
  "status": "generated",
  "download_url": "/api/v1/reports/download/report-uuid-789",
  "generated_at": "2025-01-01T12:00:00Z",
  "expires_at": "2025-01-08T12:00:00Z"
}
```

---

#### Download Report

**GET** `/reports/download/{report_id}`

Download generated report file.

**Path Parameters:**
- `report_id` (string, required): Report identifier

**Success Response (200 OK):**
- Content-Type: `application/pdf` or `text/csv`
- Content-Disposition: `attachment; filename="report.pdf"`
- Binary file content

**Error Response (404 Not Found):**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Report not found or expired"
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## API Versioning

### Current Version: v1

All endpoints are prefixed with `/api/v1/`.

### Version Migration

When v2 is released:
- v1 endpoints remain available for 12 months
- Deprecation notices added to v1 responses
- New features only in v2

**Deprecation Header (Future):**
```http
Sunset: Sat, 01 Jan 2026 00:00:00 GMT
Deprecation: true
Link: <https://api.drdo.example.com/api/v2/sensors/ingest>; rel="successor-version"
```

---

## Rate Limiting

### Default Limits (Per API Key)

| Service | Requests per Minute | Burst Limit |
|---------|-------------------|-------------|
| Sensor Ingestion | 1000 | 1500 |
| ML Prediction | 500 | 750 |
| Alert & Maintenance | 200 | 300 |
| Dashboard | 100 | 150 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1672531260
```

### Rate Limit Exceeded Response (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 1000 requests per minute exceeded",
    "retry_after": 45
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## Webhooks

### Future Feature: Event Notifications

Subscribe to real-time events via webhooks.

**Webhook Registration (Future):**

```http
POST /api/v1/webhooks/subscribe
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["alert.created", "prediction.high_severity"],
  "secret": "your_webhook_secret"
}
```

**Supported Events:**
- `sensor.data_received`
- `prediction.completed`
- `alert.created`
- `alert.acknowledged`
- `alert.resolved`
- `maintenance.scheduled`
- `maintenance.completed`

---

## API Testing

### Using cURL

```bash
# Ingest sensor data
curl -X POST http://localhost:8001/api/v1/sensors/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": "RADAR-LOC-001",
    "temperature": 85.5,
    "vibration": 0.45,
    "pressure": 3.2,
    "humidity": 65.0,
    "voltage": 220.0
  }'
```

### Using Python

```python
import requests

# Ingest sensor data
response = requests.post(
    "http://localhost:8001/api/v1/sensors/ingest",
    json={
        "equipment_id": "RADAR-LOC-001",
        "temperature": 85.5,
        "vibration": 0.45,
        "pressure": 3.2,
        "humidity": 65.0,
        "voltage": 220.0
    }
)

print(response.json())
```

---

**Document Version:** 1.0  
**API Version:** v1  
**Contact:** api-support@drdo.example.com
