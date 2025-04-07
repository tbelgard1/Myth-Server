"""
Room-related packet definitions for Myth metaserver.
Combines functionality from room_packets.py and related files.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional
import struct

from .base import Packet, PacketHeader, PacketBuilder
from ...models.room import RoomInfo
from ...models.player import BungieNetPlayerStats
from ...models.game import GameData
from ...models.stats import CasteBreakpointData, OverallRankingData
from ...models.buddy import BuddyEntry
from ...models.order import OrderMember

# Constants
ROOM_PASSWORD_SIZE = 16
ROOM_MAXIMUM_UPDATE_URL_SIZE = 256 
ROOM_MAXIMUM_MOTD_SIZE = 256
MAXIMUM_ROOMS = 128
MAXIMUM_ROOMS_PER_PLAYER = 24
MAXIMUM_PLAYER_NAME_LENGTH = 32

class RoomPacketType(IntEnum):
    """Types of room server packets"""
    # Server packets
    LOGIN_SUCCESSFUL = 0
    LOGIN_FAILURE = 1
    CLIENT_RANKING = 2
    MOTD_CHANGED = 3
    SEND_STATUS = 4
    ROOM_LIST = 5
    PLAYER_INFORMATION = 6
    UPDATE_BUDDY_RESPONSE = 7
    GLOBAL_MESSAGE = 8
    PING = 9

    # Client packets
    LOGIN = 10
    UPDATE_RANKING = 11
    UPDATE_ROOM_DATA = 12
    REQUEST_RANKING = 13
    STATUS = 14
    PUBLIC_ANNOUNCEMENT = 15
    PLAYER_INFORMATION_QUERY = 16
    UPDATE_BUDDY = 17
    PLAYER_ENTER_ROOM = 18
    PLAYER_LEAVE_ROOM = 19
    PLAYER_QUERY = 20
    UPDATE_PLAYER_INFORMATION = 21
    PLAYER_INFO_REQUEST = 22
    BAN_PLAYER = 23

    # Manually byte-swapped packets
    RANK_UPDATE = 24
    PLAYER_INFO_REPLY = 25
    UPDATE_ORDER_STATUS = 26
    PLAYER_QUERY_RESPONSE = 27
    SCORE_GAME = 28
    PLAYER_APPLICATION_TYPE = 29

class PlayerQueryType(IntEnum):
    """Types of player queries"""
    PLAYER_SEARCH = 0
    BUDDY = 1
    ORDER = 2

@dataclass
class RoomHeader(PacketHeader):
    """Header for room packets"""
    type: RoomPacketType = RoomPacketType.LOGIN

@dataclass
class LoginSuccessfulPacket(Packet):
    """Login successful response packet"""
    PACKET_TYPE = RoomPacketType.LOGIN_SUCCESSFUL
    identifier: int
    supported_application_flags: int
    player_data_size: int
    game_data_size: int
    ranked: bool
    tournament_room: bool
    caste_breakpoints: CasteBreakpointData
    url_for_version_update: str
    motd: str
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.LOGIN_SUCCESSFUL))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.identifier)
        builder.append_data(self.supported_application_flags)
        builder.append_data(self.player_data_size)
        builder.append_data(self.game_data_size)
        builder.append_data(self.ranked)
        builder.append_data(self.tournament_room)
        builder.append_data(self.caste_breakpoints)
        builder.append_data(self.url_for_version_update[:ROOM_MAXIMUM_UPDATE_URL_SIZE])
        builder.append_data(self.motd[:ROOM_MAXIMUM_MOTD_SIZE])
        return builder.get_packet()

@dataclass
class LoginPacket(Packet):
    """Login request packet"""
    PACKET_TYPE = RoomPacketType.LOGIN
    port: int
    identifier: int
    password: str
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.LOGIN))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.port)
        builder.append_data(self.identifier)
        builder.append_data(self.password[:ROOM_PASSWORD_SIZE])
        return builder.get_packet()

@dataclass
class PlayerInformationPacket(Packet):
    """Player information packet"""
    PACKET_TYPE = RoomPacketType.PLAYER_INFORMATION
    player_id: int
    buddies: List[BuddyEntry]
    order: int
    player_is_admin: bool
    player_is_bungie_employee: bool
    account_is_kiosk: bool
    country_code: int
    login_name: str
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.PLAYER_INFORMATION))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.player_id)
        builder.append_data(len(self.buddies))
        for buddy in self.buddies:
            builder.append_data(buddy)
        builder.append_data(self.order)
        builder.append_data(self.player_is_admin)
        builder.append_data(self.player_is_bungie_employee)
        builder.append_data(self.account_is_kiosk)
        builder.append_data(self.country_code)
        builder.append_data(self.login_name[:MAXIMUM_PLAYER_NAME_LENGTH])
        return builder.get_packet()

@dataclass
class UpdateBuddyResponsePacket(Packet):
    """Buddy list update response packet"""
    PACKET_TYPE = RoomPacketType.UPDATE_BUDDY_RESPONSE
    player_id: int
    buddies: List[BuddyEntry]
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.UPDATE_BUDDY_RESPONSE))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.player_id)
        builder.append_data(len(self.buddies))
        for buddy in self.buddies:
            builder.append_data(buddy)
        return builder.get_packet()

@dataclass
class UpdateOrderStatusPacket(Packet):
    """Order status update packet"""
    PACKET_TYPE = RoomPacketType.UPDATE_ORDER_STATUS
    player_id: int
    members: List[OrderMember]
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.UPDATE_ORDER_STATUS))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.player_id)
        builder.append_data(len(self.members))
        for member in self.members:
            builder.append_data(member)
        return builder.get_packet()

@dataclass
class PlayerInfoReplyPacket(Packet):
    """Player info reply packet"""
    PACKET_TYPE = RoomPacketType.PLAYER_INFO_REPLY
    player_id: int
    stats: BungieNetPlayerStats
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.PLAYER_INFO_REPLY))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.player_id)
        builder.append_data(self.stats)
        return builder.get_packet()

@dataclass 
class GlobalMessagePacket(Packet):
    """Global message packet"""
    PACKET_TYPE = RoomPacketType.GLOBAL_MESSAGE
    player_id: int
    message: str
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.GLOBAL_MESSAGE))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.player_id)
        builder.append_data(self.message)
        return builder.get_packet()

@dataclass
class RankUpdatePacket(Packet):
    """Rank update packet"""
    PACKET_TYPE = RoomPacketType.RANK_UPDATE
    caste_breakpoints: CasteBreakpointData
    overall_rank: OverallRankingData
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.RANK_UPDATE))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.caste_breakpoints)
        builder.append_data(self.overall_rank)
        return builder.get_packet()

@dataclass
class ScoreGamePacket(Packet):
    """Game score packet"""
    PACKET_TYPE = RoomPacketType.SCORE_GAME
    game: GameData
    header: RoomHeader = field(default_factory=lambda: RoomHeader(RoomPacketType.SCORE_GAME))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, RoomHeader)
        builder.append_data(self.game)
        return builder.get_packet()
