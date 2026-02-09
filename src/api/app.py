"""FastAPI application with WebSocket telemetry streaming."""
import asyncio
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

from ..config import settings
from ..ecu.factory import ECUFactory
from ..ecu.base import ECUInterface


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Real-time vehicle telemetry dashboard for Focus ST"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global ECU instance
ecu: ECUInterface = None
active_connections: Set[WebSocket] = set()


@app.on_event("startup")
async def startup_event():
    """Initialize ECU connection on startup."""
    global ecu
    ecu = ECUFactory.create_ecu(
        ecu_type=settings.ecu_type,
        port=settings.obd_port,
        baudrate=settings.obd_baudrate
    )
    
    # Attempt to connect
    connected = await ecu.connect()
    if connected:
        print(f"✓ ECU connected ({settings.ecu_type} mode)")
    else:
        print(f"✗ Failed to connect to ECU ({settings.ecu_type} mode)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup ECU connection on shutdown."""
    global ecu
    if ecu:
        await ecu.disconnect()
        print("ECU disconnected")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": settings.app_title,
            "ecu_type": settings.ecu_type
        }
    )


@app.get("/api/status")
async def get_status():
    """Get ECU connection status."""
    return {
        "connected": ecu.is_connected() if ecu else False,
        "ecu_type": settings.ecu_type,
        "telemetry_interval": settings.telemetry_interval
    }


@app.get("/api/telemetry")
async def get_telemetry():
    """Get current telemetry data (single snapshot)."""
    if not ecu or not ecu.is_connected():
        return {"error": "ECU not connected"}
    
    try:
        data = await ecu.get_telemetry()
        return data
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming."""
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        # Send initial connection status
        await websocket.send_json({
            "type": "status",
            "connected": ecu.is_connected() if ecu else False,
            "ecu_type": settings.ecu_type
        })
        
        # Stream telemetry data
        while True:
            if ecu and ecu.is_connected():
                try:
                    # Get telemetry data
                    data = await ecu.get_telemetry()
                    
                    # Send to client
                    await websocket.send_json({
                        "type": "telemetry",
                        "data": data
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            
            # Wait before next update
            await asyncio.sleep(settings.telemetry_interval)
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        active_connections.remove(websocket)


@app.post("/api/reconnect")
async def reconnect_ecu():
    """Attempt to reconnect to ECU."""
    global ecu
    
    if ecu:
        await ecu.disconnect()
    
    ecu = ECUFactory.create_ecu(
        ecu_type=settings.ecu_type,
        port=settings.obd_port,
        baudrate=settings.obd_baudrate
    )
    
    connected = await ecu.connect()
    
    return {
        "success": connected,
        "ecu_type": settings.ecu_type,
        "connected": connected
    }
