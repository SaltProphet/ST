# Focus ST Telemetry Edge Gateway

High-performance, asynchronous telemetry gateway for the 2016 Ford Focus ST. This system bypasses commercial app latency by establishing a direct Bluetooth-to-WebSocket bridge for real-time ECU monitoring.

## 🏎️ Features

### Hardware Integration
- **ELM327 Bluetooth Support**: Direct connection via Serial Port Profile (SPP) at `/dev/rfcomm0`
- **Ford-Specific PIDs**: Native support for Focus ST extended PIDs
- **Intelligent Polling**: 20Hz high-frequency boost monitoring, 2Hz low-frequency for oil temp/OAR
- **Keep-Alive**: Automatic keep-alive packets prevent ELM327 timeout
- **Auto-Detection**: Seamless fallback to MockECU when hardware not detected

### Backend Architecture
- **FastAPI**: Modern async web framework with automatic OpenAPI docs
- **uvicorn**: High-performance ASGI server
- **asyncio**: Concurrent OBD-II polling and WebSocket broadcasting
- **WebSocket Streaming**: Real-time JSON telemetry packets at 20Hz
- **Zero-Latency**: Direct ECU-to-browser pipeline without middleware overhead

### Frontend Design
- **Mobile-First**: Optimized for in-car Raspberry Pi touchscreen displays
- **Dark Mode**: Pure black (#121212) background reduces screen glare during night driving
- **Zero-CDN**: 100% local-only, no external dependencies
- **CSS Grid**: Responsive layout adapts from mobile to desktop
- **Canvas Gauge**: Hardware-accelerated boost pressure gauge with color-coded zones
- **Wake Lock API**: Prevents screen dimming during active driving sessions

### Monitored Parameters

| PID | Parameter | Formula | Update Rate | Warning Threshold |
|-----|-----------|---------|-------------|-------------------|
| **2204FE** | Turbo Boost Pressure | ((A×256)+B)×0.0145 - 14.7 PSI | 20Hz | > 20 PSI |
| **220546** | Oil Temperature | Custom scaling to °F | 2Hz | < 160°F or > 240°F |
| **2203E8** | Octane Adjusted Ratio | Direct ratio | 2Hz | > -0.7 (drift alert) |

## 🛠️ Hardware Requirements

### Raspberry Pi Setup
- Raspberry Pi 3/4/5 (tested on Pi 4)
- Raspbian/Raspberry Pi OS (Bookworm or newer)
- Python 3.11+

### ELM327 Adapter
- Bluetooth ELM327 OBD-II adapter (v1.5 or v2.1 recommended)
- Paired via Bluetooth SPP at `/dev/rfcomm0`
- Supports ISO 15765-4 CAN (500 kbaud) for Ford vehicles

### 2016 Ford Focus ST
- OBD-II port located under driver's side dash
- CAN bus support (standard on all 2016+ models)
- Extended Ford PIDs enabled (standard on Focus ST)

## 📦 Installation

### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Bluetooth tools
sudo apt install bluetooth bluez bluez-tools rfkill -y
```

### 2. Bluetooth ELM327 Pairing

```bash
# Start Bluetooth service
sudo systemctl start bluetooth
sudo systemctl enable bluetooth

# Pair ELM327 adapter
bluetoothctl
> scan on
# Wait for ELM327 to appear (usually named "OBDII" or "ELM327")
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> exit

# Bind to serial port
sudo rfcomm bind 0 XX:XX:XX:XX:XX:XX
```

### 3. Python Environment

```bash
# Clone repository
git clone https://github.com/SaltProphet/ST.git
cd ST

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Usage

### Start Gateway

```bash
python run_gateway.py
```

The gateway will:
1. Attempt to detect ELM327 hardware at `/dev/rfcomm0`
2. Fall back to MockECU simulation if hardware not found
3. Start streaming telemetry at 20Hz
4. Serve web dashboard on `http://0.0.0.0:8000`

### Access Dashboard

Open a browser and navigate to:
- **Desktop**: `http://raspberry-pi.local:8000` or `http://192.168.1.xxx:8000`
- **Mobile**: Same URL from phone/tablet on same network

### WebSocket Connection

Connect directly to the WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://192.168.1.xxx:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Boost: ${data.boost.psi} PSI`);
    console.log(`Oil Temp: ${data.oil_temp.fahrenheit} °F`);
    console.log(`OAR: ${data.oar.value}`);
};
```

### API Endpoints

- `GET /` - Web dashboard
- `GET /api/status` - Gateway status and statistics
- `WS /ws` - WebSocket telemetry stream

## 🧪 Testing

### Run Unit Tests

```bash
python test_gateway.py
```

Tests verify:
- ✅ Boost formula: ((A×256)+B)×0.0145 - 14.7
- ✅ OAR warning threshold: > -0.7
- ✅ Mock ECU realistic sensor noise
- ✅ Hardware auto-detection and fallback

### Development Mode

Use MockECU for development without hardware:

```bash
# MockECU automatically activates when /dev/rfcomm0 not found
python run_gateway.py
```

## 📊 Dashboard Features

### Boost Gauge
- Real-time Canvas API needle gauge
- Color-coded zones:
  - 🟢 Green: < 15 PSI (safe)
  - 🟡 Yellow: 15-20 PSI (moderate)
  - 🔴 Red: > 20 PSI (high boost warning)
- Zero-latency updates at 20Hz

### Warning System
- **Visual Alerts**: Cards pulse red when thresholds exceeded
- **Boost**: > 20 PSI
- **Oil Temp**: < 160°F or > 240°F  
- **OAR**: > -0.7 (indicates lean condition)

### Wake Lock
- Automatically requests screen wake lock on first user interaction
- Prevents screen dimming during driving
- Re-acquires lock when page becomes visible

## 🔧 Configuration

### Serial Port

Edit `run_gateway.py` to change default port:

```python
ecu = await create_ecu(device_path="/dev/ttyUSB0", baudrate=38400)
```

### Update Rate

Change polling frequency:

```python
gateway = TelemetryGateway(ecu=ecu, update_rate=10)  # 10Hz instead of 20Hz
```

### Server Binding

Modify host/port in `run_gateway.py`:

```python
host = "127.0.0.1"  # Localhost only
port = 5000
```

## 🐛 Troubleshooting

### ELM327 Not Detected

```bash
# Check if device exists
ls -la /dev/rfcomm*

