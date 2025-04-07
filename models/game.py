"""
Game-related data models for Myth metaserver.
"""

from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import List, Optional
import struct

from .base import BaseModel

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

@dataclass
class GameData(BaseModel):
    """Game data including players and scores"""
    game_id: int
    game_type: GameType
    flags: GameFlags
    options: GameOptions
    map_name: str
    player_count: int
    max_players: int
    player_ids: List[int] = field(default_factory=list)
    player_scores: List[int] = field(default_factory=list)
    
    def pack(self) -> bytes:
        data = struct.pack('<IIIIh',
            self.game_id,
            int(self.game_type),
            int(self.flags),
            int(self.options),
            len(self.map_name)
        )
        data += self.map_name.encode('utf-8')
        data += struct.pack('<hh', self.player_count, self.max_players)
        
        for player_id in self.player_ids:
            data += struct.pack('<I', player_id)
            
        for score in self.player_scores:
            data += struct.pack('<i', score)
            
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'GameData':
        game_id, type_, flags, options, name_len = struct.unpack('<IIIIh', data[:18])
        offset = 18
        
        map_name = data[offset:offset+name_len].decode('utf-8')
        offset += name_len
        
        player_count, max_players = struct.unpack('<hh', data[offset:offset+4])
        offset += 4
        
        player_ids = []
        for _ in range(player_count):
            player_id, = struct.unpack('<I', data[offset:offset+4])
            player_ids.append(player_id)
            offset += 4
            
        player_scores = []
        for _ in range(player_count):
            score, = struct.unpack('<i', data[offset:offset+4])
            player_scores.append(score)
            offset += 4
            
        return cls(
            game_id=game_id,
            game_type=GameType(type_),
            flags=GameFlags(flags),
            options=GameOptions(options),
            map_name=map_name,
            player_count=player_count,
            max_players=max_players,
            player_ids=player_ids,
            player_scores=player_scores
        )

@dataclass
class MetaserverGameAuxData(BaseModel):
    """Additional game data for metaserver"""
    game_id: int
    host_address: int
    host_port: int
    
    def pack(self) -> bytes:
        return struct.pack('<III',
            self.game_id,
            self.host_address,
            self.host_port
        )
        
    @classmethod
    def unpack(cls, data: bytes) -> 'MetaserverGameAuxData':
        game_id, host_address, host_port = struct.unpack('<III', data[:12])
        return cls(game_id, host_address, host_port)

@dataclass
class MetaserverGameDescription(BaseModel):
    """Game description for metaserver listing"""
    game_type: GameType
    flags: GameFlags
    options: GameOptions
    map_name: str
    player_count: int
    max_players: int
    host_name: str
    
    def pack(self) -> bytes:
        data = struct.pack('<IIIhh',
            int(self.game_type),
            int(self.flags),
            int(self.options),
            self.player_count,
            self.max_players
        )
        data += self.map_name.encode('utf-8') + b'\0'
        data += self.host_name.encode('utf-8') + b'\0'
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'MetaserverGameDescription':
        type_, flags, options, player_count, max_players = struct.unpack('<IIIhh', data[:16])
        offset = 16
        
        # Find null-terminated strings
        map_end = data.find(b'\0', offset)
        map_name = data[offset:map_end].decode('utf-8')
        offset = map_end + 1
        
        host_end = data.find(b'\0', offset)
        host_name = data[offset:host_end].decode('utf-8')
        
        return cls(
            game_type=GameType(type_),
            flags=GameFlags(flags),
            options=GameOptions(options),
            map_name=map_name,
            player_count=player_count,
            max_players=max_players,
            host_name=host_name
        )
