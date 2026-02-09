"""OBD-II bridge data source for production use."""

import asyncio
import logging
import time
from typing import Callable, Dict, Optional

from st_telemetry.config import Config, PIDConfig
from st_telemetry.data_sources.base import DataPoint, DataSource

logger = logging.getLogger(__name__)


class OBDBridge(DataSource):
    """OBD-II Bridge for real vehicle data.
    
    This is a stub implementation that provides the interface for future OBD integration.
    To use with a real OBD-II adapter, install the 'obd' extra:
        pip install st-telemetry[obd]
    """

    def __init__(self, config: Config):
        self.config = config
        self.pids = config.get_pids()
        self._streaming = False
        self._connection = None
        self._tasks: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, list] = {}
        self._previous_values: Dict[str, float] = {}

    async def initialize(self) -> None:
        """Initialize the OBD-II connection."""
        logger.info("Initializing OBD-II Bridge")
        
        # TODO: Initialize real OBD connection
        # Example (requires 'obd' package):
        # import obd
        # self._connection = obd.OBD(
        #     portstr=self.config.data_source.get("obd_bridge", {}).get("port"),
        #     baudrate=self.config.data_source.get("obd_bridge", {}).get("baudrate", 38400),
        #     protocol=self.config.data_source.get("obd_bridge", {}).get("protocol", "AUTO")
        # )
        
        logger.warning("OBD Bridge is a stub - not connected to real vehicle")
        
        for pid in self.pids:
            self._callbacks[pid.name] = []
            if pid.warning_threshold is not None:
                self._previous_values[pid.name] = pid.warning_threshold

    async def shutdown(self) -> None:
        """Shutdown the OBD-II connection."""
        logger.info("Shutting down OBD-II Bridge")
        await self.stop_streaming()
        
        # TODO: Close real OBD connection
        # if self._connection:
        #     self._connection.close()

    def register_callback(self, pid_name: str, callback: Callable[[DataPoint], None]) -> None:
        """Register a callback for PID updates."""
        if pid_name in self._callbacks:
            self._callbacks[pid_name].append(callback)

    def _convert_value(self, pid: PIDConfig, raw_value: float) -> float:
        """Apply PID-specific conversion formula."""
        converted_value = raw_value * pid.conversion_multiplier + pid.conversion_offset
        return converted_value

    def _check_warning(self, pid: PIDConfig, converted_value: float) -> Optional[str]:
        """Check for warnings based on PID-specific logic."""
        warning = None

        if pid.warning_threshold is not None:
            prev_value = self._previous_values.get(pid.name)
            if prev_value is not None:
                if prev_value == pid.warning_threshold and converted_value != pid.warning_threshold:
                    warning = f"{pid.name} moved from {pid.warning_threshold}"
                    logger.warning(f"Warning: {warning}")

            self._previous_values[pid.name] = converted_value

        return warning

    async def read_pid(self, pid_name: str) -> Optional[DataPoint]:
        """Read a single PID value from OBD."""
        pid_config = self.config.get_pid_by_name(pid_name)
        if not pid_config:
            logger.error(f"PID '{pid_name}' not found in configuration")
            return None

        # TODO: Read from real OBD connection
        # Example:
        # response = self._connection.query(obd.commands[pid_config.id])
        # if response.is_null():
        #     return None
        # raw_value = response.value.magnitude
        
        # For now, return None as this is a stub
        logger.debug(f"OBD stub: would read PID {pid_name}")
        return None

    async def _stream_pid(self, pid: PIDConfig) -> None:
        """Stream a single PID at its configured rate."""
        interval = 1.0 / pid.update_rate_hz
        logger.info(
            f"Starting OBD stream for {pid.name} at {pid.update_rate_hz}Hz (interval: {interval}s)"
        )

        while self._streaming:
            try:
                data_point = await self.read_pid(pid.name)
                if data_point:
                    # Notify callbacks
                    for callback in self._callbacks.get(pid.name, []):
                        try:
                            await callback(data_point)
                        except Exception as e:
                            logger.error(f"Error in callback for {pid.name}: {e}")

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info(f"OBD stream cancelled for {pid.name}")
                break
            except Exception as e:
                logger.error(f"Error streaming {pid.name} from OBD: {e}")
                await asyncio.sleep(interval)

    async def start_streaming(self) -> None:
        """Start streaming all PIDs."""
        if self._streaming:
            logger.warning("Already streaming")
            return

        logger.info("Starting OBD PID streaming")
        self._streaming = True

        # Start a task for each PID
        for pid in self.pids:
            task = asyncio.create_task(self._stream_pid(pid))
            self._tasks[pid.name] = task

    async def stop_streaming(self) -> None:
        """Stop streaming all PIDs."""
        if not self._streaming:
            return

        logger.info("Stopping OBD PID streaming")
        self._streaming = False

        # Cancel all tasks
        for task in self._tasks.values():
            task.cancel()

        # Wait for all tasks to complete
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._streaming
