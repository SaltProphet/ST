# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser / Client                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Dashboard   │  │  REST API    │  │  WebSocket   │         │
│  │   (HTML/JS)  │  │   Clients    │  │   Clients    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │ HTTP/HTTPS       │ HTTP/HTTPS       │ WebSocket
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────────┐
│                     FastAPI Application                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  API Routes Layer                         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐      │  │
│  │  │  Auth   │ │Sessions │ │  Alerts  │ │   Export │      │  │
│  │  │   API   │ │   API   │ │   API    │ │    API   │      │  │
│  │  └────┬────┘ └────┬────┘ └────┬─────┘ └────┬─────┘      │  │
│  └───────┼───────────┼──────────┼──────────────┼────────────┘  │
│          │           │          │              │                │
│  ┌───────▼───────────▼──────────▼──────────────▼────────────┐  │
│  │              Business Logic Layer                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │   Auth   │ │ Database │ │  Alerts  │ │  Cloud   │   │  │
│  │  │ Manager  │ │ Manager  │ │Evaluator │ │   Sync   │   │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │  │
│  └───────┼────────────┼─────────────┼────────────┼─────────┘  │
└──────────┼────────────┼─────────────┼────────────┼────────────┘
           │            │             │            │
           │            │             │            │
    ┌──────▼─────┐ ┌───▼────────┐ ┌──▼────────┐ ┌▼──────────┐
    │   JWT      │ │  SQLite    │ │   SMTP    │ │  Cloud    │
    │  Tokens    │ │  Database  │ │   Server  │ │    API    │
    └────────────┘ └───┬────────┘ └───────────┘ └───────────┘
                       │
            ┌──────────▼──────────┐
            │  Telemetry Sessions │
            │  ┌───────────────┐  │
            │  │ Session Data  │  │
            │  │ Alert Configs │  │
            │  │ Alert History │  │
            │  │ User Accounts │  │
            │  └───────────────┘  │
            └─────────────────────┘
```

## Data Flow

### Real-Time Telemetry Stream

```
OBD Simulator
     │
     │ (async stream)
     ▼
Hardware Abstraction Layer
     │
     │ (async for loop)
     ▼
Telemetry Worker (Background Task)
     │
     ├──► Database (Insert)
     │
     ├──► Alert Evaluator (Check thresholds)
     │         │
     │         ├──► Email (if triggered)
     │         └──► Alert History (log)
     │
     ├──► Cloud Sync Queue (if enabled)
     │
     └──► WebSocket Manager (Broadcast)
               │
               ▼
          Connected Clients
```

### API Request Flow

```
Client Request
     │
     ▼
FastAPI Router
     │
     ├──► Authentication Middleware
     │         │
     │         ├──► Verify JWT Token
     │         │
     │         └──► Check User Role
     │                   │
     ▼                   ▼
Endpoint Handler  (if authorized)
     │
     ▼
Business Logic
     │
     ├──► Database Operations
     │
     ├──► Alert Management
     │
     └──► Data Processing
           │
           ▼
      JSON Response
           │
           ▼
        Client
