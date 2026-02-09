# 🏁 Focus ST Telemetry Simulation & Gateway

A real-time telemetry gateway and dashboard for Ford Focus ST, supporting both development (Mock ECU) and production (OBD-II Bluetooth Bridge) data sources.

## Features

- 🔌 **Pluggable Interface**: Switch between mock ECU and real OBD-II bridge via config/CLI
- 🔄 **Real-time Streaming**: 20Hz+ updates via WebSocket
- 🛡️ **Alert Flags**: Automatic warnings for out-of-range values
- 🖥️ **Headless-First**: CLI-manageable, with optional web dashboard
- 👩‍🔧 **Easy Extension**: Modular design for adding PIDs, outputs, or features

## Tech Stack

- **Python 3.11+** (asyncio, typing)
- **FastAPI** for gateway API
- **WebSockets** for real-time streaming
- **Jinja2** for HTML templates
- **TOML** for configuration

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/SaltProphet/ST.git
cd ST

# Install dependencies
pip install -r requirements.txt
```

### Running the Gateway

```bash
# Run with mock ECU (development)
python main.py --data_source mock_ecu

# Run with OBD-II bridge (production - stub)
python main.py --data_source obd_bridge

# Custom host and port
python main.py --host 0.0.0.0 --port 8080

# Using config file
python main.py --config config.toml
```

### Accessing the Dashboard

Once running, open your browser to:
- **Dashboard**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws
- **API Status**: http://localhost:8000/api/status

## Architecture

### Project Structure

```
focusst_telemetry/
├── main.py                # Entry point with CLI
├── config.py              # Configuration handling
├── ecu/
│   ├── base.py            # Abstract base class for ECU sources
│   ├── mock.py            # Mock ECU simulation
│   └── obd_bridge.py      # OBD-II bridge (stub)
├── gateway/
│   ├── app.py             # FastAPI application
│   └── broadcaster.py     # WebSocket broadcaster
├── data/
│   └── parser.py          # PID parsing and transformations
├── templates/
│   └── index.html         # Web dashboard
└── static/                # Static assets (optional)
```

### Monitored PIDs

| PID | Name | Raw Value | Conversion | Warning Threshold |
|-----|------|-----------|------------|-------------------|
| 0x2204FE | Boost Pressure | Raw ADC | `PSI = raw * 0.0145 - 14.7` | > 20 PSI |
| 0x220546 | Oil Temperature | Degrees F | Direct | < 160°F or > 240°F |
| 0x2203E8 | O₂/Air Ratio | Ratio | Direct | Not near -1.0 (±0.3) |

## Configuration

### Via TOML File

Create `config.toml`:

```toml
data_source = "mock_ecu"  # or "obd_bridge"
host = "0.0.0.0"
port = 8000
update_rate = 20  # Hz
log_level = "INFO"
```

### Via Environment Variables

```bash
export DATA_SOURCE=mock_ecu
export HOST=0.0.0.0
export PORT=8000
export UPDATE_RATE=20
export LOG_LEVEL=INFO
python main.py
```

### Via CLI Arguments

```bash
python main.py \
  --data_source mock_ecu \
  --host 0.0.0.0 \
  --port 8000 \
  --update_rate 20 \
  --log_level INFO
```

## Development

### Mock ECU

The Mock ECU simulates realistic telemetry data:

- **Boost**: Sine wave cycling between vacuum and boost with noise
- **Oil Temp**: Slowly varying temperature (180-220°F range)
- **OAR**: Oscillates around -1.0 with occasional disturbances

Perfect for development and testing without real hardware.

### Adding New PIDs

1. Add raw data generation in `ecu/mock.py` or `ecu/obd_bridge.py`
2. Add parsing logic in `data/parser.py`
3. Update web dashboard to display new data

Example:

```python
# In parser.py
@staticmethod
def parse_coolant_temp(raw_value: float) -> Tuple[float, bool]:
    temp_f = raw_value
    is_warning = temp_f > 220.0
    return temp_f, is_warning
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
};
```

### Data Format

```json
{
  "timestamp": 1707457200.123,
  "boost": {
    "raw": 1214.5,
    "psi": 2.89,
    "warning": false
  },
  "oil_temp": {
    "raw": 205.3,
    "fahrenheit": 205.3,
    "warning": false
  },
  "oar": {
    "value": -0.985,
    "warning": false
  }
}
```

## Extension Ideas

- 📊 Add more PIDs (coolant temp, AFR, timing, etc.)
- 💾 Persist data to database or file
- 📱 Build mobile-friendly responsive UI
- 🔌 Add CAN/ISO-TP support for other vehicles
- 📈 Add historical data visualization
- 🚨 Configurable alert thresholds
- 📤 Export data to CSV/JSON

## Production OBD-II Bridge

The OBD-II bridge is currently a stub. To implement:

1. Install Bluetooth library (e.g., `bleak`, `pybluez`)
2. Implement connection in `ecu/obd_bridge.py`
3. Add ISO-TP/CAN protocol handling
4. Map Ford-specific PIDs to OBD-II requests

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

---

**Built for extensibility, rapid prototyping, and production deployment.**
