"""Main entry point for the Focus ST Telemetry Dashboard."""
import uvicorn
from src.config import settings


if __name__ == "__main__":
    print(f"Starting {settings.app_title} v{settings.app_version}")
    print(f"ECU Mode: {settings.ecu_type.upper()}")
    print(f"Server: http://{settings.host}:{settings.port}")
    print("-" * 50)
    
    uvicorn.run(
        "src.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
