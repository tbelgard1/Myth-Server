"""
Common data structures for the Myth metaserver.

This module defines the core data structures used throughout the metaserver,
including network addresses, colors, and other common types.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import socket
import struct

@dataclass
class RGBColor:
    """RGB color representation."""
    red: int = 0
    green: int = 0
    blue: int = 0

@dataclass
class NetworkAddress:
    """Network address representation."""
    host: int = 0  # IP address as integer
    port: int = 0
    
    @classmethod
    def from_socket_address(cls, addr: tuple) -> 'NetworkAddress':
        """Create NetworkAddress from a socket address tuple (host, port)."""
        try:
            host_bytes = socket.inet_aton(addr[0])
            host = struct.unpack("!L", host_bytes)[0]
            return cls(host=host, port=addr[1])
        except socket.error:
            return cls()
    
    def to_socket_address(self) -> tuple:
        """Convert to socket address tuple (host, port)."""
        try:
            host_bytes = struct.pack("!L", self.host)
            host = socket.inet_ntoa(host_bytes)
            return (host, self.port)
        except socket.error:
            return ("0.0.0.0", 0)

@dataclass
class MetaserverCommonStructs:
    """Container for common metaserver data structures."""
    # Network constants
    MAXIMUM_PACKET_LENGTH: int = 32767
    MAXIMUM_LOGIN_LENGTH: int = 31
    MAXIMUM_PASSWORD_LENGTH: int = 31
    MAXIMUM_DESCRIPTION_LENGTH: int = 255
    
    # Game constants
    MAXIMUM_PLAYERS_PER_GAME: int = 8
    MAXIMUM_TEAMS_PER_GAME: int = 4
    MAXIMUM_ROOMS: int = 32
    
    # Version information
    MINIMUM_PROTOCOL_VERSION: int = 1
    CURRENT_PROTOCOL_VERSION: int = 3
    
    # Status codes
    STATUS_OK: int = 0
    STATUS_ERROR: int = 1
    STATUS_VERSION_TOO_OLD: int = 2
    STATUS_INVALID_LOGIN: int = 3
    STATUS_ALREADY_LOGGED_IN: int = 4
    STATUS_ROOM_FULL: int = 5
    STATUS_GAME_FULL: int = 6
    STATUS_GAME_STARTED: int = 7
    STATUS_GAME_NOT_FOUND: int = 8
    STATUS_INVALID_PARAMETERS: int = 9
    STATUS_INVALID_TEAM: int = 10
