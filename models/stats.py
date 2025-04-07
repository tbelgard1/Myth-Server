"""
Statistics-related data models for Myth metaserver.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import struct

from .base import BaseModel

@dataclass
class CasteBreakpointData(BaseModel):
    """Data for caste ranking breakpoints"""
    caste_id: int
    min_rating: float
    max_rating: float
    name: str
    
    def pack(self) -> bytes:
        data = struct.pack('<Iff', self.caste_id, self.min_rating, self.max_rating)
        data += self.name.encode('utf-8') + b'\0'
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'CasteBreakpointData':
        caste_id, min_rating, max_rating = struct.unpack('<Iff', data[:12])
        offset = 12
        
        name_end = data.find(b'\0', offset)
        name = data[offset:name_end].decode('utf-8')
        
        return cls(
            caste_id=caste_id,
            min_rating=min_rating,
            max_rating=max_rating,
            name=name
        )

@dataclass
class OverallRankingData(BaseModel):
    """Overall player ranking data"""
    player_id: int
    rating: float
    rank: int
    caste: int
    
    def pack(self) -> bytes:
        return struct.pack('<IfiI',
            self.player_id,
            self.rating,
            self.rank,
            self.caste
        )
        
    @classmethod
    def unpack(cls, data: bytes) -> 'OverallRankingData':
        fields = struct.unpack('<IfiI', data[:16])
        return cls(*fields)

@dataclass
class PlayerStats(BaseModel):
    """Complete player statistics"""
    total_games: int
    total_wins: int
    total_losses: int
    total_disconnects: int
    rating: float
    rank: int
    caste: int
    
    # Game type specific stats
    game_type_games: List[int] = field(default_factory=lambda: [0] * 15)
    game_type_wins: List[int] = field(default_factory=lambda: [0] * 15)
    game_type_losses: List[int] = field(default_factory=lambda: [0] * 15)
    game_type_ratings: List[float] = field(default_factory=lambda: [0.0] * 15)
    
    def pack(self) -> bytes:
        data = struct.pack('<IIIIfiI',
            self.total_games,
            self.total_wins,
            self.total_losses,
            self.total_disconnects,
            self.rating,
            self.rank,
            self.caste
        )
        
        # Pack game type stats
        for i in range(15):
            data += struct.pack('<IIIf',
                self.game_type_games[i],
                self.game_type_wins[i],
                self.game_type_losses[i],
                self.game_type_ratings[i]
            )
            
        return data
        
    @classmethod
    def unpack(cls, data: bytes) -> 'PlayerStats':
        # Unpack overall stats
        fields = list(struct.unpack('<IIIIfiI', data[:28]))
        offset = 28
        
        # Unpack game type stats
        game_type_games = []
        game_type_wins = []
        game_type_losses = []
        game_type_ratings = []
        
        for _ in range(15):
            games, wins, losses, rating = struct.unpack('<IIIf', data[offset:offset+16])
            game_type_games.append(games)
            game_type_wins.append(wins)
            game_type_losses.append(losses)
            game_type_ratings.append(rating)
            offset += 16
            
        return cls(
            *fields,
            game_type_games=game_type_games,
            game_type_wins=game_type_wins,
            game_type_losses=game_type_losses,
            game_type_ratings=game_type_ratings
        )
