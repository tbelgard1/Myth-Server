"""
Packet definitions for the Myth metaserver.

This module defines the packet structures and handling for all network
communication in the metaserver, including packet encoding/decoding.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import struct
import logging
from enum import IntEnum

from ..models.metaserver_common_structs import NetworkAddress, MetaserverCommonStructs

logger = logging.getLogger(__name__)

class PacketType(IntEnum):
    """Types of packets that can be sent/received."""
    # Authentication packets
    LOGIN_REQUEST = 1
    LOGIN_REPLY = 2
    LOGOUT_REQUEST = 3
    LOGOUT_REPLY = 4
    
    # Room management packets
    CREATE_ROOM_REQUEST = 10
    CREATE_ROOM_REPLY = 11
    JOIN_ROOM_REQUEST = 12
    JOIN_ROOM_REPLY = 13
    LEAVE_ROOM_REQUEST = 14
    LEAVE_ROOM_REPLY = 15
    LIST_ROOMS_REQUEST = 16
    LIST_ROOMS_REPLY = 17
    
    # Game management packets
    CREATE_GAME_REQUEST = 20
    CREATE_GAME_REPLY = 21
    JOIN_GAME_REQUEST = 22
    JOIN_GAME_REPLY = 23
    LEAVE_GAME_REQUEST = 24
    LEAVE_GAME_REPLY = 25
    LIST_GAMES_REQUEST = 26
    LIST_GAMES_REPLY = 27
    START_GAME_REQUEST = 28
    START_GAME_REPLY = 29
    END_GAME_REQUEST = 30
    END_GAME_REPLY = 31
    
    # Player management packets
    PLAYER_INFO_REQUEST = 40
    PLAYER_INFO_REPLY = 41
    UPDATE_PLAYER_REQUEST = 42
    UPDATE_PLAYER_REPLY = 43

@dataclass
class PacketHeader:
    """Common header for all packets."""
    type: PacketType = PacketType.LOGIN_REQUEST
    length: int = 0
    sequence: int = 0
    
    def pack(self) -> bytes:
        """Pack header into bytes."""
        return struct.pack("!HHH", 
            self.type,
            self.length,
            self.sequence
        )
    
    @classmethod
    def unpack(cls, data: bytes) -> 'PacketHeader':
        """Unpack header from bytes."""
        type_, length, sequence = struct.unpack("!HHH", data[:6])
        return cls(
            type=PacketType(type_),
            length=length,
            sequence=sequence
        )

class MetaserverPackets:
    """Packet handling for the metaserver."""
    
    HEADER_SIZE = 6  # Size of PacketHeader in bytes
    
    @staticmethod
    def encode_packet(packet_type: PacketType, sequence: int, payload: bytes) -> bytes:
        """Encode a packet with header and payload."""
        header = PacketHeader(
            type=packet_type,
            length=len(payload),
            sequence=sequence
        )
        return header.pack() + payload
    
    @staticmethod
    def decode_packet(data: bytes) -> tuple:
        """Decode a packet into header and payload.
        
        Returns:
            Tuple of (PacketHeader, payload bytes)
        """
        if len(data) < MetaserverPackets.HEADER_SIZE:
            raise ValueError("Packet too short")
            
        header = PacketHeader.unpack(data[:MetaserverPackets.HEADER_SIZE])
        payload = data[MetaserverPackets.HEADER_SIZE:]
        
        if len(payload) != header.length:
            raise ValueError("Packet length mismatch")
            
        return header, payload
    
    @staticmethod
    def encode_login_request(username: str, password: str) -> bytes:
        """Encode a login request packet."""
        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')
        return struct.pack(
            f"!H{len(username_bytes)}sH{len(password_bytes)}s",
            len(username_bytes),
            username_bytes,
            len(password_bytes),
            password_bytes
        )
    
    @staticmethod
    def decode_login_request(payload: bytes) -> tuple:
        """Decode a login request packet.
        
        Returns:
            Tuple of (username, password)
        """
        username_len = struct.unpack("!H", payload[:2])[0]
        username = payload[2:2+username_len].decode('utf-8')
        
        password_len = struct.unpack("!H", payload[2+username_len:4+username_len])[0]
        password = payload[4+username_len:4+username_len+password_len].decode('utf-8')
        
        return username, password
