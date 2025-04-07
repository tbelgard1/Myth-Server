"""
Network interface for the Myth metaserver.

This module defines the interface for network operations including connection
handling, packet processing, and client management.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, Optional, Set
import asyncio

class NetworkInterface(ABC):
    """Interface for network operations."""
    
    @abstractmethod
    async def start_server(self, host: str, port: int) -> None:
        """Start the network server.
        
        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        pass
        
    @abstractmethod
    async def stop_server(self) -> None:
        """Stop the network server and cleanup resources."""
        pass
        
    @abstractmethod
    async def broadcast(self, message: Any, exclude_clients: Optional[Set[str]] = None) -> None:
        """Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude_clients: Optional set of client IDs to exclude
        """
        pass
        
    @abstractmethod
    async def send_to_client(self, client_id: str, message: Any) -> bool:
        """Send a message to a specific client.
        
        Args:
            client_id: ID of the client to send to
            message: Message to send
            
        Returns:
            bool: True if sent successfully, False if client not found
        """
        pass
        
    @abstractmethod
    async def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a connected client.
        
        Args:
            client_id: ID of the client
            
        Returns:
            Optional[Dict[str, Any]]: Client info if found, None if not found
        """
        pass
        
    @abstractmethod
    async def get_connected_clients(self) -> Set[str]:
        """Get set of all connected client IDs.
        
        Returns:
            Set[str]: Set of client IDs
        """
        pass
        
    @abstractmethod
    async def disconnect_client(self, client_id: str) -> bool:
        """Disconnect a specific client.
        
        Args:
            client_id: ID of the client to disconnect
            
        Returns:
            bool: True if disconnected successfully, False if client not found
        """
        pass
        
    @abstractmethod
    def get_client_stream(self, client_id: str) -> Optional[AsyncIterator[Any]]:
        """Get an async iterator for receiving messages from a specific client.
        
        Args:
            client_id: ID of the client
            
        Returns:
            Optional[AsyncIterator[Any]]: Message stream if client found, None if not
        """
        pass