```

## Component Details

### Frontend Layer
- **Dashboard**: Jinja2 template with Chart.js
- **WebSocket Client**: Real-time data subscription
- **API Client**: REST calls for actions

### API Layer
- **Authentication**: OAuth2 + JWT
- **Sessions**: CRUD operations
- **Alerts**: Configuration management
- **Export**: Data extraction
- **Diagnostics**: System info

### Business Logic
- **Auth Manager**: User authentication & authorization
- **Database Manager**: Async SQLite operations
- **Alert Evaluator**: Threshold checking & notifications
- **Cloud Sync**: Queue-based remote sync

### Data Layer
- **SQLite Database**: Persistent storage
- **Sessions**: Telemetry recordings
- **Users**: Account management
- **Alerts**: Configuration & history

### External Integrations
- **SMTP Server**: Email notifications
- **Cloud API**: Remote monitoring
- **OBD Hardware**: Real vehicle data (optional)

## Security Architecture

```
┌─────────────────────────────────────────┐
│         Security Layers                  │
├─────────────────────────────────────────┤
│  1. HTTPS/TLS (Transport Security)      │
├─────────────────────────────────────────┤
│  2. OAuth2 Authentication               │
│     - Username/Password                 │
│     - JWT Token Generation              │
├─────────────────────────────────────────┤
│  3. JWT Token Validation                │
│     - Signature Verification            │
│     - Expiration Check                  │
├─────────────────────────────────────────┤
│  4. Role-Based Authorization            │
│     - Viewer: Read-only                 │
│     - Operator: + Alerts, Export        │
│     - Admin: + User Management          │
├─────────────────────────────────────────┤
│  5. Password Security                   │
│     - bcrypt Hashing                    │
│     - Salt per Password                 │
└─────────────────────────────────────────┘
```

## Deployment Architecture

### Development
```
┌─────────────────┐
│  Local Machine  │
│                 │
│  ┌───────────┐  │
│  │  Python   │  │
│  │  app.py   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  SQLite   │  │
│  └───────────┘  │
└─────────────────┘
```

### Production (Standalone)
```
┌─────────────────────────────────┐
│         Linux Server            │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Nginx (Reverse Proxy) │  │
│  │         :80/:443          │  │
│  └──────────┬────────────────┘  │
│             │                   │
│  ┌──────────▼────────────────┐  │
│  │    FastAPI Application    │  │
│  │         :8000             │  │
│  └──────────┬────────────────┘  │
│             │                   │
│  ┌──────────▼────────────────┐  │
│  │    SQLite Database        │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### Production (Docker)
```
┌─────────────────────────────────┐
│       Docker Host               │
│                                 │
│  ┌───────────────────────────┐  │
│  │   nginx Container         │  │
│  │      :80/:443            │  │
│  └──────────┬────────────────┘  │
│             │                   │
│  ┌──────────▼────────────────┐  │
│  │  telemetry Container      │  │
│  │      :8000               │  │
│  └──────────┬────────────────┘  │
│             │                   │
│  ┌──────────▼────────────────┐  │
│  │   Volume (Database)       │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

## Scalability Considerations

### Current Architecture
- Single process (suitable for 100+ concurrent users)
- SQLite (suitable for development and small deployments)
- In-memory WebSocket connections

### Scale-Up Options
1. **PostgreSQL** - Replace SQLite for better concurrency
2. **Redis** - Session storage and caching
3. **Load Balancer** - Multiple app instances
4. **Message Queue** - RabbitMQ/Kafka for telemetry
5. **Separate WebSocket Server** - Dedicated WS handling
6. **CDN** - Static asset delivery

## Technology Stack

### Core
- **Python 3.12+**: Modern Python with async/await
- **FastAPI**: High-performance web framework
- **Uvicorn**: ASGI server
- **aiosqlite**: Async SQLite
- **WebSockets**: Real-time communication

### Authentication
- **python-jose**: JWT tokens
- **passlib**: Password hashing
- **bcrypt**: Secure hashing algorithm

### Frontend
- **Jinja2**: Template engine
- **Chart.js**: Data visualization
- **HTML5/CSS3**: Modern web standards

### Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async test support

### Utilities
- **pydantic**: Data validation
- **python-dotenv**: Environment management
- **argparse**: CLI interface

## API Endpoints Summary

### Public
- `GET /` - Dashboard
- `GET /health` - Health check

### Authentication
- `POST /api/auth/token` - Login
- `GET /api/auth/me` - Current user

### Sessions (Requires: Viewer)
- `GET /api/sessions` - List sessions
- `GET /api/sessions/{id}` - Get session
- `GET /api/sessions/current/recent` - Recent data

### Alerts (Requires: Viewer/Operator)
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert (Operator)

### Export (Requires: Viewer)
- `POST /api/export` - Export data

### Diagnostics
- `GET /api/diagnostics/pids` - List PIDs
- `GET /api/diagnostics/dtc` - Get DTCs (Operator)

### Users (Requires: Admin)
- `POST /api/users` - Create user

### WebSocket
- `WS /ws/telemetry` - Real-time stream
