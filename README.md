# Focus ST Telemetry Simulation & Gateway

An advanced telemetry simulation and gateway system for the Ford Focus ST, featuring real-time monitoring, cloud sync, custom alerts, historical replay, and comprehensive diagnostics.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)

## 🚀 Features

### Core Capabilities
- **Real-Time Telemetry**: WebSocket-based streaming of OBD-II data at configurable rates (default 10Hz)
- **Web Dashboard**: Modern, responsive dashboard with Chart.js visualizations
- **OBD-II Simulation**: Realistic Focus ST telemetry simulation with multiple driving scenarios

### Advanced Features

#### 1. 💾 Telemetry Data Persistence
- SQLite database for storing raw telemetry streams
- Configurable rolling buffer (default: 10 minutes)
- CSV/JSON export functionality
- Automatic cleanup of old data

#### 2. ⏮️ Historical Replay
- Replay previously recorded sessions through WebSocket gateway
- Adjustable playback speed
- Session management and listing

#### 3. 🔔 Custom Alerts & Notifications
- User-configurable triggers on any PID (RPM, boost, temperatures, etc.)
- Multiple condition operators: >, >=, <, <=, ==, !=
- Email notifications via SMTP
- Alert history tracking
- Real-time alert display in dashboard

#### 4. 📊 Advanced Visualization
- Chart.js integration for real-time trend lines
- Multi-axis charts (RPM, boost, speed)
- Exportable dashboard data
- Mobile-responsive design

#### 5. ☁️ Cloud Sync
- Optional forwarding to remote APIs
- Queue-based architecture for reliability
- Configurable via environment variables

#### 6. 🔐 Role-Based Access & Security
- OAuth2 authentication with JWT tokens
- Three user roles: viewer, operator, admin
- Secure API endpoints with role-based permissions
- Password hashing with bcrypt

#### 7. 🔧 Diagnostic Tools Suite
- Interactive PID explorer
- DTC (Diagnostic Trouble Codes) retrieval
- REST API for diagnostic queries
- Support for custom PID queries

#### 8. 🔌 Hardware Abstraction Layer
- Pluggable interface system
- Built-in simulator for development
- Support for USB OBD adapters
- CAN bus adapter interface (extensible)
- Remote bridge proxy support

#### 9. 📱 Mobile-Friendly Design
- Responsive dashboard layout
- Touch-optimized controls
- PWA-ready architecture

#### 10. 🔗 Third-Party API
- REST API for extensions
- WebSocket streaming for real-time integrations
- Comprehensive API documentation
- JSON response format

## 📋 Prerequisites

- Python 3.12 or higher
- pip package manager

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone https://github.com/SaltProphet/ST.git
cd ST
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Run the application**:
```bash
python app.py
```

The server will start on `http://localhost:8000` by default.

## 🎮 Usage

### Web Dashboard
Open your browser and navigate to `http://localhost:8000` to access the real-time telemetry dashboard.

### API Documentation
Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Authentication

Default admin credentials:
- Username: `admin`
- Password: `admin`

**⚠️ Change these immediately in production!**

Get an access token:
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

Use the token in subsequent requests:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/sessions"
```

### WebSocket Connection

Connect to real-time telemetry stream:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log(`${data.pid}: ${data.value} ${data.unit}`);
};
```

### Creating Alerts

```bash
curl -X POST "http://localhost:8000/api/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Boost Alert",
    "pid": "BOOST",
    "condition": "gt",
    "threshold": 20.0,
    "email_notify": true
  }'
```

### Exporting Data

```bash
curl -X POST "http://localhost:8000/api/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "format": "csv"
  }' > telemetry.csv
```

## 🎯 Available PIDs

The simulator provides the following OBD-II PIDs:

