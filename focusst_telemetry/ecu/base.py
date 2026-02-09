"""Abstract base class for ECU data sources"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio


class ECUBase(ABC):
    """Base class for all ECU data sources"""
    
    def __init__(self):
        self.running = False
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the ECU data source
        
        Returns:
            bool: True if connection successful
        """
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the ECU data source"""
        pass
        
    @abstractmethod
    async def read_data(self) -> Dict[str, Any]:
        """Read data from the ECU
        
        Returns:
            Dict containing PID data with keys:
            - boost: Boost pressure raw value
            - oil_temp: Oil temperature raw value
            - oar: Oxygen sensor air ratio
            - timestamp: Unix timestamp
        """
        pass
        
    async def start(self):
        """Start the ECU data source"""
        self.running = True
        await self.connect()
        
    async def stop(self):
        """Stop the ECU data source"""
        self.running = False
        await self.disconnect()
