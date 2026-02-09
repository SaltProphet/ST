# 🏎️ Focus ST Telemetry Simulation & Gateway

A high-density vehicle telemetry dashboard for Ford Focus ST that supports both development (Mock ECU) and production (OBD-II Bluetooth bridge) environments.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![WebSockets](https://img.shields.io/badge/WebSockets-Real--time-orange.svg)

## 🎯 Features

- **Dual ECU Support**: Seamlessly switch between Mock ECU (development) and OBD-II (production)
- **Real-time Streaming**: WebSocket-based telemetry updates at 10Hz (configurable)
- **High-Density Dashboard**: Monitor 16+ vehicle parameters simultaneously
- **Focus ST Optimized**: Tailored for turbocharged EcoBoost metrics (boost pressure, AFR, temperatures)
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Low Latency**: Sub-100ms update latency for critical metrics

## 📊 Monitored Parameters

### Primary Gauges
- **RPM** (Engine Speed)
- **Speed** (Vehicle Speed)
- **Boost Pressure** (Turbocharger boost)

### Engine Metrics
- Engine Load (%)
- Throttle Position (%)
- Timing Advance (°)
- Air/Fuel Ratio

### Temperatures
- Coolant Temperature
- Oil Temperature
- Intake Air Temperature
- Manifold Pressure

### Fuel & Electrical
- Fuel Level (%)
- Fuel Pressure (PSI)
- Instant MPG
- Battery Voltage

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SaltProphet/ST.git
   cd ST
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env to configure ECU type and settings
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Open dashboard**
   ```
   Navigate to: http://localhost:8000
   ```

## ⚙️ Configuration

Configuration is managed through environment variables (`.env` file or system environment).

### ECU Modes

#### Mock ECU (Development)
```bash
ECU_TYPE=mock
```
- Simulates realistic Focus ST driving scenarios
- Includes full driving cycle: idle → acceleration → cruise → deceleration
- No hardware required
- Perfect for development and testing

#### OBD-II (Production)
```bash
ECU_TYPE=obd2
OBD_PORT=/dev/ttyUSB0    # Leave empty for auto-detection
OBD_BAUDRATE=38400
```
- Connects to real ECU via OBD-II Bluetooth/USB adapter
- Supports ELM327-compatible adapters
- Automatically queries supported PIDs

### Performance Tuning

```bash
# Update rate (Hz)
TELEMETRY_INTERVAL=0.1   # 10 Hz (default)
TELEMETRY_INTERVAL=0.05  # 20 Hz (higher frequency)

# Server configuration
HOST=0.0.0.0
PORT=8000
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Dashboard UI (Jinja2 + HTML5 + CSS3)             │    │
│  │  - Real-time gauges                                │    │
│  │  - WebSocket client                                │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │ WebSocket (ws://)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              FastAPI Server (Python)                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  API Routes                                        │    │
│  │  - /               → Dashboard HTML                │    │
│  │  - /ws/telemetry   → WebSocket stream             │    │
│  │  - /api/status     → ECU status                    │    │
│  │  - /api/reconnect  → Manual reconnection           │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ECU Factory (Strategy Pattern)                   │    │
│  │  - Creates appropriate ECU instance                │    │
│  └─────────┬──────────────────────┬────────────────────┘    │
└────────────┼──────────────────────┼─────────────────────────┘
             │                      │
   ┌─────────▼─────────┐  ┌────────▼──────────┐
   │   Mock ECU       │  │  OBD-II Bridge    │
   │                   │  │                   │
   │ - Simulates       │  │ - python-obd      │
   │   telemetry       │  │ - ELM327          │
   │ - Driving cycles  │  │ - Real ECU        │
   └───────────────────┘  └─────────┬─────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  Bluetooth/USB    │
                          │  OBD-II Adapter   │
                          │  (ELM327)         │
                          └─────────┬─────────┘
                                    │
                          ┌─────────▼─────────┐
                          │   Vehicle ECU     │
                          │  (Focus ST)       │
                          └───────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **WebSockets**: Real-time bidirectional communication
- **Templates**: Jinja2
- **OBD-II**: python-obd library
- **Async**: asyncio for concurrent operations
- **Configuration**: pydantic-settings

## 📱 Dashboard Features

### Visual Indicators
- **Connection Status**: Real-time ECU connection indicator
- **Warning States**: Automatic highlighting of critical values
  - High coolant temp (>220°F)
  - High oil temp (>280°F)
  - Voltage anomalies (<12V or >15V)
  - Excessive boost (>22 PSI)

### Real-time Updates
- **10Hz default update rate** (100ms refresh)
- **Sub-100ms latency** from ECU to browser
- **Update rate monitor** shows actual Hz

### Responsive Design
- Adapts to desktop, tablet, and mobile screens
- Touch-friendly controls
- High-contrast, motorsport-inspired theme

## 🔧 Development

### Project Structure
```
ST/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py         # FastAPI application
│   ├── ecu/
│   │   ├── __init__.py
│   │   ├── base.py        # ECU interface
│   │   ├── mock_ecu.py    # Mock ECU implementation
│   │   ├── obd_ecu.py     # OBD-II implementation
│   │   └── factory.py     # ECU factory
│   └── config.py          # Configuration management
├── static/
│   ├── css/
│   │   └── style.css      # Dashboard styling
│   └── js/
│       └── telemetry.js   # WebSocket client
└── templates/
    └── index.html         # Dashboard HTML
```

### Running in Development Mode
```bash
python main.py
```
The server will auto-reload on code changes.

### Testing with Mock ECU
```bash
export ECU_TYPE=mock
python main.py
```

### Testing with Real OBD-II
```bash
export ECU_TYPE=obd2
export OBD_PORT=/dev/ttyUSB0  # or leave empty for auto-detect
python main.py
```

## 🔌 Hardware Requirements (for OBD-II mode)

- **OBD-II Adapter**: ELM327-compatible Bluetooth or USB adapter
- **Vehicle**: OBD-II compliant (2001+ for US vehicles)
- **Recommended**: WiFi or Bluetooth OBD-II adapter for wireless connection

### Tested Adapters
- Generic ELM327 Bluetooth adapters
- BAFX Products Bluetooth OBD-II Scanner
- OBDLink MX+ Bluetooth

## 📝 API Reference

### REST Endpoints

#### GET /
Returns the dashboard HTML page.

#### GET /api/status
Returns ECU connection status.
```json
{
  "connected": true,
  "ecu_type": "mock",
  "telemetry_interval": 0.1
}
```

#### GET /api/telemetry
Returns a single telemetry snapshot.

#### POST /api/reconnect
Attempts to reconnect to ECU.

### WebSocket Endpoint

#### WS /ws/telemetry
Real-time telemetry streaming.

**Message Types:**
```json
{
  "type": "status",
  "connected": true,
  "ecu_type": "mock"
}
```

```json
{
  "type": "telemetry",
  "data": {
    "rpm": 3500,
    "speed": 65,
    "boost_pressure": 15.5,
    ...
  }
}
```

```json
{
  "type": "error",
  "message": "Connection lost"
}
```

## 🐛 Troubleshooting

### "ECU not connected" error
- **Mock mode**: Should auto-connect. Check logs for errors.
- **OBD-II mode**: 
  - Verify adapter is plugged in and powered
  - Check correct port in configuration
  - Ensure vehicle ignition is ON
  - Try auto-detection by leaving OBD_PORT empty

### Slow updates / lag
- Reduce `TELEMETRY_INTERVAL` for faster updates
- Check network latency (for remote access)
- Verify ECU adapter communication speed

### WebSocket disconnects frequently
- Check firewall settings
- Verify stable connection to vehicle ECU
- Review server logs for errors

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI**: Modern, fast web framework
- **python-obd**: OBD-II communication library
- **Focus ST Community**: For inspiration and support

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for the Focus ST community**
