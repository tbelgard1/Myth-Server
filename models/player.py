"""
Player-related data models for Myth metaserver.
"""

from dataclasses import dataclass, field
from enum import IntFlag
from typing import List, Optional
import struct

from .base import BaseModel
from .stats import PlayerStats

class PlayerFlags(IntFlag):
    """Player status flags"""
    ADMIN = 1 << 0
    BUNGIE = 1 << 1
    KIOSK = 1 << 2
    TOURNAMENT = 1 << 3
    BANNED = 1 << 4
    MUTED = 1 << 5

class PlayerStatus(IntFlag):
    """Player connection status"""
    OFFLINE = 0
    ONLINE = 1 << 0
    IN_GAME = 1 << 1
    AWAY = 1 << 2
    DO_NOT_DISTURB = 1 << 3

@dataclass
class BungieNetPlayerStats(BaseModel):
    """Player statistics from bungie.net"""
    player_id: int
    total_games: int
    total_wins: int
    total_losses: int
    total_disconnects: int
    rating: float
    rank: int
    caste: int
    
    def pack(self) -> bytes:
        return struct.pack('<IIIIIfiI',
            self.player_id,
            self.total_games,
            self.total_wins,
            self.total_losses,
            self.total_disconnects,
            self.rating,
            self.rank,
            self.caste
        )
        
    @classmethod
    def unpack(cls, data: bytes) -> 'BungieNetPlayerStats':
        fields = struct.unpack('<IIIIIfiI', data[:32])
        return cls(*fields)

@dataclass
class PlayerInfo(BaseModel):
    """Complete player information"""
    player_id: int
    name: str
    flags: PlayerFlags
    status: PlayerStatus
    stats: PlayerStats
    current_game_id: Optional[int] = None
    current_room_id: Optional[int] = None
    
    def pack(self) -> bytes:
        data = struct.pack('<I', self.player_id)
        data += self.name.encode('utf-8') + b'\0'
        data += struct.pack('<II', int(self.flags), int(self.status))
        data += self.stats.pack()
        
        if self.current_game_id is not None:
            data += struct.pack('<I', self.current_game_id)
        else:
            data += struct.pack('<I', 0)
            
        if self.current_room_id is not None:
            data += struct.pack('<I', self.current_room_id)
        else:
            data += struct.pack('<I', 0)
            
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'PlayerInfo':
        player_id, = struct.unpack('<I', data[:4])
        offset = 4
        
        name_end = data.find(b'\0', offset)
        name = data[offset:name_end].decode('utf-8')
        offset = name_end + 1
        
        flags, status = struct.unpack('<II', data[offset:offset+8])
        offset += 8
        
        stats = PlayerStats.unpack(data[offset:])
        offset += stats.size()
        
        game_id, room_id = struct.unpack('<II', data[offset:offset+8])
        
        return cls(
            player_id=player_id,
            name=name,
            flags=PlayerFlags(flags),
            status=PlayerStatus(status),
            stats=stats,
            current_game_id=game_id if game_id != 0 else None,
            current_room_id=room_id if room_id != 0 else None
        )
