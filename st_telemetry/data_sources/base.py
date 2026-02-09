"""Base interface for data sources."""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class DataPoint:
    """Represents a single data point from a PID."""

    def __init__(
        self,
        pid_id: str,
        pid_name: str,
        raw_value: float,
        converted_value: float,
        unit: str,
        timestamp: float,
        warning: Optional[str] = None,
    ):
        self.pid_id = pid_id
        self.pid_name = pid_name
        self.raw_value = raw_value
        self.converted_value = converted_value
        self.unit = unit
        self.timestamp = timestamp
        self.warning = warning

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "pid_id": self.pid_id,
            "pid_name": self.pid_name,
            "raw_value": self.raw_value,
            "converted_value": self.converted_value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "warning": self.warning,
        }


class DataSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the data source."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the data source."""
        pass

    @abstractmethod
    async def read_pid(self, pid_name: str) -> Optional[DataPoint]:
        """Read a single PID value."""
        pass

    @abstractmethod
    async def start_streaming(self) -> None:
        """Start streaming data."""
        pass

    @abstractmethod
    async def stop_streaming(self) -> None:
        """Stop streaming data."""
        pass

    @abstractmethod
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        pass
