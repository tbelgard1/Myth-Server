"""
Game search service for the Myth metaserver.
Handles game registration, querying, and matchmaking.
"""

import asyncio
import socket
import struct
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Set
from enum import IntEnum
import signal
import sys

from core.models.game import GameData, GameManager
from core.networking.packets.game_search import (
    GameSearchPacketType,
    RoomPacketHeader,
    GSLoginPacket,
    GSUpdatePacket,
    GSQueryPacket,
    byte_swap_game_search_packet
)

# Constants
MAXIMUM_OUTSTANDING_REQUESTS = 32
SELECT_TIMEOUT_PERIOD = 10
MAX_ROOM_ID = 128
MAXIMUM_PACKET_SIZE = 16 * 1024
CLIENT_QUEUE_SIZE = 64 * 1024
KILO = 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClientData:
    """Client connection data"""
    socket: socket.socket
    writer: asyncio.StreamWriter
    reader: asyncio.StreamReader
    incoming_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    outgoing_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    connected: bool = True

class GameSearchService:
    def __init__(self, host: str = '0.0.0.0', port: int = 3453):
        self.host = host
        self.port = port
        self.clients: Dict[socket.socket, ClientData] = {}
        self.server: Optional[asyncio.AbstractServer] = None
        self.running = False
        self.game_manager = GameManager()

    async def start(self):
        """Initialize and start the server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client_connection,
                self.host,
                self.port,
                reuse_address=True
            )
            addr = self.server.sockets[0].getsockname()
            logger.info(f'Game search server running on {addr}')
            
            self.running = True
            self.game_manager.initialize()
            
            # Handle shutdown gracefully
            for sig in (signal.SIGTERM, signal.SIGINT):
                asyncio.get_event_loop().add_signal_handler(sig, self.stop)
                
            await self.server.serve_forever()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.stop()
            
    def stop(self):
        """Stop the server"""
        if self.running:
            logger.info("Shutting down game search server...")
            self.running = False
            self.game_manager.dispose()
            
            # Close all client connections
            for client in list(self.clients.values()):
                client.connected = False
                client.writer.close()
                
            if self.server:
                self.server.close()
                
            logger.info("Server shutdown complete")

    async def handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle new client connection"""
        sock = writer.get_extra_info('socket')
        client = ClientData(sock, writer, reader)
        self.clients[sock] = client
        
        try:
            await asyncio.gather(
                self.handle_client_read(client),
                self.handle_client_write(client)
            )
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            await self.delete_client(client)

    async def delete_client(self, client: ClientData):
        """Clean up client connection"""
        if client.socket in self.clients:
            client.connected = False
            try:
                client.writer.close()
                await client.writer.wait_closed()
            except:
                pass
            del self.clients[client.socket]

    async def handle_client_read(self, client: ClientData):
        """Handle incoming client data"""
        while client.connected:
            try:
                # Read header first
                header_data = await client.reader.readexactly(RoomPacketHeader.SIZE)
                header = RoomPacketHeader.from_bytes(header_data)
                
                # Read packet body
                body_data = await client.reader.readexactly(header.length - RoomPacketHeader.SIZE)
                packet_data = header_data + body_data
                
                # Process packet
                if not await self.handle_game_search_packet(header, body_data, client):
                    break
                    
            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                logger.error(f"Error reading from client: {e}")
                break

    async def handle_client_write(self, client: ClientData):
        """Handle outgoing client data"""
        while client.connected:
            try:
                data = await client.outgoing_queue.get()
                client.writer.write(data)
                await client.writer.drain()
            except Exception as e:
                logger.error(f"Error writing to client: {e}")
                break

    async def handle_game_search_packet(self, header: RoomPacketHeader, body: bytes, client: ClientData) -> bool:
        """Process game search packets"""
        try:
            if header.type == GameSearchPacketType.GS_LOGIN:
                packet = GSLoginPacket.from_bytes(body)
                return await self.handle_gs_login(packet, client)
                
            elif header.type == GameSearchPacketType.GS_UPDATE:
                packet = GSUpdatePacket.from_bytes(body)
                return await self.handle_gs_update(packet, client)
                
            elif header.type == GameSearchPacketType.GS_QUERY:
                packet = GSQueryPacket.from_bytes(body)
                return await self.handle_gs_query(packet, client)
                
            else:
                logger.error(f"Unknown packet type: {header.type}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling packet: {e}")
            return False

    async def handle_gs_login(self, packet: GSLoginPacket, client: ClientData) -> bool:
        """Handle login packet"""
        # TODO: Implement login validation with auth service
        return True

    async def handle_gs_update(self, packet: GSUpdatePacket, client: ClientData) -> bool:
        """Handle game update packet"""
        game_data = GameData(
            room_id=packet.room_id,
            game_id=packet.game_id,
            aux_data=packet.aux_data,
            description=packet.description,
            flags=packet.flags,
            game_name=packet.game_name,
            map_name=packet.map_name
        )
        
        self.game_manager.add_game(game_data)
        return True

    async def handle_gs_query(self, packet: GSQueryPacket, client: ClientData) -> bool:
        """Handle game query packet"""
        query = {
            'flags': packet.flags,
            'game_scoring': packet.game_scoring,
            'unit_trading': packet.unit_trading,
            'veterans': packet.veterans,
            'teams': packet.teams,
            'alliances': packet.alliances,
            'enemy_visibility': packet.enemy_visibility,
            'game_name': packet.game_name,
            'map_name': packet.map_name
        }
        
        # Search for matching games
        games = self.game_manager.search_games(query)
        for game in games:
            response = GSUpdatePacket.from_game_data(game)
            await client.outgoing_queue.put(response.to_bytes())
            
        return True
