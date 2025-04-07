"""
Buddy list data models for Myth metaserver.
"""

from dataclasses import dataclass, field
from enum import IntFlag
from typing import List, Optional
import struct

from .base import BaseModel

class BuddyFlags(IntFlag):
    """Buddy status flags"""
    BLOCKED = 1 << 0
    MUTED = 1 << 1
    FAVORITE = 1 << 2

@dataclass
class BuddyEntry(BaseModel):
    """Entry in buddy list"""
    player_id: int
    name: str
    flags: BuddyFlags
    
    def pack(self) -> bytes:
        data = struct.pack('<II', self.player_id, int(self.flags))
        data += self.name.encode('utf-8') + b'\0'
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'BuddyEntry':
        player_id, flags = struct.unpack('<II', data[:8])
        offset = 8
        
        name_end = data.find(b'\0', offset)
        name = data[offset:name_end].decode('utf-8')
        
        return cls(
            player_id=player_id,
            name=name,
            flags=BuddyFlags(flags)
        )

@dataclass
class BuddyList(BaseModel):
    """Complete buddy list"""
    owner_id: int
    entries: List[BuddyEntry] = field(default_factory=list)
    
    def pack(self) -> bytes:
        data = struct.pack('<II', self.owner_id, len(self.entries))
        
        for entry in self.entries:
            data += entry.pack()
            
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'BuddyList':
        owner_id, count = struct.unpack('<II', data[:8])
        offset = 8
        
        entries = []
        for _ in range(count):
            entry = BuddyEntry.unpack(data[offset:])
            entries.append(entry)
            offset += len(entry.pack())
            
        return cls(
            owner_id=owner_id,
            entries=entries
        )
