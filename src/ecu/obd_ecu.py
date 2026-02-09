"""OBD-II Bluetooth bridge for real ECU connection."""
import asyncio
import time
from typing import Dict, Any, Optional
from .base import ECUInterface

try:
    import obd
    OBD_AVAILABLE = True
except ImportError:
    OBD_AVAILABLE = False


class OBDII_ECU(ECUInterface):
    """OBD-II interface for real ECU connection via Bluetooth."""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 38400):
        """
        Initialize OBD-II connection.
        
        Args:
            port: Serial port for OBD-II adapter (None for auto-detect)
            baudrate: Communication baudrate
        """
        if not OBD_AVAILABLE:
            raise ImportError(
                "python-obd not installed. Install with: pip install python-obd"
            )
        
        self._port = port
        self._baudrate = baudrate
        self._connection: Optional[obd.OBD] = None
        self._connected = False
        
    async def connect(self) -> bool:
        """Establish connection to OBD-II adapter."""
        try:
            # Run blocking OBD connection in executor
            loop = asyncio.get_event_loop()
            self._connection = await loop.run_in_executor(
                None,
                lambda: obd.OBD(self._port, self._baudrate)
            )
            
            self._connected = self._connection.is_connected()
            return self._connected
            
        except Exception as e:
            print(f"Failed to connect to OBD-II: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close OBD-II connection."""
        if self._connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connection.close)
            self._connection = None
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check OBD-II connection status."""
        return self._connected and self._connection is not None
    
    def _extract_value(self, response) -> Any:
        """
        Extract value from OBD response.
        
        Args:
            response: OBD query response
            
        Returns:
            Extracted value or None
        """
        if response and not response.is_null():
            return response.value.magnitude if hasattr(response.value, 'magnitude') else response.value
        return None
    
    def _query_command(self, cmd) -> Any:
        """Query a single OBD command."""
        if not self._connection:
            return None
        
        try:
            response = self._connection.query(cmd)
            return self._extract_value(response)
        except Exception:
            pass
        return None
    
    async def get_telemetry(self) -> Dict[str, Any]:
        """Get real telemetry data from OBD-II."""
        if not self.is_connected():
            raise RuntimeError("OBD-II not connected")
        
        # Run queries in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Query all commands
        commands = {
            'rpm': obd.commands.RPM,
            'speed': obd.commands.SPEED,
            'throttle_position': obd.commands.THROTTLE_POS,
            'engine_load': obd.commands.ENGINE_LOAD,
            'coolant_temp': obd.commands.COOLANT_TEMP,
            'intake_temp': obd.commands.INTAKE_TEMP,
            'timing_advance': obd.commands.TIMING_ADVANCE,
            'maf': obd.commands.MAF,
            'intake_pressure': obd.commands.INTAKE_PRESSURE,
            'fuel_level': obd.commands.FUEL_LEVEL,
            'voltage': obd.commands.CONTROL_MODULE_VOLTAGE,
            'fuel_pressure': obd.commands.FUEL_PRESSURE,
        }
        
        # Query all commands in parallel
        tasks = []
        for key, cmd in commands.items():
            task = loop.run_in_executor(None, self._query_command, cmd)
            tasks.append((key, task))
        
        # Gather results
        results = {}
        for key, task in tasks:
            try:
                value = await task
                if value is not None:
                    results[key] = value
            except Exception:
                pass
        
        # Build telemetry dictionary with available data
        telemetry = {
            "rpm": results.get('rpm', 0),
            "speed": results.get('speed', 0),
            "throttle_position": results.get('throttle_position', 0),
            "engine_load": results.get('engine_load', 0),
            "coolant_temp": results.get('coolant_temp', 0),
            "intake_air_temp": results.get('intake_temp', 0),
            "timing_advance": results.get('timing_advance', 0),
            "manifold_pressure": results.get('intake_pressure', 0),
            "fuel_level": results.get('fuel_level', 0),
            "battery_voltage": results.get('voltage', 0),
            "fuel_pressure": results.get('fuel_pressure', 0),
            "timestamp": time.time(),
            "ecu_type": "obd2"
        }
        
        # Calculate boost (intake pressure - atmospheric)
        if telemetry.get('manifold_pressure', 0) > 0:
            telemetry['boost_pressure'] = telemetry['manifold_pressure'] - 14.7
        else:
            telemetry['boost_pressure'] = 0
        
        return telemetry
