"""ECU factory for creating appropriate ECU instances."""
from typing import Optional
from .base import ECUInterface
from .mock_ecu import MockECU
from .obd_ecu import OBDII_ECU


class ECUFactory:
    """Factory for creating ECU instances based on configuration."""
    
    @staticmethod
    def create_ecu(
        ecu_type: str = "mock",
        port: Optional[str] = None,
        baudrate: int = 38400
    ) -> ECUInterface:
        """
        Create an ECU instance.
        
        Args:
            ecu_type: Type of ECU ("mock" or "obd2")
            port: Serial port for OBD-II (None for auto-detect)
            baudrate: Baudrate for OBD-II connection
            
        Returns:
            ECU instance
            
        Raises:
            ValueError: If ecu_type is not recognized
        """
        if ecu_type.lower() == "mock":
            return MockECU()
        elif ecu_type.lower() == "obd2":
            return OBDII_ECU(port=port, baudrate=baudrate)
        else:
            raise ValueError(
                f"Unknown ECU type: {ecu_type}. Must be 'mock' or 'obd2'"
            )
