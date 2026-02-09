"""Mock ECU data source for development and testing."""

import asyncio
import logging
import time
from typing import Callable, Dict, Optional

import numpy as np

from st_telemetry.config import Config, PIDConfig
from st_telemetry.data_sources.base import DataPoint, DataSource

logger = logging.getLogger(__name__)


class MockECU(DataSource):
    """Mock ECU that generates realistic PID data using sine waves and noise."""

    def __init__(self, config: Config):
        self.config = config
        self.pids = config.get_pids()
        self._streaming = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, list] = {}
        self._start_time = None
        self._previous_values: Dict[str, float] = {}

    async def initialize(self) -> None:
        """Initialize the mock ECU."""
        logger.info("Initializing Mock ECU")
        self._start_time = time.time()
        for pid in self.pids:
            self._callbacks[pid.name] = []
            # Initialize previous values for warning detection
            if pid.warning_threshold is not None:
                self._previous_values[pid.name] = pid.warning_threshold

    async def shutdown(self) -> None:
        """Shutdown the mock ECU."""
        logger.info("Shutting down Mock ECU")
        await self.stop_streaming()

    def register_callback(self, pid_name: str, callback: Callable[[DataPoint], None]) -> None:
        """Register a callback for PID updates."""
        if pid_name in self._callbacks:
            self._callbacks[pid_name].append(callback)

    def _generate_value(self, pid: PIDConfig, elapsed_time: float) -> float:
        """Generate a mock value using sine wave and noise."""
        # Base sine wave
        if pid.mock_wave_type == "sine":
            base_value = pid.mock_amplitude * np.sin(2 * np.pi * pid.mock_frequency * elapsed_time)
        else:
            # Default to sine
            base_value = pid.mock_amplitude * np.sin(2 * np.pi * pid.mock_frequency * elapsed_time)

        # Add offset
        base_value += pid.mock_offset

        # Add Gaussian noise
        noise = np.random.normal(0, pid.mock_noise_stddev)
        raw_value = base_value + noise

        return raw_value

    def _convert_value(self, pid: PIDConfig, raw_value: float) -> float:
        """Apply PID-specific conversion formula."""
        # For Boost: RawValue * 0.0145 - 14.7
        # For Oil Temp: Linear conversion with multiplier and offset
        # For OAR: No conversion (multiplier=1.0, offset=0.0)
        converted_value = raw_value * pid.conversion_multiplier + pid.conversion_offset
        return converted_value

    def _check_warning(self, pid: PIDConfig, converted_value: float) -> Optional[str]:
        """Check for warnings based on PID-specific logic."""
        warning = None

        # OAR warning: flag if it moves from -1.0
        if pid.warning_threshold is not None:
            prev_value = self._previous_values.get(pid.name)
            if prev_value is not None:
                if prev_value == pid.warning_threshold and converted_value != pid.warning_threshold:
                    warning = f"{pid.name} moved from {pid.warning_threshold}"
                    logger.warning(f"Warning: {warning}")

            self._previous_values[pid.name] = converted_value

        return warning

    async def read_pid(self, pid_name: str) -> Optional[DataPoint]:
        """Read a single PID value."""
        pid_config = self.config.get_pid_by_name(pid_name)
        if not pid_config:
            logger.error(f"PID '{pid_name}' not found in configuration")
            return None

        elapsed_time = time.time() - self._start_time if self._start_time else 0
        raw_value = self._generate_value(pid_config, elapsed_time)
        converted_value = self._convert_value(pid_config, raw_value)
        warning = self._check_warning(pid_config, converted_value)

        return DataPoint(
            pid_id=pid_config.id,
            pid_name=pid_config.name,
            raw_value=raw_value,
            converted_value=converted_value,
            unit=pid_config.unit,
            timestamp=time.time(),
            warning=warning,
        )

    async def _stream_pid(self, pid: PIDConfig) -> None:
        """Stream a single PID at its configured rate."""
        interval = 1.0 / pid.update_rate_hz
        logger.info(
            f"Starting stream for {pid.name} at {pid.update_rate_hz}Hz (interval: {interval}s)"
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
                logger.info(f"Stream cancelled for {pid.name}")
                break
            except Exception as e:
                logger.error(f"Error streaming {pid.name}: {e}")
                await asyncio.sleep(interval)

    async def start_streaming(self) -> None:
        """Start streaming all PIDs."""
        if self._streaming:
            logger.warning("Already streaming")
            return

        logger.info("Starting PID streaming")
        self._streaming = True

        # Start a task for each PID
        for pid in self.pids:
            task = asyncio.create_task(self._stream_pid(pid))
            self._tasks[pid.name] = task

    async def stop_streaming(self) -> None:
        """Stop streaming all PIDs."""
        if not self._streaming:
            return

        logger.info("Stopping PID streaming")
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
