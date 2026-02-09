"""OBD-II ELM327 Bluetooth Bridge implementation for Focus ST"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional
import serial

from .base import ECUBase

logger = logging.getLogger(__name__)


class OBDBridge(ECUBase):
    """OBD-II ELM327 Bluetooth Bridge for Focus ST Telemetry
    
    Connects to ELM327 adapter via Bluetooth Serial Port Profile (SPP)
    at /dev/rfcomm0 and polls Ford-specific PIDs:
    - 2204FE: Turbo Boost (20Hz)
    - 220546: Oil Temperature (2Hz)  
    - 2203E8: Octane Adjusted Ratio (2Hz)
    """
    
    def __init__(self, device_path: str = "/dev/rfcomm0", baudrate: int = 38400):
        super().__init__()
        self.device_path = device_path
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.last_keepalive = 0.0
        self.keepalive_interval = 5.0  # Send keep-alive every 5 seconds
        
        # PID polling cycle counters for different frequencies
        self.poll_counter = 0
        
    async def connect(self) -> bool:
        """Connect to ELM327 via Bluetooth SPP
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Check if device exists
            if not os.path.exists(self.device_path):
                logger.warning(f"Device {self.device_path} not found. Hardware not detected.")
                return False
                
            logger.info(f"Connecting to ELM327 at {self.device_path}...")
            
            # Open serial connection
            self.serial_conn = serial.Serial(
                port=self.device_path,
                baudrate=self.baudrate,
                timeout=2.0,
                write_timeout=2.0
            )
            
            # Give the connection time to stabilize
            await asyncio.sleep(0.5)
            
            # Initialize ELM327
            await self._send_command("ATZ")  # Reset
            await asyncio.sleep(1.0)
            await self._send_command("ATE0")  # Echo off
            await self._send_command("ATL0")  # Line feeds off
            await self._send_command("ATS0")  # Spaces off
            await self._send_command("ATH1")  # Headers on
            await self._send_command("ATSP6")  # Set protocol to ISO 15765-4 CAN (500 kbaud)
            
            logger.info("ELM327 initialized successfully")
            self.last_keepalive = time.time()
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to ELM327: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during ELM327 connection: {e}")
            return False
        
    async def disconnect(self) -> None:
        """Disconnect from ELM327"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info("ELM327 disconnected")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
        self.serial_conn = None
        
    async def _send_command(self, command: str, await_response: bool = True) -> Optional[str]:
        """Send command to ELM327 and optionally await response
        
        Args:
            command: AT command or PID request
            await_response: Whether to wait for and return response
            
        Returns:
            Response string if await_response=True, None otherwise
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Serial connection not open")
            return None
            
        try:
            # Send command
            cmd = f"{command}\r"
            self.serial_conn.write(cmd.encode('ascii'))
            
            if not await_response:
                return None
                
            # Read response
            response_lines = []
            while True:
                line = self.serial_conn.readline().decode('ascii').strip()
                if not line or line == '>' or 'ERROR' in line:
                    break
                response_lines.append(line)
                
            return '\n'.join(response_lines) if response_lines else None
            
        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return None
            
    async def _read_pid(self, pid: str) -> Optional[bytes]:
        """Read a Ford-specific PID
        
        Args:
            pid: PID in hex format (e.g., "2204FE")
            
        Returns:
            Raw response bytes or None on error
        """
        response = await self._send_command(pid)
        if not response:
            return None
            
        try:
            # Parse response: "62 04 FE AA BB" -> extract data bytes
            # For Ford extended PIDs, response format is: 62 [PID bytes] [Data bytes]
            parts = response.replace(' ', '')
            if len(parts) >= 8 and parts.startswith('62'):
                # Extract data bytes after the header
                data_hex = parts[6:]  # Skip "62" + PID bytes
                return bytes.fromhex(data_hex)
            return None
        except Exception as e:
            logger.error(f"Error parsing PID {pid} response: {e}")
            return None
    
    async def _keepalive(self) -> None:
        """Send keep-alive to prevent ELM327 timeout"""
        current_time = time.time()
        if current_time - self.last_keepalive >= self.keepalive_interval:
            await self._send_command("0100", await_response=False)  # Simple PID query as keep-alive
            self.last_keepalive = current_time
            
    async def read_data(self) -> Dict[str, Any]:
        """Read PIDs from ELM327 with intelligent polling
        
        High-frequency (20Hz): Boost (2204FE)
        Low-frequency (2Hz): Oil Temp (220546), OAR (2203E8)
        
        Returns:
            Dict with PID values matching MockECU format
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("Cannot read data: serial connection not open")
            return {
                "boost": 1014.0,
                "oil_temp": 200.0,
                "oar": -1.0,
                "timestamp": time.time(),
            }
        
        # Keep-alive check
        await self._keepalive()
        
        # Always read high-frequency boost
        boost_raw = 1014.0  # Default
        boost_data = await self._read_pid("2204FE")
        if boost_data and len(boost_data) >= 2:
            # Formula: ((A*256)+B)*0.0145 - 14.7
            # Raw value is (A*256)+B which will be converted by parser
            A, B = boost_data[0], boost_data[1]
            boost_raw = float((A * 256) + B)
        
        # Read low-frequency PIDs every 10 cycles (20Hz / 10 = 2Hz)
        oil_temp_raw = getattr(self, '_last_oil_temp', 200.0)
        oar_raw = getattr(self, '_last_oar', -1.0)
        
        if self.poll_counter % 10 == 0:
            # Read oil temp
            oil_temp_data = await self._read_pid("220546")
            if oil_temp_data and len(oil_temp_data) >= 2:
                # Ford oil temp PID: Direct °F value encoded as 2-byte integer
                # Formula: raw temperature in Fahrenheit from (A*256 + B) / 10
                A, B = oil_temp_data[0], oil_temp_data[1]
                oil_temp_raw = float((A * 256) + B) / 10.0
                self._last_oil_temp = oil_temp_raw
            
            # Read OAR  
            oar_data = await self._read_pid("2203E8")
            if oar_data and len(oar_data) >= 2:
                # Ford OAR PID: Signed ratio value
                # Formula: Convert 2-byte signed integer to ratio (-1.0 typical)
                A, B = oar_data[0], oar_data[1]
                raw_int = (A * 256) + B
                # Convert to signed 16-bit
                if raw_int > 32768:
                    raw_int -= 65536
                # Scale to ratio (typical range: -1.5 to 0.0)
                oar_raw = float(raw_int) / 1000.0
                self._last_oar = oar_raw
        
        self.poll_counter += 1
        
        return {
            "boost": boost_raw,
            "oil_temp": oil_temp_raw,
            "oar": oar_raw,
            "timestamp": time.time(),
        }
