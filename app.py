"""Main FastAPI application with WebSocket gateway and REST API."""
import asyncio
import json
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, Depends, 
    HTTPException, status, Request, Form
)
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import uvicorn

from config import settings
from database import db
from obd_simulator import HardwareAbstractionLayer
from alerts import alert_evaluator, cloud_sync
from auth import (
    Token, User, authenticate_user, create_access_token,
    get_current_active_user, require_viewer, require_operator, require_admin,
    get_password_hash
)


# Initialize FastAPI app
app = FastAPI(
    title="Focus ST Telemetry Simulation & Gateway",
    description="Advanced telemetry system with real-time monitoring, alerts, and cloud sync",
    version="1.0.0"
)

# Templates for web dashboard
templates = Jinja2Templates(directory="templates")

# Global state
active_connections: List[WebSocket] = []
current_session_id: Optional[str] = None
hal: Optional[HardwareAbstractionLayer] = None


# Pydantic models for API
class SessionCreate(BaseModel):
    vehicle_info: Optional[Dict[str, Any]] = None


class AlertCreate(BaseModel):
    name: str
    pid: str
    condition: str  # gt, gte, lt, lte, eq, neq
    threshold: float
    email_notify: bool = False


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "viewer"


class ExportRequest(BaseModel):
    session_id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    format: str = "csv"  # csv or json


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    global hal
    
    # Connect to database
    await db.connect()
    
    # Load alert configurations
    await alert_evaluator.load_alerts()
    
    # Initialize hardware abstraction layer
    hal = HardwareAbstractionLayer(
        interface_type="simulator" if settings.simulation_mode else "usb"
    )
    await hal.connect()
    
    # Start cloud sync worker
    if settings.enable_cloud_sync:
        asyncio.create_task(cloud_sync.worker())
    
    # Start telemetry streaming
    asyncio.create_task(telemetry_stream_worker())
    
    # Create default admin user if none exists
    admin_user = await db.get_user("admin")
    if not admin_user:
        await db.create_user(
            username="admin",
            email="admin@focusst.local",
            hashed_password=get_password_hash("admin"),
            role="admin"
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global current_session_id
    
    if current_session_id:
        await db.end_session(current_session_id)
    
    await db.close()
    
    if hal:
        await hal.disconnect()


async def telemetry_stream_worker():
    """Background worker to stream telemetry data."""
    global current_session_id
    
    # Create a new session
    import uuid
    current_session_id = str(uuid.uuid4())
    await db.create_session(current_session_id, {"vehicle": "Focus ST"})
    
    # Stream telemetry data
    async for data_batch in hal.stream(rate_hz=settings.sample_rate_hz):
        for data_point in data_batch:
            if not data_point:
                continue
            
            # Store in database
            await db.insert_telemetry(
                current_session_id,
                data_point["pid"],
                data_point["value"],
                data_point["unit"]
            )
            
            # Evaluate alerts
            triggered_alerts = await alert_evaluator.evaluate(
                current_session_id,
                data_point["pid"],
                data_point["value"]
            )
            
            # Add alerts to data point
            data_point["alerts"] = triggered_alerts
            
            # Cloud sync
            if settings.enable_cloud_sync:
                await cloud_sync.push(data_point)
            
            # Broadcast to WebSocket clients
            await manager.broadcast(data_point)


# WebSocket endpoint for real-time telemetry
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Authentication endpoints
@app.post("/api/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 login endpoint."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return current_user


# User management endpoints
@app.post("/api/users", dependencies=[Depends(require_admin)])
async def create_user(user: UserCreate):
    """Create a new user (admin only)."""
    hashed_password = get_password_hash(user.password)
    user_id = await db.create_user(
        user.username,
        user.email,
        hashed_password,
        user.role
    )
    return {"id": user_id, "username": user.username, "role": user.role}


# Session management endpoints
@app.get("/api/sessions", dependencies=[Depends(require_viewer)])
async def list_sessions(limit: int = 100):
    """List all telemetry sessions."""
    sessions = await db.list_sessions(limit)
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}", dependencies=[Depends(require_viewer)])
async def get_session(
    session_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Get telemetry data for a specific session."""
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None
    
    data = await db.get_session_data(session_id, start_dt, end_dt)
    return {"session_id": session_id, "data": data}


@app.get("/api/sessions/current/recent", dependencies=[Depends(require_viewer)])
async def get_recent_data(seconds: int = 60):
    """Get recent telemetry data from current session."""
    if not current_session_id:
        raise HTTPException(status_code=404, detail="No active session")
    
    data = await db.get_recent_telemetry(current_session_id, seconds)
    return {"session_id": current_session_id, "data": data}


# Alert management endpoints
@app.get("/api/alerts", dependencies=[Depends(require_viewer)])
async def list_alerts():
    """List all alert configurations."""
    alerts = await db.get_alerts(enabled_only=False)
    return {"alerts": alerts}


@app.post("/api/alerts", dependencies=[Depends(require_operator)])
async def create_alert(alert: AlertCreate):
    """Create a new alert configuration."""
    alert_id = await db.create_alert(
        alert.name,
        alert.pid,
        alert.condition,
        alert.threshold,
        alert.email_notify
    )
    await alert_evaluator.load_alerts()  # Reload alerts
    return {"id": alert_id, "name": alert.name}


# Export endpoints
@app.post("/api/export", dependencies=[Depends(require_viewer)])
async def export_data(request: ExportRequest):
    """Export telemetry data to CSV or JSON."""
    start_dt = datetime.fromisoformat(request.start_time) if request.start_time else None
    end_dt = datetime.fromisoformat(request.end_time) if request.end_time else None
    
    data = await db.get_session_data(request.session_id, start_dt, end_dt)
    
    if request.format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={request.session_id}.csv"}
        )
    else:
        return JSONResponse(content={"session_id": request.session_id, "data": data})


# Replay mode endpoint
@app.post("/api/replay/{session_id}", dependencies=[Depends(require_operator)])
async def start_replay(session_id: str, speed: float = 1.0):
    """Start replay mode for a recorded session."""
    # This would need implementation to actually replay through WebSocket
    return {"status": "replay_started", "session_id": session_id, "speed": speed}


# Diagnostic endpoints
@app.get("/api/diagnostics/pids")
async def list_pids():
    """List all available PIDs."""
    from obd_simulator import OBDSimulator
    simulator = OBDSimulator()
    return {"pids": list(simulator.PIDS.keys())}


@app.get("/api/diagnostics/dtc", dependencies=[Depends(require_operator)])
async def get_dtc_codes():
    """Get diagnostic trouble codes."""
    if hal and hasattr(hal.interface, 'get_dtc_codes'):
        codes = hal.interface.get_dtc_codes()
        return {"dtc_codes": codes}
    return {"dtc_codes": []}


# Web dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Focus ST Telemetry Dashboard"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "session_id": current_session_id,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
