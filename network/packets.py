"""
Network packet definitions and handling for metaserver communication.

This module contains packet types, builders, and parsers for the metaserver
protocol, including:
- Packet headers and types
- Packet building helpers
- Network stream parsing
- Packet byte swapping
"""

import enum
import struct
import dataclasses
from typing import Optional, List, Dict, Any, Union, TypeVar, Generic
import logging
import io

from core.security.authentication import AuthenticationToken
from core.utils.byte_swapping import swap_bytes_16, swap_bytes_32
from core.models.metaserver_structs import (
    MetaserverPlayerAuxData,
    MetaserverGameAuxData,
    RoomInfo,
    DataChunkIdentifierData
)

logger = logging.getLogger(__name__)

# Constants
MAXIMUM_METASERVER_APPLICATION_NAME = 31
MAXIMUM_METASERVER_BUILD_DATE = 31
MAXIMUM_METASERVER_BUILD_TIME = 31
NUMBER_OF_SCORING_DATUMS_IN_PLAYER_INFO_PACKET = 36
PACKET_IDENTIFIER = 0xDEAD
METASERVER_PACKET_VERSION = 1
FIRST_CLIENT_PACKET_ID = 100
FIRST_BOTH_PACKET_ID = 200

class PacketType(enum.IntEnum):
    """Types of metaserver packets"""
    # Server packets (0-99)
    ROOM_LIST = 0
    PLAYER_LIST = 1
    GAME_LIST = 2
    SERVER_MESSAGE = 3
    URL = 4
    DATA_CHUNK = 5
    PASSWORD_CHALLENGE = 6
    USER_SUCCESSFUL_LOGIN = 7
    SET_PLAYER_DATA_FROM_METASERVER = 8
    ROOM_LOGIN_SUCCESSFUL = 9
    MESSAGE_OF_THE_DAY = 10
    PATCH = 11
    SEND_VERSIONS = 12
    GAME_LIST_PREF = 13
    PLAYER_SEARCH_LIST = 14
    BUDDY_LIST = 15
    ORDER_LIST = 16
    PLAYER_INFO = 17
    UPDATE_INFO = 18
    UPDATE_PLAYER_BUDDY_LIST = 19
    UPDATE_ORDER_MEMBER_LIST = 20
    YOU_JUST_GOT_BLAMMED_SUCKA = 21

    # Client packets (100-199)
    LOGIN = FIRST_CLIENT_PACKET_ID
    ROOM_LOGIN = 101
    LOGOUT = 102
    SET_PLAYER_DATA = 103
    CREATE_GAME = 104
    REMOVE_GAME = 105
    CHANGE_ROOM = 106
    SET_PLAYER_MODE = 107
    DATA_CHUNK_REPLY = 108
    PASSWORD_RESPONSE = 109
    REQUEST_FULL_UPDATE = 110
    GAME_PLAYER_LIST = 111
    GAME_SCORE = 112
    RESET_GAME = 113
    START_GAME = 114
    VERSION_CONTROL = 115
    GAME_SEARCH_QUERY = 116
    PLAYER_SEARCH_QUERY = 117
    BUDDY_QUERY = 118
    ORDER_QUERY = 119
    UPDATE_BUDDY = 120
    PLAYER_INFO_QUERY = 121
    UPDATE_PLAYER_INFORMATION = 122

    # Both packets (200+)
    ROOM_BROADCAST = FIRST_BOTH_PACKET_ID
    DIRECTED_DATA = 201
    KEEPALIVE = 202
    SESSION_KEY = 203

@dataclasses.dataclass
class CircularBuffer:
    """Circular buffer for network data"""
    buffer: bytearray
    size: int
    read_index: int = 0
    write_index: int = 0

    @property
    def written_size(self) -> int:
        """Get amount of data written"""
        if self.read_index <= self.write_index:
            return self.write_index - self.read_index
        return self.size - self.read_index + self.write_index

    def increment_read_index(self) -> None:
        """Increment read index with wraparound"""
        self.read_index = (self.read_index + 1) % self.size

@dataclasses.dataclass
class PacketHeader:
    """Common header for all packets"""
    packet_identifier: int = PACKET_IDENTIFIER
    type: PacketType = PacketType.ROOM_LIST
    length: int = 0

    def pack(self) -> bytes:
        """Pack header into bytes"""
        return struct.pack('<HHl', self.packet_identifier, self.type, self.length)

    @classmethod
    def unpack(cls, data: bytes) -> 'PacketHeader':
        """Unpack header from bytes"""
        identifier, type_, length = struct.unpack('<HHl', data[:8])
        return cls(identifier, PacketType(type_), length)

