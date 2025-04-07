"""
Network service implementation for the Myth metaserver.

This module provides the core networking functionality including TCP connection
handling, client management, and message routing.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Optional, Set

from ..interfaces.network_interface import NetworkInterface

logger = logging.getLogger(__name__)

@dataclass
class ClientConnection:
    """Represents a connected client."""
    id: str
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    user_id: Optional[int] = None
    connected_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    last_message_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    
    def __hash__(self) -> int:
        return hash(self.id)

class NetworkService(NetworkInterface):
    """Network service implementation."""
    
    def __init__(self):
        self._server: Optional[asyncio.AbstractServer] = None
        self._clients: Dict[str, ClientConnection] = {}
        self._client_queues: Dict[str, asyncio.Queue] = {}
        
    async def start_server(self, host: str, port: int) -> None:
        """Start the network server."""
        if self._server:
            logger.warning("Server already running")
            return
            
        try:
            self._server = await asyncio.start_server(
                self._handle_client_connection, host, port
            )
            
            addr = self._server.sockets[0].getsockname()
            logger.info(f"Server started on {addr}")
            
            async with self._server:
                await self._server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
            
    async def stop_server(self) -> None:
        """Stop the network server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            
            # Disconnect all clients
            for client_id in list(self._clients.keys()):
                await self.disconnect_client(client_id)
                
            logger.info("Server stopped")
            
    async def broadcast(self, message: Any, exclude_clients: Optional[Set[str]] = None) -> None:
        """Broadcast a message to all connected clients."""
        exclude_clients = exclude_clients or set()
        
        for client_id, client in self._clients.items():
            if client_id not in exclude_clients:
                try:
                    await self._send_message(client, message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to client {client_id}: {e}")
                    await self.disconnect_client(client_id)
                    
    async def send_to_client(self, client_id: str, message: Any) -> bool:
        """Send a message to a specific client."""
        client = self._clients.get(client_id)
        if not client:
            return False
            
        try:
            await self._send_message(client, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            await self.disconnect_client(client_id)
            return False
            
    async def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a connected client."""
        client = self._clients.get(client_id)
        if not client:
            return None
            
        return {
            "id": client.id,
            "user_id": client.user_id,
            "connected_at": client.connected_at,
            "last_message_at": client.last_message_at,
            "address": client.writer.get_extra_info("peername")
        }
        
    async def get_connected_clients(self) -> Set[str]:
        """Get set of all connected client IDs."""
        return set(self._clients.keys())
        
    async def disconnect_client(self, client_id: str) -> bool:
        """Disconnect a specific client."""
        client = self._clients.get(client_id)
        if not client:
            return False
            
        try:
            client.writer.close()
            await client.writer.wait_closed()
        except Exception as e:
            logger.error(f"Error closing client connection {client_id}: {e}")
            
        del self._clients[client_id]
        
        if client_id in self._client_queues:
            del self._client_queues[client_id]
            
        logger.info(f"Client {client_id} disconnected")
        return True
        
    def get_client_stream(self, client_id: str) -> Optional[AsyncIterator[Any]]:
        """Get an async iterator for receiving messages from a specific client."""
        if client_id not in self._client_queues:
            return None
            
        async def message_stream() -> AsyncIterator[Any]:
            queue = self._client_queues[client_id]
            while True:
                try:
                    message = await queue.get()
                    yield message
                except asyncio.CancelledError:
                    break
                    
        return message_stream()
        
    async def _handle_client_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle a new client connection."""
        client_id = str(uuid.uuid4())
        client = ClientConnection(
            id=client_id,
            reader=reader,
            writer=writer
        )
        
        self._clients[client_id] = client
        self._client_queues[client_id] = asyncio.Queue()
        
        peer_name = writer.get_extra_info("peername")
        logger.info(f"New connection from {peer_name} (client_id: {client_id})")
        
        try:
            while True:
                try:
                    data = await reader.read(8192)  # 8KB buffer
                    if not data:
                        break
                        
                    client.last_message_at = asyncio.get_event_loop().time()
                    
                    # Process received data
                    await self._handle_client_message(client, data)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    break
                    
        finally:
            await self.disconnect_client(client_id)
            
    async def _handle_client_message(self, client: ClientConnection, data: bytes) -> None:
        """Handle a message received from a client."""
        try:
            # Put message in client's queue for processing
            if client.id in self._client_queues:
                await self._client_queues[client.id].put(data)
                
        except Exception as e:
            logger.error(f"Error processing client message: {e}")
            
    async def _send_message(self, client: ClientConnection, message: Any) -> None:
        """Send a message to a client."""
        if isinstance(message, str):
            message = message.encode()
        elif not isinstance(message, bytes):
            message = str(message).encode()
            
        client.writer.write(message)
        await client.writer.drain()

# Global instance
network_service = NetworkService()