| PID | Description | Unit | Range |
|-----|-------------|------|-------|
| RPM | Engine RPM | RPM | 800-6500 |
| SPEED | Vehicle Speed | MPH | 0-155 |
| THROTTLE | Throttle Position | % | 0-100 |
| ENGINE_LOAD | Engine Load | % | 0-100 |
| COOLANT_TEMP | Coolant Temperature | °F | 80-220 |
| INTAKE_TEMP | Intake Air Temperature | °F | 60-180 |
| MAF | Mass Air Flow | g/s | 2-250 |
| INTAKE_PRESSURE | Intake Manifold Pressure | PSI | 10-25 |
| TIMING_ADVANCE | Ignition Timing Advance | ° | -10-30 |
| FUEL_PRESSURE | Fuel Pressure | PSI | 40-65 |
| BOOST | Turbo Boost Pressure | PSI | -5-22 |
| OIL_TEMP | Oil Temperature | °F | 80-280 |
| TURBO_SPEED | Turbocharger Speed | RPM | 0-240000 |
| AFR | Air/Fuel Ratio | ratio | 10-16 |
| FUEL_LEVEL | Fuel Level | % | 0-100 |
| BATTERY_VOLTAGE | Battery Voltage | V | 12.0-14.8 |

## ⚙️ Configuration

Edit `.env` file to configure:

### Server Settings
```env
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### Database
```env
DATABASE_URL=sqlite:///./telemetry.db
```

### Security
```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Telemetry
```env
ROLLING_BUFFER_SECONDS=600
SAMPLE_RATE_HZ=10
```

### Email Alerts
```env
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=recipient@example.com
```

### Cloud Sync
```env
ENABLE_CLOUD_SYNC=true
CLOUD_API_URL=https://your-api.com/telemetry
CLOUD_API_KEY=your-api-key
```

### OBD Interface
```env
OBD_PORT=/dev/ttyUSB0
OBD_BAUDRATE=38400
SIMULATION_MODE=true
```

## 🏗️ Architecture

```
┌─────────────────┐
│  Web Dashboard  │ ← HTTP/WebSocket
└────────┬────────┘
         │
┌────────▼────────┐
│   FastAPI App   │
│   (app.py)      │
└─┬──┬──┬──┬──┬──┘
  │  │  │  │  │
  │  │  │  │  └──→ Auth System (auth.py)
  │  │  │  └─────→ Alert Evaluator (alerts.py)
  │  │  └────────→ Cloud Sync (alerts.py)
  │  └───────────→ Database Layer (database.py)
  └──────────────→ HAL (obd_simulator.py)
                        │
              ┌─────────┴─────────┐
              │                   │
         Simulator            Real Hardware
      (Development)         (USB/CAN/Remote)
```

## 🧪 Development

### Running in Development Mode
```bash
python app.py
```

The server will auto-reload on code changes when `DEBUG=true`.

### Testing Scenarios

The simulator supports multiple driving scenarios:
- `idle`: Engine running, stationary
- `cruising`: Highway cruising (60 MPH)
- `acceleration`: Hard acceleration
- `hard_driving`: Performance driving with high boost

## 🐳 Docker Support

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t focus-st-telemetry .
docker run -p 8000:8000 focus-st-telemetry
```

## 📝 API Endpoints

### Authentication
- `POST /api/auth/token` - Get access token
- `GET /api/auth/me` - Get current user info

### Sessions
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{session_id}` - Get session data
- `GET /api/sessions/current/recent` - Get recent data

### Alerts
- `GET /api/alerts` - List alert configurations
- `POST /api/alerts` - Create new alert

### Export
- `POST /api/export` - Export telemetry data

### Diagnostics
- `GET /api/diagnostics/pids` - List available PIDs
- `GET /api/diagnostics/dtc` - Get diagnostic trouble codes

### WebSocket
- `WS /ws/telemetry` - Real-time telemetry stream

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Chart.js for beautiful visualizations
- python-OBD for OBD-II protocol support

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ for Focus ST enthusiasts**