# Manually bind Bluetooth device
sudo rfcomm bind 0 XX:XX:XX:XX:XX:XX

# Test connection
screen /dev/rfcomm0 38400
# Type: ATZ (should respond with "ELM327 v1.5")
```

### Permission Denied

```bash
# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect
```

### Bluetooth Connection Drops

```bash
# Increase Bluetooth timeout
sudo nano /etc/bluetooth/main.conf
# Set: ConnectionAttemptTimeout = 60
sudo systemctl restart bluetooth
```

## 📈 Performance

- **CPU Usage**: ~5-10% on Raspberry Pi 4 (MockECU), ~15-20% with real hardware
- **Memory**: ~50MB resident
- **Latency**: <50ms ECU-to-browser with local network
- **Update Rate**: Stable 20Hz for boost, 2Hz for oil/OAR

## 🔒 Security Notes

- Gateway binds to `0.0.0.0` by default (all interfaces)
- For production, bind to specific interface or add authentication
- Consider firewall rules to restrict access
- Wake Lock API requires user interaction (security feature)

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- FastAPI for the excellent async web framework
- pyserial for robust serial communication
- Focus ST community for PID documentation

## 📧 Support

For issues or questions:
- Open a GitHub issue
- Check existing documentation
- Review test output for diagnostic info

---

**Built for Focus ST enthusiasts who demand real-time telemetry without compromise.**
