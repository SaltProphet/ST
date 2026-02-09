"""Base ECU interface for telemetry data acquisition."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ECUInterface(ABC):
    """Abstract base class for ECU interfaces."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to ECU."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to ECU."""
        pass
    
    @abstractmethod
    async def get_telemetry(self) -> Dict[str, Any]:
        """Get current telemetry data from ECU."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if ECU is connected."""
        pass
