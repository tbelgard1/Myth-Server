"""
Order-related data models for Myth metaserver.
"""

from dataclasses import dataclass, field
from enum import IntFlag
from typing import List, Optional
import struct

from .base import BaseModel

class OrderFlags(IntFlag):
    """Order status flags"""
    PRIVATE = 1 << 0
    INVITE_ONLY = 1 << 1
    DISBANDED = 1 << 2
    TOURNAMENT = 1 << 3

@dataclass
class OrderMember(BaseModel):
    """Member in an order"""
    player_id: int
    name: str
    rank: int
    join_date: int  # Unix timestamp
    last_active: int  # Unix timestamp
    total_games: int
    total_wins: int
    
    def pack(self) -> bytes:
        data = struct.pack('<IiIIIII',
            self.player_id,
            self.rank,
            self.join_date,
            self.last_active,
            self.total_games,
            self.total_wins,
            len(self.name)
        )
        data += self.name.encode('utf-8')
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'OrderMember':
        player_id, rank, join_date, last_active, games, wins, name_len = \
            struct.unpack('<IiIIIII', data[:28])
        offset = 28
        
        name = data[offset:offset+name_len].decode('utf-8')
        
        return cls(
            player_id=player_id,
            name=name,
            rank=rank,
            join_date=join_date,
            last_active=last_active,
            total_games=games,
            total_wins=wins
        )

@dataclass
class OrderInfo(BaseModel):
    """Complete order information"""
    order_id: int
    name: str
    tag: str  # 4-character tag
    flags: OrderFlags
    creation_date: int  # Unix timestamp
    leader_id: int
    description: str
    motd: str  # Message of the day
    members: List[OrderMember] = field(default_factory=list)
    
    def pack(self) -> bytes:
        data = struct.pack('<IIIIh',
            self.order_id,
            int(self.flags),
            self.creation_date,
            self.leader_id,
            len(self.members)
        )
        
        # Pack strings
        data += self.name.encode('utf-8') + b'\0'
        data += self.tag.encode('utf-8') + b'\0'
        data += self.description.encode('utf-8') + b'\0'
        data += self.motd.encode('utf-8') + b'\0'
        
        # Pack members
        for member in self.members:
            data += member.pack()
            
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'OrderInfo':
        order_id, flags, creation_date, leader_id, member_count = \
            struct.unpack('<IIIIh', data[:18])
        offset = 18
        
        # Find null-terminated strings
        name_end = data.find(b'\0', offset)
        name = data[offset:name_end].decode('utf-8')
        offset = name_end + 1
        
        tag_end = data.find(b'\0', offset)
        tag = data[offset:tag_end].decode('utf-8')
        offset = tag_end + 1
        
        desc_end = data.find(b'\0', offset)
        description = data[offset:desc_end].decode('utf-8')
        offset = desc_end + 1
        
        motd_end = data.find(b'\0', offset)
        motd = data[offset:motd_end].decode('utf-8')
        offset = motd_end + 1
        
        # Unpack members
        members = []
        for _ in range(member_count):
            member = OrderMember.unpack(data[offset:])
            members.append(member)
            offset += len(member.pack())
            
        return cls(
            order_id=order_id,
            name=name,
            tag=tag,
            flags=OrderFlags(flags),
            creation_date=creation_date,
            leader_id=leader_id,
            description=description,
            motd=motd,
            members=members
        )
