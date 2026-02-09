"""Mock ECU for development and testing."""
import asyncio
import random
import math
import time
from typing import Dict, Any
from .base import ECUInterface


class MockECU(ECUInterface):
    """Mock ECU that simulates realistic Focus ST telemetry data."""
    
    def __init__(self):
        self._connected = False
        self._start_time = None
        self._sim_time = 0.0
        
        # Simulation state
        self._rpm_base = 800
        self._speed_base = 0
        self._throttle_base = 0
        self._boost_base = 0
        
    async def connect(self) -> bool:
        """Simulate ECU connection."""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self._connected = True
        self._start_time = time.time()
        return True
    
    async def disconnect(self) -> None:
        """Simulate ECU disconnection."""
        self._connected = False
        self._start_time = None
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def _simulate_driving_scenario(self) -> None:
        """Simulate realistic driving patterns."""
        if self._start_time is None:
            return
            
        # Update simulation time
        self._sim_time = time.time() - self._start_time
        
        # Create a driving cycle (idle -> accelerate -> cruise -> decelerate)
        cycle_duration = 30  # 30 second cycle
        cycle_position = (self._sim_time % cycle_duration) / cycle_duration
        
        if cycle_position < 0.1:  # Idle (0-3s)
            self._rpm_base = 800 + random.uniform(-50, 50)
            self._speed_base = 0
            self._throttle_base = 0
            self._boost_base = 0
            
        elif cycle_position < 0.4:  # Accelerating (3-12s)
            progress = (cycle_position - 0.1) / 0.3
            self._rpm_base = 800 + (5500 * progress) + random.uniform(-100, 100)
            self._speed_base = 60 * progress + random.uniform(-2, 2)
            self._throttle_base = 80 + (20 * progress) + random.uniform(-5, 5)
            self._boost_base = 18 * progress + random.uniform(-1, 1)
            
        elif cycle_position < 0.7:  # Cruising (12-21s)
            self._rpm_base = 2800 + random.uniform(-100, 100)
            self._speed_base = 60 + random.uniform(-3, 3)
            self._throttle_base = 30 + random.uniform(-5, 5)
            self._boost_base = 2 + random.uniform(-0.5, 0.5)
            
        else:  # Decelerating (21-30s)
            progress = (cycle_position - 0.7) / 0.3
            self._rpm_base = 2800 - (2000 * progress) + random.uniform(-100, 100)
            self._speed_base = 60 - (60 * progress) + random.uniform(-2, 2)
            self._throttle_base = 30 - (30 * progress) + random.uniform(-5, 5)
            self._boost_base = max(0, 2 - (2 * progress) + random.uniform(-0.5, 0.5))
    
    async def get_telemetry(self) -> Dict[str, Any]:
        """Generate simulated telemetry data."""
        if not self._connected:
            raise RuntimeError("ECU not connected")
        
        # Update driving simulation
        self._simulate_driving_scenario()
        
        # Calculate derived values
        rpm = max(0, self._rpm_base)
        speed = max(0, self._speed_base)
        throttle = max(0, min(100, self._throttle_base))
        boost = max(-5, min(25, self._boost_base))
        
        # Calculate engine load based on throttle and RPM
        engine_load = (throttle * 0.7) + (rpm / 6500 * 30)
        
        # Temperature increases with load and time
        coolant_temp = min(210, 160 + (engine_load * 0.3) + random.uniform(-2, 2))
        oil_temp = min(250, coolant_temp + 20 + (boost * 2) + random.uniform(-3, 3))
        intake_temp = min(150, 70 + (boost * 3) + random.uniform(-5, 5))
        
        # Fuel consumption
        fuel_level = max(0, 100 - (self._sim_time / 600))  # Decreases over time
        instant_mpg = 0 if speed < 1 else max(5, 35 - (throttle * 0.2) - (rpm / 200))
        
        # Timing and air/fuel ratio
        timing_advance = 15 + (rpm / 500) - (boost * 0.5) + random.uniform(-1, 1)
        afr = 14.7 if throttle < 50 else 12.5 + random.uniform(-0.5, 0.5)
        
        # Voltages
        battery_voltage = 14.2 + random.uniform(-0.3, 0.3)
        
        return {
            # Engine
            "rpm": round(rpm, 0),
            "engine_load": round(engine_load, 1),
            "throttle_position": round(throttle, 1),
            "timing_advance": round(timing_advance, 1),
            
            # Boost and air
            "boost_pressure": round(boost, 1),
            "intake_air_temp": round(intake_temp, 1),
            "manifold_pressure": round((boost + 14.7), 1),
            
            # Temperatures
            "coolant_temp": round(coolant_temp, 1),
            "oil_temp": round(oil_temp, 1),
            
            # Fuel
            "fuel_level": round(fuel_level, 1),
            "fuel_pressure": round(40 + random.uniform(-2, 2), 1),
            "instant_mpg": round(instant_mpg, 1),
            "air_fuel_ratio": round(afr, 2),
            
            # Vehicle
            "speed": round(speed, 1),
            "battery_voltage": round(battery_voltage, 2),
            
            # Status
            "timestamp": time.time(),
            "ecu_type": "mock"
        }
