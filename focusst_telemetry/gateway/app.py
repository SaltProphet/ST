"""FastAPI application with WebSocket support"""

import asyncio
import json
import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from ..ecu.base import ECUBase
from ..data.parser import PIDParser
from .broadcaster import Broadcaster

logger = logging.getLogger(__name__)


class TelemetryGateway:
    """FastAPI gateway for telemetry streaming"""
    
    def __init__(self, ecu: ECUBase, update_rate: int = 20):
        self.app = FastAPI(title="Focus ST Telemetry Gateway")
        self.ecu = ecu
        self.update_rate = update_rate
        self.broadcaster = Broadcaster()
        self.parser = PIDParser()
        self._data_task: Optional[asyncio.Task] = None
        
        # Set up templates and static files
        base_path = Path(__file__).parent.parent
        templates_path = base_path / "templates"
        static_path = base_path / "static"
        
        if templates_path.exists():
            self.templates = Jinja2Templates(directory=str(templates_path))
        else:
            self.templates = None
            
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Set up API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """Serve the web dashboard"""
            if self.templates:
                return self.templates.TemplateResponse("index.html", {"request": request})
            return HTMLResponse(content=self._get_fallback_html())
        
        @self.app.get("/api/status")
        async def status():
            """Get gateway status"""
            return {
                "running": self.ecu.running,
                "clients": self.broadcaster.get_client_count(),
                "update_rate": self.update_rate,
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time telemetry streaming"""
            await websocket.accept()
            queue = await self.broadcaster.register()
            
            try:
                while True:
                    # Get data from broadcaster queue
                    data = await queue.get()
                    # Send to client
                    await websocket.send_json(data)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await self.broadcaster.unregister(queue)
                
    async def _data_loop(self):
        """Main data acquisition and broadcasting loop"""
        interval = 1.0 / self.update_rate
        
        while self.ecu.running:
            try:
                # Read raw data from ECU
                raw_data = await self.ecu.read_data()
                
                # Parse and transform data
                parsed_data = self.parser.parse_all(raw_data)
                
                # Broadcast to all clients
                await self.broadcaster.broadcast(parsed_data)
                
                # Sleep until next update
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in data loop: {e}")
                await asyncio.sleep(interval)
                
    async def start(self):
        """Start the gateway and data streaming"""
        await self.ecu.start()
        self._data_task = asyncio.create_task(self._data_loop())
        
    async def stop(self):
        """Stop the gateway and data streaming"""
        await self.ecu.stop()
        if self._data_task:
            self._data_task.cancel()
            try:
                await self._data_task
            except asyncio.CancelledError:
                pass
                
    def _get_fallback_html(self) -> str:
        """Return simple HTML page when templates are not available"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Focus ST Telemetry</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
        }
        h1 { color: #00d4ff; }
        .metric {
            background: #2a2a2a;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #00d4ff;
        }
        .warning {
            border-left-color: #ff4444;
            background: #3a2020;
        }
        .value {
            font-size: 2em;
            font-weight: bold;
        }
        .label {
            color: #aaa;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>🏁 Focus ST Telemetry</h1>
    <div id="status">Connecting...</div>
    <div id="boost" class="metric">
        <div class="label">Boost Pressure</div>
        <div class="value">-- PSI</div>
    </div>
    <div id="oil_temp" class="metric">
        <div class="label">Oil Temperature</div>
        <div class="value">-- °F</div>
    </div>
    <div id="oar" class="metric">
        <div class="label">Oxygen/Air Ratio</div>
        <div class="value">--</div>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${location.host}/ws`);
        
        ws.onopen = () => {
            document.getElementById('status').textContent = '✅ Connected';
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            // Update boost
            const boostDiv = document.getElementById('boost');
            boostDiv.querySelector('.value').textContent = `${data.boost.psi} PSI`;
            boostDiv.className = data.boost.warning ? 'metric warning' : 'metric';
            
            // Update oil temp
            const oilTempDiv = document.getElementById('oil_temp');
            oilTempDiv.querySelector('.value').textContent = `${data.oil_temp.fahrenheit} °F`;
            oilTempDiv.className = data.oil_temp.warning ? 'metric warning' : 'metric';
            
            // Update OAR
            const oarDiv = document.getElementById('oar');
            oarDiv.querySelector('.value').textContent = data.oar.value;
            oarDiv.className = data.oar.warning ? 'metric warning' : 'metric';
        };
        
        ws.onerror = (error) => {
            document.getElementById('status').textContent = '❌ Error';
        };
        
        ws.onclose = () => {
            document.getElementById('status').textContent = '⚠️ Disconnected';
        };
    </script>
</body>
</html>
"""
