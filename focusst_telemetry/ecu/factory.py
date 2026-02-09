"""ECU Factory - Auto-detects hardware and falls back to simulation"""

import logging
import os
from typing import Union

from .base import ECUBase
from .obd_bridge import OBDBridge
from .mock import MockECU

logger = logging.getLogger(__name__)


async def create_ecu(device_path: str = "/dev/rfcomm0", baudrate: int = 38400) -> ECUBase:
    """Create ECU instance with automatic hardware detection
    
    Attempts to connect to ELM327 hardware. If hardware is not detected,
    automatically falls back to MockECU for development/testing.
    
    Args:
        device_path: Path to serial device (default: /dev/rfcomm0)
        baudrate: Serial baudrate (default: 38400)
        
    Returns:
        ECUBase: Either OBDBridge (if hardware detected) or MockECU (fallback)
    """
    logger.info("Attempting to detect ELM327 hardware...")
    
    # Try to create OBD bridge
    obd = OBDBridge(device_path=device_path, baudrate=baudrate)
    
    # Attempt connection
    try:
        connected = await obd.connect()
        if connected:
            logger.info("✓ ELM327 hardware detected and connected")
            return obd
    except Exception as e:
        logger.warning(f"Hardware detection failed: {e}")
    
    # Hardware not available - fall back to mock
    logger.info("No ELM327 hardware detected. Using MockECU simulation mode.")
    return MockECU(update_rate=20)
