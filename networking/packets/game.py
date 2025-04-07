"""
Game-related packet definitions for Myth metaserver.
Combines functionality from game_search_packets.py and related files.
"""

from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import List, Optional

from .base import Packet, PacketHeader, PacketBuilder
from ...models.game import MetaserverGameDescription, MetaserverGameAuxData

# Port constants
DEFAULT_GAME_SEARCH_PORT = 7980
DEMO_GAME_SEARCH_PORT = 7981

class GameFlags(IntFlag):
    """Game state flags"""
    IN_PROGRESS = 1 << 0
    HAS_PASSWORD = 1 << 1
    INVALID = 1 << 2
    IS_TOURNAMENT_ROUND = 1 << 3
    IS_CLOSED = 1 << 4

class GameOptions(IntFlag):
    """Game options flags"""
    RANDOM_ENDGAME_COUNTDOWN = 1 << 0
    ALLOW_MULTIPLAYER_TEAMS = 1 << 1
    LIMITED_VISIBILITY = 1 << 2
    NO_INGAME_RANKING = 1 << 3
    ALLOW_UNIT_TRADING = 1 << 4
    ALLOW_VETERANS = 1 << 5
    ALLOW_ALLIANCES = 1 << 13
    ALLOW_OVERHEAD_MAP = 1 << 14
    ORDER_GAME = 1 << 15
    SERVER_IS_OBSERVER = 1 << 16
    DEATHMATCH = 1 << 20
    VTFL = 1 << 21
    ANTICLUMP = 1 << 22
    TEAM_CAPTAIN_CHOSEN = 1 << 23
    METASERVER_HOSTED = 1 << 24

class GameType(IntEnum):
    """Game types"""
    BODY_COUNT = 0
    STEAL_THE_BACON = 1
    LAST_MAN_ON_THE_HILL = 2
    SCAVENGER_HUNT = 3
    FLAG_RALLY = 4
    CAPTURE_THE_FLAG = 5
    BALLS_ON_PARADE = 6
    TERRITORIES = 7
    CAPTURES = 8
    KING_OF_THE_HILL = 9
    STAMPEDE = 10
    ASSASSINATION = 11
    HUNTING = 12
    CUSTOM_SCORING = 13
    KING_OF_THE_HILL_TFL = 14

class GameSearchPacketType(IntEnum):
    """Game search packet types"""
    LOGIN = 0
    UPDATE = 1
    QUERY = 2
    QUERY_RESPONSE = 3

class UpdateType(IntEnum):
    """Game update types"""
    ADD_NEW_GAME = 0
    CHANGE_GAME_INFO = 1
    REMOVE_GAME = 2

@dataclass
class GameSearchHeader(PacketHeader):
    """Header for game search packets"""
    type: GameSearchPacketType = GameSearchPacketType.LOGIN

@dataclass
class LoginPacket(Packet):
    """Login packet for game search server"""
    PACKET_TYPE = GameSearchPacketType.LOGIN
    room_id: int
    header: GameSearchHeader = field(default_factory=lambda: GameSearchHeader(GameSearchPacketType.LOGIN))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, GameSearchHeader)
        builder.append_data(self.room_id)
        return builder.get_packet()

    @classmethod
    def unpack(cls, data: bytes) -> 'LoginPacket':
        header = GameSearchHeader.unpack(data[:4])
        room_id = struct.unpack('<l', data[4:8])[0]
        return cls(room_id=room_id, header=header)

@dataclass
class UpdatePacket(Packet):
    """Update packet for game info"""
    PACKET_TYPE = GameSearchPacketType.UPDATE
    type: UpdateType
    room_id: int
    game_is_ranked: bool
    aux_data: MetaserverGameAuxData
    game: MetaserverGameDescription
    header: GameSearchHeader = field(default_factory=lambda: GameSearchHeader(GameSearchPacketType.UPDATE))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, GameSearchHeader)
        builder.append_data(self.type)
        builder.append_data(self.room_id)
        builder.append_data(self.game_is_ranked)
        builder.append_data(self.aux_data)
        builder.append_data(self.game)
        return builder.get_packet()

    @classmethod
    def unpack(cls, data: bytes) -> 'UpdatePacket':
        header = GameSearchHeader.unpack(data[:4])
        offset = 4
        
        type_, room_id = struct.unpack('<ll', data[offset:offset+8])
        offset += 8
        
        game_is_ranked = bool(struct.unpack('<?', data[offset:offset+1])[0])
        offset += 1
        
        aux_data = MetaserverGameAuxData.unpack(data[offset:])
        offset += aux_data.size()
        
        game = MetaserverGameDescription.unpack(data[offset:])
        
        return cls(
            type=UpdateType(type_),
            room_id=room_id,
            game_is_ranked=game_is_ranked,
            aux_data=aux_data,
            game=game,
            header=header
        )

