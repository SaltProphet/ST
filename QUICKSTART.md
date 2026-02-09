# Quick Start Guide

Get up and running with Focus ST Telemetry in 5 minutes!

## Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/SaltProphet/ST.git
cd ST

# Run setup script (Linux/Mac)
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure (Optional)

```bash
# Copy example configuration
cp .env.example .env

# Edit if needed (defaults work fine for testing)
nano .env
```

## Step 3: Start the Server

```bash
python app.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 4: Open Dashboard

Open your browser and go to: **http://localhost:8000**

You'll see real-time telemetry data streaming!

## Step 5: Login (Optional)

For protected features, login with:
- **Username**: `admin`
- **Password**: `admin`

**⚠️ Change these in production!**

## Quick Examples

### View Available PIDs

```bash
python cli.py pids
```

### Export Telemetry Data

```bash
# Get current session ID from the dashboard or:
python cli.py sessions

# Export to CSV
curl -X POST http://localhost:8000/api/export \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "format": "csv"}' > data.csv
```

### Create an Alert

```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Boost",
    "pid": "BOOST",
    "condition": "gt",
    "threshold": 20.0,
    "email_notify": false
  }'
```

### WebSocket Connection (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.pid}: ${data.value} ${data.unit}`);
};
```

## Key Features Demo

### 1. Real-Time Dashboard
- Open http://localhost:8000
- Watch live telemetry updates
- See charts update in real-time

### 2. Interactive API Docs
- Open http://localhost:8000/docs
- Try out API endpoints
- See request/response examples

### 3. CLI Tools
```bash
# List all PIDs
python cli.py pids

# Test simulator
python cli.py test --duration 10

# List sessions
python cli.py sessions

# Create user
python cli.py create-user testuser test@example.com password123 --role viewer
```

### 4. Run Tests
```bash
pytest test_telemetry.py -v
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [API.md](API.md) for API reference
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Configure email alerts in `.env`
- Set up cloud sync if needed

## Troubleshooting

### Port Already in Use
Change the port in `.env`:
```env
PORT=8001
```

### Dependencies Installation Fails
Ensure Python 3.12+ is installed:
```bash
python3 --version
```

### Database Errors
Delete the database and restart:
```bash
rm telemetry.db
python app.py
```

## Getting Help

- Check [README.md](README.md) for detailed documentation
- Review [API.md](API.md) for API details
- Open an issue on GitHub for bugs

**Enjoy your Focus ST Telemetry System! 🏎️**
