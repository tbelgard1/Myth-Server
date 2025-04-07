"""
Packet system for Myth metaserver.
Provides a unified interface for all network packets.
"""

from .base import Packet, PacketHeader, PacketBuilder
from .game import (
    GameSearchPacketType, GameType, GameFlags, GameOptions,
    LoginPacket as GameLoginPacket,
    UpdatePacket as GameUpdatePacket,
    QueryPacket as GameQueryPacket,
    QueryResponsePacket as GameQueryResponsePacket
)
from .room import (
    RoomPacketType, PlayerQueryType,
    LoginPacket as RoomLoginPacket,
    LoginSuccessfulPacket,
    PlayerInformationPacket,
    UpdateBuddyResponsePacket,
    UpdateOrderStatusPacket,
    PlayerInfoReplyPacket,
    GlobalMessagePacket,
    RankUpdatePacket,
    ScoreGamePacket
)

__all__ = [
    # Base classes
    'Packet',
    'PacketHeader',
    'PacketBuilder',
    
    # Game packets
    'GameSearchPacketType',
    'GameType',
    'GameFlags',
    'GameOptions',
    'GameLoginPacket',
    'GameUpdatePacket',
    'GameQueryPacket',
    'GameQueryResponsePacket',
    
    # Room packets
    'RoomPacketType',
    'PlayerQueryType',
    'RoomLoginPacket',
    'LoginSuccessfulPacket',
    'PlayerInformationPacket',
    'UpdateBuddyResponsePacket',
    'UpdateOrderStatusPacket',
    'PlayerInfoReplyPacket',
    'GlobalMessagePacket',
    'RankUpdatePacket',
    'ScoreGamePacket'
]
