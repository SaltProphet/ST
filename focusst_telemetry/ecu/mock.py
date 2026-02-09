"""Mock ECU implementation for development and testing"""

import asyncio
import math
import random
import time
from typing import Dict, Any

from .base import ECUBase


class MockECU(ECUBase):
    """Simulates ECU data with realistic patterns"""
    
    def __init__(self, update_rate: int = 20):
        super().__init__()
        self.update_rate = update_rate
        self.time_offset = 0.0
        
    async def connect(self) -> bool:
        """Simulate connection to ECU"""
        await asyncio.sleep(0.1)  # Simulate connection delay
        print("MockECU: Connected")
        return True
        
    async def disconnect(self) -> None:
        """Simulate disconnection from ECU"""
        print("MockECU: Disconnected")
        
    async def read_data(self) -> Dict[str, Any]:
        """Generate simulated PID data
        
        Returns:
            Dict with simulated values:
            - boost (0x2204FE): Sine wave with noise for realistic boost simulation
            - oil_temp (0x220546): Sine wave within realistic temp range (180-220°F)
            - oar (0x2203E8): Simulated oxygen/air ratio with drift
            - timestamp: Current Unix timestamp
        """
        current_time = time.time()
        self.time_offset += 1.0 / self.update_rate
        
        # Boost (0x2204FE): Sine wave representing boost cycles with noise
        # Raw value will be converted by parser: raw_value * 0.0145 - 14.7
        # Target PSI range: -14.7 to +15 PSI
        # So raw needs to be in range ~0 to ~2048
        boost_base = 1014.0 + math.sin(self.time_offset * 0.5) * 500.0  # Cycles between vacuum and boost
        boost_noise = random.gauss(0, 20)  # Add realistic noise
        boost_raw = max(0, boost_base + boost_noise)
        
        # Oil Temp (0x220546): Slowly varying temperature
        # Realistic operating range: 180-220°F
        # Raw value in some arbitrary units, will be interpreted as temp
        oil_temp_base = 200.0 + math.sin(self.time_offset * 0.1) * 20.0
        oil_temp_noise = random.gauss(0, 1)
        oil_temp_raw = oil_temp_base + oil_temp_noise
        
        # OAR (0x2203E8): Oxygen/Air Ratio - should hover near -1.0 for proper operation
        # Simulate occasional drift and disturbances
        oar_base = -1.0
        oar_drift = math.sin(self.time_offset * 0.3) * 0.15
        oar_disturbance = random.gauss(0, 0.05)
        oar_value = oar_base + oar_drift + oar_disturbance
        
        return {
            "boost": boost_raw,
            "oil_temp": oil_temp_raw,
            "oar": oar_value,
            "timestamp": current_time,
        }