@dataclass
class QueryPacket(Packet):
    """Query packet for searching games"""
    PACKET_TYPE = GameSearchPacketType.QUERY
    player_id: int
    game_type: GameType
    game_scoring: bool = False
    unit_trading: bool = False
    veterans: bool = False
    teams: bool = False
    alliances: bool = False
    enemy_visibility: bool = False
    header: GameSearchHeader = field(default_factory=lambda: GameSearchHeader(GameSearchPacketType.QUERY))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, GameSearchHeader)
        builder.append_data(self.player_id)
        builder.append_data(self.game_type)
        builder.append_data(self.game_scoring)
        builder.append_data(self.unit_trading)
        builder.append_data(self.veterans)
        builder.append_data(self.teams)
        builder.append_data(self.alliances)
        builder.append_data(self.enemy_visibility)
        return builder.get_packet()

    @classmethod
    def unpack(cls, data: bytes) -> 'QueryPacket':
        header = GameSearchHeader.unpack(data[:4])
        player_id, game_type, scoring, trading, vets, teams, alliances, visibility = \
            struct.unpack('<L7?', data[4:15])
        return cls(
            player_id=player_id,
            game_type=GameType(game_type),
            game_scoring=bool(scoring),
            unit_trading=bool(trading),
            veterans=bool(vets),
            teams=bool(teams),
            alliances=bool(alliances),
            enemy_visibility=bool(visibility),
            header=header
        )

@dataclass
class QueryResponseSegment:
    """Single game response in query response packet"""
    room_id: int
    game_is_ranked: bool
    aux_data: MetaserverGameAuxData
    game: MetaserverGameDescription

    def pack(self) -> bytes:
        game_data = self.game.pack()
        aux_data = self.aux_data.pack()
        
        length = 4 + 4 + 1 + len(aux_data) + 4 + len(game_data)
        data = struct.pack('<iil?',
            length,
            self.room_id,
            self.game_is_ranked
        )
        data += aux_data
        data += struct.pack('<i', len(game_data))
        data += game_data
        
        # Pad to 4-byte boundary
        pad = length % 4
        if pad:
            data += b'\0' * (4 - pad)
            
        return data

    @classmethod
    def unpack(cls, data: bytes) -> tuple['QueryResponseSegment', int]:
        offset = 0
        length, room_id, game_is_ranked = struct.unpack('<iil?', data[offset:offset+13])
        offset += 13
        
        aux_data = MetaserverGameAuxData.unpack(data[offset:])
        offset += aux_data.size()
        
        game_len = struct.unpack('<i', data[offset:offset+4])[0]
        offset += 4
        
        game = MetaserverGameDescription.unpack(data[offset:offset+game_len])
        offset += game_len
        
        # Skip padding
        pad = length % 4
        if pad:
            offset += 4 - pad
            
        return cls(room_id, bool(game_is_ranked), aux_data, game), offset

@dataclass
class QueryResponsePacket(Packet):
    """Response packet containing matching games"""
    PACKET_TYPE = GameSearchPacketType.QUERY_RESPONSE
    player_id: int
    segments: List[QueryResponseSegment] = field(default_factory=list)
    header: GameSearchHeader = field(default_factory=lambda: GameSearchHeader(GameSearchPacketType.QUERY_RESPONSE))

    def pack(self) -> bytes:
        builder = PacketBuilder(self.PACKET_TYPE, GameSearchHeader)
        builder.append_data(len(self.segments))
        builder.append_data(self.player_id)
        
        for segment in self.segments:
            builder.append_data(segment.pack())
            
        return builder.get_packet()

    @classmethod
    def unpack(cls, data: bytes) -> 'QueryResponsePacket':
        header = GameSearchHeader.unpack(data[:4])
        offset = 4
        
        num_responses, player_id = struct.unpack('<iL', data[offset:offset+8])
        offset += 8
        
        segments = []
        for _ in range(num_responses):
            segment, bytes_read = QueryResponseSegment.unpack(data[offset:])
            segments.append(segment)
            offset += bytes_read
            
        return cls(player_id=player_id, segments=segments, header=header)
