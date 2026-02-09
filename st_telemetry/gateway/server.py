"""FastAPI server with Socket.io WebSocket support."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from st_telemetry.config import Config
from st_telemetry.data_sources.base import DataPoint, DataSource
from st_telemetry.data_sources.factory import create_data_source

logger = logging.getLogger(__name__)


class TelemetryGateway:
    """Gateway server that ingests data and broadcasts via WebSockets."""

    def __init__(self, config: Config):
        self.config = config
        self.data_source: Optional[DataSource] = None
        
        # Create Socket.IO server
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=config.gateway.socketio_logger,
            engineio_logger=config.gateway.socketio_engineio_logger,
        )
        
        # Create FastAPI app
        self.app = FastAPI(title="Focus ST Telemetry Gateway", version="0.1.0")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config.gateway.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup templates if UI is enabled
        self.templates = None
        if config.ui.enabled:
            templates_path = Path(config.ui.templates_dir)
            if templates_path.exists():
                self.templates = Jinja2Templates(directory=str(templates_path))
                # Mount static files
                static_path = Path(config.ui.static_dir)
                if static_path.exists():
                    self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_handlers()
        
        # Wrap FastAPI app with Socket.IO
        self.asgi_app = socketio.ASGIApp(self.sio, self.app)
        
        # Track connected clients
        self.connected_clients = set()

    def _setup_routes(self):
        """Setup HTTP routes."""
        
        @self.app.get("/")
        async def index(request: Request):
            """Serve the dashboard UI."""
            if self.templates and self.config.ui.enabled:
                return self.templates.TemplateResponse(
                    "index.html",
                    {
                        "request": request,
                        "title": self.config.ui.title,
                        "pids": self.config.get_pids(),
                    },
                )
            return {"message": "Focus ST Telemetry Gateway", "version": "0.1.0"}

        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "streaming": self.data_source.is_streaming() if self.data_source else False,
                "data_source": self.config.data_source.type,
            }

        @self.app.get("/pids")
        async def list_pids():
            """List all configured PIDs."""
            return {
                "pids": [
                    {
                        "id": pid.id,
                        "name": pid.name,
                        "description": pid.description,
                        "unit": pid.unit,
                        "update_rate_hz": pid.update_rate_hz,
                    }
                    for pid in self.config.get_pids()
                ]
            }

    def _setup_socketio_handlers(self):
        """Setup Socket.IO event handlers."""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            logger.info(f"Client connected: {sid}")
            self.connected_clients.add(sid)
            await self.sio.emit("connected", {"status": "connected"}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            logger.info(f"Client disconnected: {sid}")
            self.connected_clients.discard(sid)

        @self.sio.event
        async def subscribe(sid, data):
            """Handle subscription requests."""
            pid_name = data.get("pid")
            logger.info(f"Client {sid} subscribed to {pid_name}")
            # Join a room for this PID
            await self.sio.enter_room(sid, f"pid_{pid_name}")
            await self.sio.emit("subscribed", {"pid": pid_name}, room=sid)

        @self.sio.event
        async def unsubscribe(sid, data):
            """Handle unsubscription requests."""
            pid_name = data.get("pid")
            logger.info(f"Client {sid} unsubscribed from {pid_name}")
            # Leave the room for this PID
            await self.sio.leave_room(sid, f"pid_{pid_name}")
            await self.sio.emit("unsubscribed", {"pid": pid_name}, room=sid)

    async def _broadcast_data_point(self, data_point: DataPoint):
        """Broadcast a data point to all subscribed clients."""
        # Broadcast to all clients in the PID room
        room = f"pid_{data_point.pid_name}"
        await self.sio.emit("telemetry_data", data_point.to_dict(), room=room)
        
        # Also broadcast to general room for dashboard
        await self.sio.emit("telemetry_data", data_point.to_dict())

    async def initialize(self):
        """Initialize the gateway and data source."""
        logger.info("Initializing Telemetry Gateway")
        
        # Create and initialize data source
        self.data_source = create_data_source(self.config)
        await self.data_source.initialize()
        
        # Register callbacks for all PIDs
        for pid in self.config.get_pids():
            self.data_source.register_callback(pid.name, self._broadcast_data_point)

    async def start(self):
        """Start streaming data."""
        if not self.data_source:
            raise RuntimeError("Gateway not initialized")
        
        logger.info("Starting data streaming")
        await self.data_source.start_streaming()

    async def stop(self):
        """Stop streaming data."""
        if self.data_source:
            logger.info("Stopping data streaming")
            await self.data_source.stop_streaming()

    async def shutdown(self):
        """Shutdown the gateway."""
        logger.info("Shutting down Telemetry Gateway")
        await self.stop()
        if self.data_source:
            await self.data_source.shutdown()


def create_gateway(config: Config) -> TelemetryGateway:
    """Create a gateway instance."""
    return TelemetryGateway(config)