class PacketBuilder:
    """Helper for building packets"""
    def __init__(self, packet_type: PacketType):
        self.header = PacketHeader(type=packet_type)
        self.buffer = io.BytesIO()
        self.buffer.write(self.header.pack())

    def append_data(self, data: Union[bytes, Any]) -> None:
        """Append data to packet
        
        Args:
            data: Data to append, either bytes or an object with pack() method
        """
        if isinstance(data, bytes):
            self.buffer.write(data)
        elif hasattr(data, 'pack'):
            self.buffer.write(data.pack())
        else:
            raise ValueError(f"Cannot append data of type {type(data)}")

    def get_packet(self) -> bytes:
        """Get complete packet bytes"""
        data = self.buffer.getvalue()
        self.header.length = len(data) - 8  # Subtract header size
        return self.header.pack() + data[8:]

def build_empty_header(packet_type: PacketType) -> bytes:
    """Build packet with just a header
    
    Args:
        packet_type: Type of packet
        
    Returns:
        Packet bytes
    """
    builder = PacketBuilder(packet_type)
    return builder.get_packet()

def parse_network_stream(buffer: CircularBuffer,
                        header: PacketHeader) -> bool:
    """Parse packet from network stream
    
    Args:
        buffer: Network data buffer
        header: Header to fill in
        
    Returns:
        True if complete packet found
    """
    # Need at least header size
    if buffer.written_size < 8:
        return False

    # Read header
    header_bytes = bytes(buffer.buffer[buffer.read_index:buffer.read_index+8])
    parsed_header = PacketHeader.unpack(header_bytes)

    # Validate identifier
    if parsed_header.packet_identifier != PACKET_IDENTIFIER:
        logger.error(f"Invalid packet identifier: {parsed_header.packet_identifier}")
        buffer.increment_read_index()
        return False

    # Check if we have complete packet
    total_size = parsed_header.length + 8
    if buffer.written_size < total_size:
        return False

    # Copy header
    header.packet_identifier = parsed_header.packet_identifier
    header.type = parsed_header.type
    header.length = parsed_header.length

    return True

# Server packet builders
def build_room_packet() -> bytes:
    """Build empty room list packet"""
    return build_empty_header(PacketType.ROOM_LIST)

def add_room_data(packet: bytes, room: RoomInfo) -> bytes:
    """Add room info to packet
    
    Args:
        packet: Existing packet bytes
        room: Room info to add
        
    Returns:
        Updated packet bytes
    """
    builder = PacketBuilder(PacketType.ROOM_LIST)
    builder.append_data(packet[8:])  # Skip header
    builder.append_data(room)
    return builder.get_packet()

def build_player_info_query(player_id: int) -> bytes:
    """Build player info query packet
    
    Args:
        player_id: ID of player to query
        
    Returns:
        Query packet bytes
    """
    builder = PacketBuilder(PacketType.PLAYER_INFO_QUERY)
    builder.append_data(struct.pack('<L', player_id))
    return builder.get_packet()

def build_order_query_packet(order: int) -> bytes:
    """Build order query packet
    
    Args:
        order: Order to query
        
    Returns:
        Query packet bytes
    """
    builder = PacketBuilder(PacketType.ORDER_QUERY)
    builder.append_data(struct.pack('<h', order))
    return builder.get_packet()

def build_buddy_query_packet() -> bytes:
    """Build buddy list query packet
    
    Returns:
        Query packet bytes
    """
    return build_empty_header(PacketType.BUDDY_QUERY)

def start_building_list_packet(packet_type: PacketType) -> bytes:
    """Start building a list packet
    
    Args:
        packet_type: Type of list packet
        
    Returns:
        Initial packet bytes
    """
    return build_empty_header(packet_type)

def add_player_data_to_packet(packet: bytes,
                            aux_data: MetaserverPlayerAuxData,
                            player_data: Any,
                            room_id: Optional[int] = None,
                            packet_type: Optional[PacketType] = None) -> bytes:
    """Add player data to a packet
    
    Args:
        packet: Existing packet bytes
        aux_data: Player auxiliary data
        player_data: Player data object
        room_id: Optional room ID for search/buddy packets
        packet_type: Optional packet type override
        
    Returns:
        Updated packet bytes
    """
    if packet_type is None:
        packet_type = PacketType(packet[2])

    builder = PacketBuilder(packet_type)
    builder.append_data(packet[8:])  # Skip header

    if room_id is not None:
        builder.append_data(struct.pack('<H', room_id))

    builder.append_data(aux_data)
    builder.append_data(player_data)

    return builder.get_packet()

def build_game_list_packet(preferences: bool = False) -> bytes:
    """Build game list packet
    
    Args:
        preferences: Whether to include preferences
        
    Returns:
        Game list packet bytes
    """
    packet_type = PacketType.GAME_LIST_PREF if preferences else PacketType.GAME_LIST
    return build_empty_header(packet_type)

