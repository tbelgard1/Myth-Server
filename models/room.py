"""
Room-related data models for Myth metaserver.
"""

from dataclasses import dataclass, field
from enum import IntFlag
from typing import List, Optional
import struct

from .base import BaseModel

class RoomFlags(IntFlag):
    """Room status flags"""
    RANKED = 1 << 0
    TOURNAMENT = 1 << 1
    PRIVATE = 1 << 2
    CLOSED = 1 << 3

@dataclass
class RoomInfo(BaseModel):
    """Room information"""
    room_id: int
    name: str
    flags: RoomFlags
    player_count: int
    max_players: int
    description: str
    motd: str
    
    def pack(self) -> bytes:
        data = struct.pack('<IIhh',
            self.room_id,
            int(self.flags),
            self.player_count,
            self.max_players
        )
        data += self.name.encode('utf-8') + b'\0'
        data += self.description.encode('utf-8') + b'\0'
        data += self.motd.encode('utf-8') + b'\0'
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'RoomInfo':
        room_id, flags, player_count, max_players = struct.unpack('<IIhh', data[:12])
        offset = 12
        
        # Find null-terminated strings
        name_end = data.find(b'\0', offset)
        name = data[offset:name_end].decode('utf-8')
        offset = name_end + 1
        
        desc_end = data.find(b'\0', offset)
        description = data[offset:desc_end].decode('utf-8')
        offset = desc_end + 1
        
        motd_end = data.find(b'\0', offset)
        motd = data[offset:motd_end].decode('utf-8')
        
        return cls(
            room_id=room_id,
            name=name,
            flags=RoomFlags(flags),
            player_count=player_count,
            max_players=max_players,
            description=description,
            motd=motd
        )

@dataclass
class RoomListEntry(BaseModel):
    """Entry in room list"""
    room_id: int
    name: str
    flags: RoomFlags
    player_count: int
    max_players: int
    
    def pack(self) -> bytes:
        data = struct.pack('<IIhh',
            self.room_id,
            int(self.flags),
            self.player_count,
            self.max_players
        )
        data += self.name.encode('utf-8') + b'\0'
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'RoomListEntry':
        room_id, flags, player_count, max_players = struct.unpack('<IIhh', data[:12])
        offset = 12
        
        name_end = data.find(b'\0', offset)
        name = data[offset:name_end].decode('utf-8')
        
        return cls(
            room_id=room_id,
            name=name,
            flags=RoomFlags(flags),
            player_count=player_count,
            max_players=max_players
        )
