"""OBD-II simulator for telemetry data generation."""
import asyncio
import random
import math
from datetime import datetime
from typing import Dict, Optional, List
import uuid


class OBDSimulator:
    """Simulates OBD-II telemetry data for a Focus ST."""
    
    # Common OBD-II PIDs with realistic ranges for Focus ST
    PIDS = {
        "RPM": {"min": 800, "max": 6500, "unit": "RPM", "variance": 100},
        "SPEED": {"min": 0, "max": 155, "unit": "MPH", "variance": 5},
        "THROTTLE": {"min": 0, "max": 100, "unit": "%", "variance": 10},
        "ENGINE_LOAD": {"min": 0, "max": 100, "unit": "%", "variance": 5},
        "COOLANT_TEMP": {"min": 80, "max": 220, "unit": "°F", "variance": 2},
        "INTAKE_TEMP": {"min": 60, "max": 180, "unit": "°F", "variance": 3},
        "MAF": {"min": 2, "max": 250, "unit": "g/s", "variance": 10},
        "INTAKE_PRESSURE": {"min": 10, "max": 25, "unit": "PSI", "variance": 2},
        "TIMING_ADVANCE": {"min": -10, "max": 30, "unit": "°", "variance": 2},
        "FUEL_PRESSURE": {"min": 40, "max": 65, "unit": "PSI", "variance": 1},
        "BOOST": {"min": -5, "max": 22, "unit": "PSI", "variance": 1},
        "OIL_TEMP": {"min": 80, "max": 280, "unit": "°F", "variance": 2},
        "TURBO_SPEED": {"min": 0, "max": 240000, "unit": "RPM", "variance": 5000},
        "AFR": {"min": 10, "max": 16, "unit": "ratio", "variance": 0.5},
        "FUEL_LEVEL": {"min": 0, "max": 100, "unit": "%", "variance": 0},
        "BATTERY_VOLTAGE": {"min": 12.0, "max": 14.8, "unit": "V", "variance": 0.2},
    }
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.current_values = {}
        self.time_offset = 0
        self.scenario = "idle"  # idle, cruising, acceleration, hard_driving
        self._initialize_values()
    
    def _initialize_values(self):
        """Initialize all PID values to baseline."""
        for pid, config in self.PIDS.items():
            self.current_values[pid] = (config["min"] + config["max"]) / 2
    
    def set_scenario(self, scenario: str):
        """Change driving scenario for more realistic simulation."""
        self.scenario = scenario
    
    def _get_target_value(self, pid: str) -> float:
        """Get target value based on current scenario."""
        config = self.PIDS[pid]
        
        # Scenario-based targets
        if self.scenario == "idle":
            targets = {
                "RPM": 850,
                "SPEED": 0,
                "THROTTLE": 0,
                "ENGINE_LOAD": 15,
                "BOOST": -3,
                "TURBO_SPEED": 0,
            }
        elif self.scenario == "cruising":
            targets = {
                "RPM": 2500,
                "SPEED": 60,
                "THROTTLE": 25,
                "ENGINE_LOAD": 30,
                "BOOST": 0,
                "TURBO_SPEED": 80000,
            }
        elif self.scenario == "acceleration":
            targets = {
                "RPM": 4500,
                "SPEED": 80,
                "THROTTLE": 75,
                "ENGINE_LOAD": 80,
                "BOOST": 18,
                "TURBO_SPEED": 200000,
            }
        elif self.scenario == "hard_driving":
            targets = {
                "RPM": 5500,
                "SPEED": 100,
                "THROTTLE": 95,
                "ENGINE_LOAD": 95,
                "BOOST": 21,
                "TURBO_SPEED": 230000,
                "OIL_TEMP": 240,
            }
        else:
            return (config["min"] + config["max"]) / 2
        
        return targets.get(pid, (config["min"] + config["max"]) / 2)
    
    def read_pid(self, pid: str) -> Optional[Dict]:
        """Read a single PID value."""
        if pid not in self.PIDS:
            return None
        
        config = self.PIDS[pid]
        current = self.current_values[pid]
        target = self._get_target_value(pid)
        
        # Gradually move towards target with some noise
        delta = (target - current) * 0.1
        noise = random.uniform(-config["variance"], config["variance"])
        new_value = current + delta + noise
        
        # Clamp to valid range
        new_value = max(config["min"], min(config["max"], new_value))
        
        # Add some correlation effects
        if pid == "RPM" and new_value > 3000:
            # Higher RPM increases oil temp
            self.current_values["OIL_TEMP"] += 0.5
        
        if pid == "BOOST" and new_value > 15:
            # High boost increases intake temp
            self.current_values["INTAKE_TEMP"] += 0.3
        
        self.current_values[pid] = new_value
        
        return {
            "pid": pid,
            "value": round(new_value, 2),
            "unit": config["unit"],
            "timestamp": datetime.now().isoformat()
        }
    
    def read_all(self) -> List[Dict]:
        """Read all PID values."""
        return [self.read_pid(pid) for pid in self.PIDS.keys()]
    
    def get_dtc_codes(self) -> List[Dict]:
        """Simulate getting diagnostic trouble codes."""
        # Simulate some random DTCs occasionally
        if random.random() < 0.1:
            return [
                {
                    "code": "P0171",
                    "description": "System Too Lean (Bank 1)",
                    "severity": "warning"
                }
            ]
        return []
    
    async def stream(self, rate_hz: float = 10):
        """Async generator that streams telemetry data."""
        interval = 1.0 / rate_hz
        
        while True:
            # Randomly change scenarios for variety
            if random.random() < 0.01:
                scenarios = ["idle", "cruising", "acceleration", "hard_driving"]
                self.scenario = random.choice(scenarios)
            
            data = self.read_all()
            yield data
            await asyncio.sleep(interval)


class HardwareAbstractionLayer:
    """Hardware abstraction layer for different OBD interfaces."""
    
    def __init__(self, interface_type: str = "simulator", **kwargs):
        self.interface_type = interface_type
        self.kwargs = kwargs
        self.interface = None
    
    async def connect(self):
        """Connect to the OBD interface."""
        if self.interface_type == "simulator":
            self.interface = OBDSimulator()
        elif self.interface_type == "usb":
            # Placeholder for USB OBD adapter
            raise NotImplementedError("USB OBD adapter not yet implemented")
        elif self.interface_type == "can":
            # Placeholder for CAN bus adapter
            raise NotImplementedError("CAN bus adapter not yet implemented")
        elif self.interface_type == "remote":
            # Placeholder for remote bridge proxy
            raise NotImplementedError("Remote bridge proxy not yet implemented")
        else:
            raise ValueError(f"Unknown interface type: {self.interface_type}")
    
    async def disconnect(self):
        """Disconnect from the OBD interface."""
        self.interface = None
    
    def read_pid(self, pid: str) -> Optional[Dict]:
        """Read a PID value through the abstraction layer."""
        if not self.interface:
            raise RuntimeError("Interface not connected")
        return self.interface.read_pid(pid)
    
    def read_all(self) -> List[Dict]:
        """Read all PIDs through the abstraction layer."""
        if not self.interface:
            raise RuntimeError("Interface not connected")
        return self.interface.read_all()
    
    async def stream(self, rate_hz: float = 10):
        """Stream telemetry data."""
        if not self.interface:
            raise RuntimeError("Interface not connected")
        async for data in self.interface.stream(rate_hz):
            yield data
