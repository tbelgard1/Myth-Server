"""
Core data structures for metaserver communication.

This module contains the data structures used for communication between
the metaserver and clients, including:
- Player data
- Game data
- Room information
- Query/response structures
- Version information
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import IntFlag, IntEnum
import struct

# Constants
MAXIMUM_METASERVER_GAME_NAME = 31
MAXIMUM_METASERVER_GAME_DATA_SIZE = 1024
MAXIMUM_METASERVER_PLAYER_DATA_SIZE = 128
MAXIMUM_METASERVER_USERNAME = 31
MAXIMUM_METASERVER_ORDERNAME = 31
MAXIMUM_METASERVER_PASSWORD = 15
MOTD_CHANGE_LOGIN_KEY_SIZE = 8
MOTD_QUERY_LOGIN_KEY_SIZE = 8
MAXIMUM_MOTD_SIZE = 127
MAXIMUM_USERS_PER_ROOM = 64
MAXIMUM_TEAMS_PER_MAP = 16
MAXIMUM_PLAYERS_PER_MAP = 16
MAXIMUM_PLAYERS_PER_METASERVER_HOSTED_GAME = 16

NETWORK_GAME_NAME_LENGTH = 31
NETWORK_MAP_NAME_LENGTH = 63

# Player flags for metaserver_player_aux_data.flags
class AuxPlayerFlags(IntFlag):
    """Auxiliary player flags"""
    ADMIN = 1 << 0  # Player is an administrator
    ANONYMOUS = 1 << 1  # Player is a guest
    BUNGIE_ICON = 1 << 2  # Player has the bungie caste icon

NUM_AUX_PLAYER_FLAGS = 3

class PlayerVerb(IntEnum):
    """Player verbs"""
    ADD = 0
    DELETE = 1
    CHANGE = 2

class GameVerb(IntEnum):
    """Game verbs"""
    ADD = 0
    DELETE = 1
    CHANGE = 2

@dataclass
class MetaserverPlayerAuxData:
    """Auxiliary data for metaserver players"""
    verb: PlayerVerb
    flags: AuxPlayerFlags
    ranking: int
    player_id: int
    room_id: int
    caste: int
    player_data_length: int
    order: int
    pad: int = 0

    def pack(self) -> bytes:
        """Pack data into bytes"""
        return struct.pack('<HHLLHHHH',
            self.verb, self.flags, self.ranking, self.player_id,
            self.room_id, self.caste, self.player_data_length,
            self.order)

    @classmethod
    def unpack(cls, data: bytes) -> 'MetaserverPlayerAuxData':
        """Unpack data from bytes"""
        values = struct.unpack('<HHLLHHHH', data)
        return cls(
            verb=PlayerVerb(values[0]),
            flags=AuxPlayerFlags(values[1]),
            ranking=values[2],
            player_id=values[3],
            room_id=values[4],
            caste=values[5],
            player_data_length=values[6],
            order=values[7]
        )

class DataChunkFlags(IntFlag):
    """Data chunk flags"""
    IS_LAST_CHUNK = 1 << 0

@dataclass
class DataChunkIdentifierData:
    """Data chunk identifier"""
    flags: DataChunkFlags
    type: int
    offset: int
    length: int

    def pack(self) -> bytes:
        """Pack data into bytes"""
        return struct.pack('<LLLL',
            self.flags, self.type, self.offset, self.length)

    @classmethod
    def unpack(cls, data: bytes) -> 'DataChunkIdentifierData':
        """Unpack data from bytes"""
        flags, type_, offset, length = struct.unpack('<LLLL', data)
        return cls(DataChunkFlags(flags), type_, offset, length)

class RoomType(IntEnum):
    """Room types"""
    UNRANKED = 0
    RANKED = 1
    TOURNAMENT = 2

@dataclass
class RoomInfo:
    """Room information"""
    room_id: int
    player_count: int
    host: int
    port: int
    game_count: int
    room_type: RoomType
    unused: List[int] = None

    def __post_init__(self):
        if self.unused is None:
            self.unused = [0] * 5

    def pack(self) -> bytes:
        """Pack data into bytes"""
        return struct.pack('<HHLHHh5h',
            self.room_id, self.player_count, self.host,
            self.port, self.game_count, self.room_type,
            *self.unused)

    @classmethod
    def unpack(cls, data: bytes) -> 'RoomInfo':
        """Unpack data from bytes"""
        values = struct.unpack('<HHLHHh5h', data)
        return cls(
            room_id=values[0],
            player_count=values[1],
            host=values[2],
            port=values[3],
            game_count=values[4],
            room_type=RoomType(values[5]),
            unused=list(values[6:])
        )

@dataclass
class PlayerListPacketEntry:
    """Player list packet entry"""
    player_id: int

    def pack(self) -> bytes:
        """Pack data into bytes"""
        return struct.pack('<L', self.player_id)

    @classmethod
    def unpack(cls, data: bytes) -> 'PlayerListPacketEntry':
        """Unpack data from bytes"""
        player_id = struct.unpack('<L', data)[0]
        return cls(player_id)

@dataclass
class ScoreListPacketEntry:
    """Score list packet entry"""
    player_id: int
    place: int
    kills: int
    casualties: int
    points_killed: int
    points_lost: int
    unused: List[int] = None

    def __post_init__(self):
        if self.unused is None:
            self.unused = [0] * 2

    def pack(self) -> bytes:
        """Pack data into bytes"""
        return struct.pack('<LHHHll2l',
            self.player_id, self.place, self.kills,
            self.casualties, self.points_killed,
            self.points_lost, *self.unused)

    @classmethod
    def unpack(cls, data: bytes) -> 'ScoreListPacketEntry':
        """Unpack data from bytes"""
        values = struct.unpack('<LHHHll2l', data)
        return cls(
            player_id=values[0],
            place=values[1],
            kills=values[2],
            casualties=values[3],
            points_killed=values[4],
            points_lost=values[5],
            unused=list(values[6:])
        )

@dataclass
class MetaserverGameAuxData:
    """Auxiliary data for metaserver games"""
    game_id: int
    host: int
    port: int
    verb: GameVerb
    version: int
    seconds_remaining: int
    creating_player_id: int
    game_data_size: int
    unused_short: int = 0
    unused: List[int] = None

    def __post_init__(self):
        if self.unused is None:
            self.unused = [0] * 3

    def pack(self) -> bytes:
        """Pack data into bytes"""
        return struct.pack('<LLHHHlLHh3l',
            self.game_id, self.host, self.port, self.verb,
            self.version, self.seconds_remaining,
            self.creating_player_id, self.game_data_size,
            self.unused_short, *self.unused)

    @classmethod
    def unpack(cls, data: bytes) -> 'MetaserverGameAuxData':
        """Unpack data from bytes"""
        values = struct.unpack('<LLHHHlLHh3l', data)
        return cls(
            game_id=values[0],
            host=values[1],
            port=values[2],
            verb=GameVerb(values[3]),
            version=values[4],
            seconds_remaining=values[5],
            creating_player_id=values[6],
            game_data_size=values[7],
            unused_short=values[8],
            unused=list(values[9:])
        )

MAXIMUM_GAME_SEARCH_RESPONSES = 5

@dataclass
class Query:
    """Game query"""
    game_name: str = ""
    map_name: str = ""
    game_type: int = 0
    game_scoring: int = 0
    unit_trading: int = 0
    veterans: int = 0
    alliances: int = 0
    enemy_visibility: int = 0

    def pack(self) -> bytes:
        """Pack data into bytes"""
        game_name = self.game_name.ljust(NETWORK_GAME_NAME_LENGTH + 1, '\0')
        map_name = self.map_name.ljust(NETWORK_MAP_NAME_LENGTH + 1, '\0')
        return struct.pack(f'<{NETWORK_GAME_NAME_LENGTH + 1}s{NETWORK_MAP_NAME_LENGTH + 1}s6h',
            game_name.encode(), map_name.encode(),
            self.game_type, self.game_scoring,
            self.unit_trading, self.veterans,
            self.alliances, self.enemy_visibility)

    @classmethod
    def unpack(cls, data: bytes) -> 'Query':
        """Unpack data from bytes"""
        fmt = f'<{NETWORK_GAME_NAME_LENGTH + 1}s{NETWORK_MAP_NAME_LENGTH + 1}s6h'
        values = struct.unpack(fmt, data)
        return cls(
            game_name=values[0].decode().rstrip('\0'),
            map_name=values[1].decode().rstrip('\0'),
            game_type=values[2],
            game_scoring=values[3],
            unit_trading=values[4],
            veterans=values[5],
            alliances=values[6],
            enemy_visibility=values[7]
        )

@dataclass
class QueryResponse:
    """Game query response"""
    data_index: int
    match_value: int
    room_id: int
    game_is_ranked: bool
    aux_data: MetaserverGameAuxData
    game_data_length: int
    game: 'MetaserverGameDescription'  # Forward reference
    game_name: str = ""
    map_name: str = ""

    def pack(self) -> bytes:
        """Pack data into bytes"""
        game_name = self.game_name.ljust(NETWORK_GAME_NAME_LENGTH + 1, '\0')
        map_name = self.map_name.ljust(NETWORK_MAP_NAME_LENGTH + 1, '\0')
        return struct.pack(f'<LLLb',
            self.data_index, self.match_value,
            self.room_id, self.game_is_ranked) + \
            self.aux_data.pack() + \
            struct.pack('<l', self.game_data_length) + \
            self.game.pack() + \
            struct.pack(f'<{NETWORK_GAME_NAME_LENGTH + 1}s{NETWORK_MAP_NAME_LENGTH + 1}s',
                game_name.encode(), map_name.encode())

    @classmethod
    def unpack(cls, data: bytes) -> 'QueryResponse':
        """Unpack data from bytes"""
        offset = 0
        data_index, match_value, room_id, game_is_ranked = struct.unpack('<LLLb', data[offset:offset+13])
        offset += 13
        
        aux_data = MetaserverGameAuxData.unpack(data[offset:offset+32])
        offset += 32
        
        game_data_length = struct.unpack('<l', data[offset:offset+4])[0]
        offset += 4
        
        from .game_types import MetaserverGameDescription
        game = MetaserverGameDescription.unpack(data[offset:offset+556])
        offset += 556
        
        fmt = f'<{NETWORK_GAME_NAME_LENGTH + 1}s{NETWORK_MAP_NAME_LENGTH + 1}s'
        game_name, map_name = struct.unpack(fmt, data[offset:])
        
        return cls(
            data_index=data_index,
            match_value=match_value,
            room_id=room_id,
            game_is_ranked=bool(game_is_ranked),
            aux_data=aux_data,
            game_data_length=game_data_length,
            game=game,
            game_name=game_name.decode().rstrip('\0'),
            map_name=map_name.decode().rstrip('\0')
        )

class PatchFlags(IntFlag):
    """Patch flags"""
    REQUIRED = 1 << 0
    LAUNCH_AFTER_DOWNLOAD = 1 << 1
    ASK_BEFORE_DOWNLOAD = 1 << 2

@dataclass
class VersionEntry:
    """Version information"""
    group: int  # tag group, or appl (shlb?)
    subgroup: int  # myth, uber, mclt, etc, 01cb
    version: int  # last modification date?

    def pack(self) -> bytes:
        """Pack data into bytes"""
        return struct.pack('<LLL',
            self.group, self.subgroup, self.version)

    @classmethod
    def unpack(cls, data: bytes) -> 'VersionEntry':
        """Unpack data from bytes"""
        group, subgroup, version = struct.unpack('<LLL', data)
        return cls(group, subgroup, version)
