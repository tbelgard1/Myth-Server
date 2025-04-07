"""
Bungie.net structures for the Myth metaserver.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class BungieNetPlayerScoreDatum:
    """Player score data structure."""
    player_id: str = ''
    score: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    game_type: str = ''
    map_name: str = ''
    team_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'player_id': self.player_id,
            'score': self.score,
            'timestamp': self.timestamp.isoformat(),
            'game_type': self.game_type,
            'map_name': self.map_name,
            'team_id': self.team_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BungieNetPlayerScoreDatum':
        """Create from dictionary"""
        score = cls(
            player_id=data.get('player_id', ''),
            score=data.get('score', 0),
            game_type=data.get('game_type', ''),
            map_name=data.get('map_name', ''),
            team_id=data.get('team_id')
        )
        if 'timestamp' in data:
            score.timestamp = datetime.fromisoformat(data['timestamp'])
        return score

@dataclass
class BungieNetGameDatum:
    """Game data structure."""
    game_id: str
    game_type: str
    map_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    scores: List[BungieNetPlayerScoreDatum] = None

    def __post_init__(self):
        if self.scores is None:
            self.scores = []

@dataclass
class BungieNetTeamDatum:
    """Team data structure."""
    team_id: str
    name: str
    score: int
    players: List[str]

    def __post_init__(self):
        if self.players is None:
            self.players = []
