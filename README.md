# Focus ST Telemetry Simulation & Gateway

A modular Python application for simulating and capturing telemetry data from a Ford Focus ST vehicle. Supports both mock ECU data generation for development and OBD-II bridge for production use.

## Features

- **Modular Architecture**: Pluggable data sources (Mock ECU or OBD-II Bridge)
- **Mock ECU**: Generates realistic PID data using sine waves with noise for development
- **FastAPI Gateway**: High-performance HTTP/WebSocket server
- **Socket.io Support**: Real-time bi-directional communication at 20Hz for critical PIDs
- **PID-Specific Conversions**: Automatic data conversion (e.g., Boost pressure, Oil temp)
- **Warning System**: Automatic flagging of abnormal values (e.g., OAR deviation)
- **Headless-First Design**: CLI-based management with optional Web UI
- **Configuration-Driven**: TOML/YAML/env-based configuration
- **Web Dashboard**: Optional Jinja2-based UI for real-time monitoring

## Supported PIDs

| PID ID   | Name      | Description              | Unit | Conversion Formula                    |
|----------|-----------|--------------------------|------|---------------------------------------|
| 2204FE   | boost     | Turbo Boost Pressure     | psi  | RawValue × 0.0145 - 14.7             |
| 220546   | oil_temp  | Engine Oil Temperature   | °F   | RawValue × 1.8 + 32                  |
| 2203E8   | oar       | Octane Adjust Ratio      | -    | RawValue (warns if moves from -1.0)  |

## Installation

```bash
# Clone the repository
git clone https://github.com/SaltProphet/ST.git
cd ST

# Install dependencies
pip install -r requirements.txt

# Or install with development dependencies
pip install -e ".[dev]"

# For OBD-II support (optional)
pip install -e ".[obd]"
```

## Configuration

The application uses a `config.toml` file for configuration. You can also use YAML or environment variables.

```toml
[data_source]
# Options: "mock_ecu" or "obd_bridge"
type = "mock_ecu"

[gateway]
host = "0.0.0.0"
port = 8000

[ui]
enabled = true
```

See `config.toml` for full configuration options.

## Usage

### Start the Gateway Server

```bash
# Using default configuration
st-telemetry start

# With custom configuration
st-telemetry --config my-config.toml start

# Custom host and port
st-telemetry start --host 127.0.0.1 --port 8080

# With auto-reload for development
st-telemetry start --reload
```

### View Configuration

```bash
st-telemetry info
```

### Test a Specific PID

```bash
# Read 10 samples from boost PID
st-telemetry test-pid boost

# Custom sample count and interval
st-telemetry test-pid boost --count 20 --interval 0.5
```

### Validate Configuration

```bash
st-telemetry validate-config
```

## Web Dashboard

When the UI is enabled (default), access the web dashboard at:

```
http://localhost:8000
```

The dashboard displays:
- Real-time telemetry data for all configured PIDs
- Connection status
- Raw and converted values
- Update timestamps
- Warning indicators

## API Endpoints

### HTTP Endpoints

- `GET /` - Web dashboard (if UI enabled)
- `GET /health` - Health check endpoint
- `GET /pids` - List all configured PIDs

### WebSocket (Socket.io)

Connect to `/socket.io` for real-time telemetry data:

```javascript
const socket = io('http://localhost:8000');

// Listen for telemetry data
socket.on('telemetry_data', (data) => {
    console.log(data);
});

// Subscribe to specific PID
socket.emit('subscribe', { pid: 'boost' });
```

## Architecture

```
st_telemetry/
├── data_sources/       # Data source implementations
│   ├── base.py        # Abstract base class
│   ├── mock_ecu.py    # Mock ECU with sine wave generation
│   ├── obd_bridge.py  # OBD-II bridge (stub)
│   └── factory.py     # Data source factory
├── gateway/           # FastAPI gateway server
│   └── server.py      # Gateway with Socket.io support
├── ui/                # UI components (placeholder)
├── utils/             # Utility functions
├── config.py          # Configuration management
└── cli.py             # Command-line interface

templates/             # Jinja2 templates
static/               # Static assets (CSS, JS)
config.toml           # Default configuration
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black st_telemetry/
```

### Linting

```bash
ruff check st_telemetry/
```

## Data Source Switching

Switch between mock ECU and OBD-II bridge by modifying `config.toml`:

```toml
[data_source]
type = "obd_bridge"  # or "mock_ecu"

[data_source.obd_bridge]
port = "/dev/ttyUSB0"
baudrate = 38400
protocol = "AUTO"
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