def add_game_data_to_packet(packet: bytes,
                           aux_data: MetaserverGameAuxData,
                           game_data: Any) -> bytes:
    """Add game data to a packet
    
    Args:
        packet: Existing packet bytes
        aux_data: Game auxiliary data
        game_data: Game data object
        
    Returns:
        Updated packet bytes
    """
    builder = PacketBuilder(PacketType(packet[2]))
    builder.append_data(packet[8:])  # Skip header
    builder.append_data(aux_data)
    builder.append_data(game_data)
    return builder.get_packet()

def build_room_login_successful_packet(user_id: int,
                                     max_players: int) -> bytes:
    """Build room login success packet
    
    Args:
        user_id: User ID
        max_players: Maximum players allowed
        
    Returns:
        Login success packet bytes
    """
    builder = PacketBuilder(PacketType.ROOM_LOGIN_SUCCESSFUL)
    builder.append_data(struct.pack('<Lh', user_id, max_players))
    return builder.get_packet()

def build_data_chunk_packet(chunk_id: DataChunkIdentifierData,
                          data: bytes) -> bytes:
    """Build data chunk packet
    
    Args:
        chunk_id: Chunk identifier
        data: Chunk data
        
    Returns:
        Data chunk packet bytes
    """
    builder = PacketBuilder(PacketType.DATA_CHUNK)
    builder.append_data(chunk_id)
    builder.append_data(data)
    return builder.get_packet()

def build_password_challenge_packet(auth_type: int,
                                  salt: bytes) -> bytes:
    """Build password challenge packet
    
    Args:
        auth_type: Authentication type
        salt: Challenge salt
        
    Returns:
        Challenge packet bytes
    """
    builder = PacketBuilder(PacketType.PASSWORD_CHALLENGE)
    builder.append_data(struct.pack('<h', auth_type))
    builder.append_data(salt)
    return builder.get_packet()

def build_user_login_successful_packet(user_id: int,
                                     order: int,
                                     token: AuthenticationToken) -> bytes:
    """Build user login success packet
    
    Args:
        user_id: User ID
        order: Order index
        token: Authentication token
        
    Returns:
        Login success packet bytes
    """
    builder = PacketBuilder(PacketType.USER_SUCCESSFUL_LOGIN)
    builder.append_data(struct.pack('<lh', user_id, order))
    builder.append_data(token)
    return builder.get_packet()

def build_set_player_data_packet(player: MetaserverPlayerAuxData,
                                data: bytes) -> bytes:
    """Build set player data packet
    
    Args:
        player: Player auxiliary data
        data: Player data
        
    Returns:
        Set data packet bytes
    """
    builder = PacketBuilder(PacketType.SET_PLAYER_DATA_FROM_METASERVER)
    builder.append_data(player)
    builder.append_data(data)
    return builder.get_packet()

def build_message_packet(message: str,
                        packet_type: PacketType = PacketType.MESSAGE_OF_THE_DAY) -> bytes:
    """Build message packet
    
    Args:
        message: Message text
        packet_type: Type of message packet
        
    Returns:
        Message packet bytes
    """
    builder = PacketBuilder(packet_type)
    builder.append_data((message + '\0').encode('utf-8'))
    return builder.get_packet()

def build_versions_packet() -> bytes:
    """Build versions info packet
    
    Returns:
        Versions packet bytes
    """
    return build_empty_header(PacketType.SEND_VERSIONS)

def byte_swap_packet(packet: bytes, outgoing: bool = True) -> bytes:
    """Swap bytes in packet for endianness
    
    Args:
        packet: Packet bytes
        outgoing: Whether packet is outgoing
        
    Returns:
        Byte-swapped packet
    """
    header = PacketHeader.unpack(packet[:8])
    packet_type = header.type
    
    # Different types need different swapping
    if packet_type in (
        PacketType.GAME_LIST,
        PacketType.GAME_LIST_PREF
    ):
        # Swap game entries
        offset = 8  # Skip header
        while offset < len(packet):
            aux_data = MetaserverGameAuxData.unpack(packet[offset:offset+12])
            game_size = swap_bytes_16(aux_data.game_data_size) if outgoing else aux_data.game_data_size
            
            # Swap aux data
            swapped = aux_data.byte_swap()
            packet = packet[:offset] + swapped + packet[offset+12:]
            
            offset += 12 + game_size
            
    elif packet_type == PacketType.DATA_CHUNK:
        # Swap header and chunk ID
        chunk_id = DataChunkIdentifierData.unpack(packet[8:24])
        swapped = chunk_id.byte_swap()
        packet = packet[:8] + swapped + packet[24:]
        
    # Always swap header
    swapped_header = header.byte_swap()
    packet = swapped_header + packet[8:]
    
    return packet
