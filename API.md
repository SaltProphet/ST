# API Documentation

## Overview

The Focus ST Telemetry API provides comprehensive access to real-time telemetry data, historical sessions, alerts, and diagnostics.

Base URL: `http://localhost:8000`

## Authentication

All protected endpoints require JWT authentication.

### Get Access Token

```http
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Use Token in Requests

Include the token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

## User Roles

- **Viewer**: Read-only access to telemetry and sessions
- **Operator**: Can create alerts, export data, and run diagnostics
- **Admin**: Full access including user management

## Endpoints

### Authentication

#### Login
```http
POST /api/auth/token
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Sessions

#### List Sessions
```http
GET /api/sessions?limit=100
Authorization: Bearer <token>
```

Response:
```json
{
  "sessions": [
    {
      "session_id": "uuid-here",
      "start_time": "2024-01-01T12:00:00",
      "end_time": "2024-01-01T13:00:00",
      "vehicle_info": {"vehicle": "Focus ST"}
    }
  ]
}
```

#### Get Session Data
```http
GET /api/sessions/{session_id}?start_time=2024-01-01T12:00:00&end_time=2024-01-01T13:00:00
Authorization: Bearer <token>
```

#### Get Recent Data
```http
GET /api/sessions/current/recent?seconds=60
Authorization: Bearer <token>
```

### Alerts

#### List Alerts
```http
GET /api/alerts
Authorization: Bearer <token>
```

Response:
```json
{
  "alerts": [
    {
      "id": 1,
      "name": "High Boost",
      "pid": "BOOST",
      "condition": "gt",
      "threshold": 20.0,
      "enabled": true,
      "email_notify": false
    }
  ]
}
```

#### Create Alert
```http
POST /api/alerts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "High Oil Temp",
  "pid": "OIL_TEMP",
  "condition": "gt",
  "threshold": 260.0,
  "email_notify": true
}
```

Alert Conditions:
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `eq`: Equal
- `neq`: Not equal

### Export

#### Export Session Data
```http
POST /api/export
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "uuid-here",
  "start_time": "2024-01-01T12:00:00",
  "end_time": "2024-01-01T13:00:00",
  "format": "csv"
}
```

Formats: `csv`, `json`

### Diagnostics

#### List Available PIDs
```http
GET /api/diagnostics/pids
```

Response:
```json
{
  "pids": ["RPM", "SPEED", "BOOST", "OIL_TEMP", ...]
}
```

#### Get Diagnostic Trouble Codes
```http
GET /api/diagnostics/dtc
Authorization: Bearer <token>
```

Response:
```json
{
  "dtc_codes": [
    {
      "code": "P0171",
      "description": "System Too Lean (Bank 1)",
      "severity": "warning"
    }
  ]
}
```

### Replay

#### Start Replay Mode
```http
POST /api/replay/{session_id}?speed=1.0
Authorization: Bearer <token>
```

### User Management (Admin Only)

#### Create User
```http
POST /api/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "role": "viewer"
}
```

## WebSocket API

### Real-Time Telemetry Stream

Connect to: `ws://localhost:8000/ws/telemetry`

Messages are JSON objects:

```json
{
  "pid": "RPM",
  "value": 3500.5,
  "unit": "RPM",
  "timestamp": "2024-01-01T12:00:00.000000",
  "alerts": []
}
```

When an alert is triggered, the `alerts` array contains:

```json
{
  "alerts": [
    {
      "alert_id": 1,
      "name": "High Boost",
      "pid": "BOOST",
      "value": 21.5,
      "threshold": 20.0,
      "condition": "gt",
      "message": "Alert 'High Boost': BOOST = 21.5 gt 20.0",
      "timestamp": "2024-01-01T12:00:00"
    }
  ]
}
```

### JavaScript Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');

ws.onopen = () => {
  console.log('Connected to telemetry stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.pid}: ${data.value} ${data.unit}`);
  
  if (data.alerts && data.alerts.length > 0) {
    console.warn('Alert:', data.alerts[0].message);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from telemetry stream');
};
```

### Python Example

```python
import asyncio
import websockets
import json

async def connect_telemetry():
    uri = "ws://localhost:8000/ws/telemetry"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"{data['pid']}: {data['value']} {data['unit']}")

asyncio.run(connect_telemetry())
```

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

Error responses include a detail message:

```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider adding rate limiting middleware.

## CORS

CORS is not configured by default. To enable cross-origin requests, add CORS middleware to `app.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "session_id": "current-session-uuid",
  "timestamp": "2024-01-01T12:00:00"
}
```
