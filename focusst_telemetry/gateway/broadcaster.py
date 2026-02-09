"""Async broadcaster for relaying telemetry data to WebSocket clients"""

import asyncio
import json
import logging
from typing import Set, Dict, Any

logger = logging.getLogger(__name__)


class Broadcaster:
    """Manages broadcasting telemetry data to connected clients"""
    
    def __init__(self):
        self.clients: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
        
    async def register(self) -> asyncio.Queue:
        """Register a new client and return their message queue"""
        queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self.clients.add(queue)
        return queue
        
    async def unregister(self, queue: asyncio.Queue):
        """Unregister a client"""
        async with self._lock:
            self.clients.discard(queue)
            
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients
        
        Args:
            data: Telemetry data dictionary to broadcast
        """
        async with self._lock:
            # Create a list to avoid modification during iteration
            clients_to_remove = []
            
            for queue in list(self.clients):
                try:
                    # Non-blocking put, drop if queue is full
                    queue.put_nowait(data)
                except asyncio.QueueFull:
                    # Client is too slow, remove them
                    clients_to_remove.append(queue)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    clients_to_remove.append(queue)
            
            # Remove slow/failed clients
            for queue in clients_to_remove:
                self.clients.discard(queue)
                
    def get_client_count(self) -> int:
        """Get the number of connected clients"""
        return len(self.clients)
