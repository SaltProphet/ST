#!/usr/bin/env python3
"""
Focus ST Telemetry Gateway - Main Entry Point
Raspberry Pi / ELM327 / WebSocket Edge Gateway
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import uvicorn

from focusst_telemetry.ecu.factory import create_ecu
from focusst_telemetry.gateway.app import TelemetryGateway

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global gateway instance
gateway: TelemetryGateway = None


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for FastAPI app"""
    global gateway
    
    logger.info("=" * 60)
    logger.info("Focus ST Telemetry Gateway - Starting")
    logger.info("High-Density Edge Gateway for 2016 Ford Focus ST")
    logger.info("=" * 60)
    
    # Create ECU with auto-detection
    ecu = await create_ecu(device_path="/dev/rfcomm0", baudrate=38400)
    
    # Create gateway with 20Hz update rate for high-frequency boost monitoring
    gateway = TelemetryGateway(ecu=ecu, update_rate=20)
    
    # Start data streaming
    await gateway.start()
    logger.info("✓ Gateway started - streaming at 20Hz")
    logger.info("✓ WebSocket endpoint: ws://0.0.0.0:8000/ws")
    logger.info("✓ Dashboard: http://0.0.0.0:8000/")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down gateway...")
    await gateway.stop()
    logger.info("✓ Gateway stopped")


def create_app():
    """Create and configure the FastAPI application"""
    from fastapi import FastAPI
    
    # Create gateway's app first (synchronously) 
    # The actual ECU connection will happen in lifespan
    app = FastAPI(
        title="Focus ST Telemetry Gateway",
        description="High-performance telemetry gateway for 2016 Ford Focus ST",
        version="1.0.0",
        lifespan=lifespan
    )
    
    return app


def main():
    """Main entry point"""
    # Get configuration from environment or use defaults
    host = "0.0.0.0"
    port = 8000
    
    logger.info(f"Starting server on {host}:{port}")
    
    # Run with uvicorn
    try:
        # Start the gateway
        asyncio.run(async_main(host, port))
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal. Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


async def async_main(host: str, port: int):
    """Async main to properly initialize gateway before starting server"""
    global gateway
    
    logger.info("=" * 60)
    logger.info("Focus ST Telemetry Gateway - Starting")
    logger.info("High-Density Edge Gateway for 2016 Ford Focus ST")
    logger.info("=" * 60)
    
    # Create ECU with auto-detection
    ecu = await create_ecu(device_path="/dev/rfcomm0", baudrate=38400)
    
    # Create gateway with 20Hz update rate
    gateway = TelemetryGateway(ecu=ecu, update_rate=20)
    
    # Start data streaming
    await gateway.start()
    logger.info("✓ Gateway started - streaming at 20Hz")
    logger.info(f"✓ WebSocket endpoint: ws://{host}:{port}/ws")
    logger.info(f"✓ Dashboard: http://{host}:{port}/")
    logger.info("=" * 60)
    
    # Create uvicorn config
    config = uvicorn.Config(
        gateway.app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    finally:
        logger.info("Shutting down gateway...")
        await gateway.stop()
        logger.info("✓ Gateway stopped")


if __name__ == "__main__":
    main()
