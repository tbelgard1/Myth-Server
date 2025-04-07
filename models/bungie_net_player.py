"""
Part of the Bungie.net Myth2 Metaserver source code
Copyright (c) 1997-2002 Bungie Studios
Refer to the file "License.txt" for details

Converted to Python by Codeium
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Flag, IntFlag, auto
from typing import List, Optional
import ipaddress

# Constants
TAG_FILE_NAME_LENGTH = 8
MAXIMUM_LOGIN_LENGTH = 15
MAXIMUM_PASSWORD_LENGTH = 15
MAXIMUM_PLAYER_NAME_LENGTH = 31
MAXIMUM_DESCRIPTION_LENGTH = 431
MAXIMUM_NUMBER_OF_GAME_TYPES = 16
MAXIMUM_BUDDIES = 16
MAXIMUM_ORDER_MEMBERS = 16
STEFANS_MAXIMUM_ORDER_MEMBERS = 32
MAXIMUM_PACKED_PLAYER_DATA_LENGTH = 128
NUMBER_OF_TRACKED_OPPONENTS = 10

class PlayerStatus(IntFlag):
    """Player status flags"""
    INACTIVE = 0
    UNACKNOWLEDGED = auto()
    ACTIVE = auto()
    OFFLINE = auto()

class GameTypeFlags(Flag):
    """Game type flags"""
    MYTH1 = auto()
    MYTH2 = auto()
    MYTH3 = auto()
    MARATHON = auto()
    JCHAT = auto()

class PlayerFlags(Flag):
    """Player account flags"""
    BUNGIE_EMPLOYEE = auto()
    ACCOUNT_IS_KIOSK = auto()
    IS_ADMIN = auto()
    IS_BANNED = auto()

@dataclass
class RGBColor:
    """RGB color with flags"""
    red: int = 0
    green: int = 0
    blue: int = 0
    flags: int = 0

    def to_dict(self) -> dict:
        return {
            'red': self.red,
            'green': self.green,
            'blue': self.blue,
            'flags': self.flags
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RGBColor':
        return cls(
            red=data.get('red', 0),
            green=data.get('green', 0),
            blue=data.get('blue', 0),
            flags=data.get('flags', 0)
        )

@dataclass
class OrderMember:
    """Order (clan/team) member data"""
    player_id: int = 0
    online: bool = False

@dataclass
class BuddyEntry:
    """Buddy list entry"""
    player_id: int = 0
    active: bool = False

@dataclass
class BungieNetPlayerScoreDatum:
    """Player score data"""
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    damage_inflicted: int = 0
    damage_received: int = 0
    disconnects: int = 0
    points: int = 0
    rank: int = 0
    highest_points: int = 0
    highest_rank: int = 0
    numerical_rank: int = 0

    def to_dict(self) -> dict:
        return {
            'games_played': self.games_played,
            'wins': self.wins,
            'losses': self.losses,
            'ties': self.ties,
            'damage_inflicted': self.damage_inflicted,
            'damage_received': self.damage_received,
            'disconnects': self.disconnects,
            'points': self.points,
            'rank': self.rank,
            'highest_points': self.highest_points,
            'highest_rank': self.highest_rank,
            'numerical_rank': self.numerical_rank
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BungieNetPlayerScoreDatum':
        return cls(**data)

@dataclass
class AdditionalPlayerData:
    """Additional player metadata"""
    game_type_flags: GameTypeFlags = field(default_factory=lambda: GameTypeFlags(0))
    build_version: int = 0

@dataclass
class BungieNetPlayerDatum:
    """Main player data structure"""
    player_id: int = 0
    login: str = field(default="", metadata={"max_length": MAXIMUM_LOGIN_LENGTH})
    password: str = field(default="", metadata={"max_length": MAXIMUM_PASSWORD_LENGTH})
    flags: PlayerFlags = field(default_factory=lambda: PlayerFlags(0))
    
    last_login_ip: ipaddress.IPv4Address = field(default_factory=lambda: ipaddress.IPv4Address('0.0.0.0'))
    last_login_time: datetime = field(default_factory=datetime.now)
    last_game_time: datetime = field(default_factory=datetime.now)
    last_ranked_game_time: datetime = field(default_factory=datetime.now)
    
    room_id: int = 0
    buddies: List[BuddyEntry] = field(default_factory=lambda: [BuddyEntry() for _ in range(MAXIMUM_BUDDIES)])
    
    order_index: int = 0
    icon_index: int = 0
    icon_collection_name: str = ""
    
    name: str = field(default="", metadata={"max_length": MAXIMUM_PLAYER_NAME_LENGTH})
    team_name: str = field(default="", metadata={"max_length": MAXIMUM_PLAYER_NAME_LENGTH})
    description: str = field(default="", metadata={"max_length": MAXIMUM_DESCRIPTION_LENGTH})
    
    primary_color: RGBColor = field(default_factory=RGBColor)
    secondary_color: RGBColor = field(default_factory=RGBColor)
    
    # Ban tracking
    ban_duration: int = 0
    banned_time: datetime = field(default_factory=datetime.now)
    times_banned: int = 0
    
    # Location
    country_code: int = 0
    
    # Score tracking
    unranked_score: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    ranked_score: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    ranked_scores_by_game_type: List[BungieNetPlayerScoreDatum] = field(
        default_factory=lambda: [BungieNetPlayerScoreDatum() for _ in range(MAXIMUM_NUMBER_OF_GAME_TYPES)]
    )
    
    # Opponent tracking
    last_opponent_index: int = 0
    last_opponents: List[int] = field(default_factory=lambda: [0] * NUMBER_OF_TRACKED_OPPONENTS)
    
    # Additional data
    aux_data: AdditionalPlayerData = field(default_factory=AdditionalPlayerData)

    def __post_init__(self):
        """Validate and truncate fields that exceed maximum lengths"""
        if len(self.login) > MAXIMUM_LOGIN_LENGTH:
            self.login = self.login[:MAXIMUM_LOGIN_LENGTH]
            
        if len(self.password) > MAXIMUM_PASSWORD_LENGTH:
            self.password = self.password[:MAXIMUM_PASSWORD_LENGTH]
            
        if len(self.name) > MAXIMUM_PLAYER_NAME_LENGTH:
            self.name = self.name[:MAXIMUM_PLAYER_NAME_LENGTH]
            
        if len(self.team_name) > MAXIMUM_PLAYER_NAME_LENGTH:
            self.team_name = self.team_name[:MAXIMUM_PLAYER_NAME_LENGTH]
            
        if len(self.description) > MAXIMUM_DESCRIPTION_LENGTH:
            self.description = self.description[:MAXIMUM_DESCRIPTION_LENGTH]

    def to_dict(self) -> dict:
        """Convert player data to a dictionary for serialization"""
        return {
            'player_id': self.player_id,
            'login': self.login,
            'flags': self.flags.value,
            'last_login_ip': str(self.last_login_ip),
            'last_login_time': self.last_login_time.isoformat(),
            'last_game_time': self.last_game_time.isoformat(),
            'last_ranked_game_time': self.last_ranked_game_time.isoformat(),
            'room_id': self.room_id,
            'buddies': [
                {'player_id': b.player_id, 'active': b.active}
                for b in self.buddies
            ],
            'order_index': self.order_index,
            'icon_index': self.icon_index,
            'icon_collection_name': self.icon_collection_name,
            'name': self.name,
            'team_name': self.team_name,
            'description': self.description,
            'primary_color': self.primary_color.to_dict(),
            'secondary_color': self.secondary_color.to_dict(),
            'ban_duration': self.ban_duration,
            'banned_time': self.banned_time.isoformat(),
            'times_banned': self.times_banned,
            'country_code': self.country_code,
            'last_opponent_index': self.last_opponent_index,
            'last_opponents': self.last_opponents,
            'unranked_score': self.unranked_score.to_dict(),
            'ranked_score': self.ranked_score.to_dict(),
            'ranked_scores_by_game_type': [score.to_dict() for score in self.ranked_scores_by_game_type],
            'aux_data': {
                'game_type_flags': self.aux_data.game_type_flags.value,
                'build_version': self.aux_data.build_version
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BungieNetPlayerDatum':
        """Create a player from a dictionary"""
        player = cls(
            player_id=data.get('player_id', 0),
            login=data.get('login', ''),
            flags=PlayerFlags(data.get('flags', 0)),
            last_login_ip=ipaddress.IPv4Address(data.get('last_login_ip', '0.0.0.0')),
            room_id=data.get('room_id', 0),
            order_index=data.get('order_index', 0),
            icon_index=data.get('icon_index', 0),
            icon_collection_name=data.get('icon_collection_name', ''),
            name=data.get('name', ''),
            team_name=data.get('team_name', ''),
            description=data.get('description', ''),
            ban_duration=data.get('ban_duration', 0),
            times_banned=data.get('times_banned', 0),
            country_code=data.get('country_code', 0),
            last_opponent_index=data.get('last_opponent_index', 0),
            last_opponents=data.get('last_opponents', [0] * NUMBER_OF_TRACKED_OPPONENTS)
        )

        # Convert datetime fields
        for field_name in ['last_login_time', 'last_game_time', 'last_ranked_game_time', 'banned_time']:
            if field_name in data:
                setattr(player, field_name, datetime.fromisoformat(data[field_name]))

        # Convert colors
        if 'primary_color' in data:
            player.primary_color = RGBColor.from_dict(data['primary_color'])
        if 'secondary_color' in data:
            player.secondary_color = RGBColor.from_dict(data['secondary_color'])

        # Convert buddies
        if 'buddies' in data:
            player.buddies = [
                BuddyEntry(player_id=b['player_id'], active=b['active'])
                for b in data['buddies']
            ]

        # Convert scores
        if 'unranked_score' in data:
            player.unranked_score = BungieNetPlayerScoreDatum.from_dict(data['unranked_score'])
        if 'ranked_score' in data:
            player.ranked_score = BungieNetPlayerScoreDatum.from_dict(data['ranked_score'])
        if 'ranked_scores_by_game_type' in data:
            player.ranked_scores_by_game_type = [
                BungieNetPlayerScoreDatum.from_dict(score_data)
                for score_data in data['ranked_scores_by_game_type']
            ]

        # Convert aux data
        if 'aux_data' in data:
            player.aux_data = AdditionalPlayerData(
                game_type_flags=GameTypeFlags(data['aux_data'].get('game_type_flags', 0)),
                build_version=data['aux_data'].get('build_version', 0)
            )

        return player

@dataclass
class BungieNetOnlinePlayerData:
    """Online player data"""
    online_data_index: int = 0
    player_id: int = 0
    login: str = field(default="", metadata={"max_length": MAXIMUM_LOGIN_LENGTH})
    name: str = field(default="", metadata={"max_length": MAXIMUM_PLAYER_NAME_LENGTH})
    room_id: int = 0
    order: int = 0
    logged_in: bool = False
    player_data: bytes = field(default_factory=lambda: bytearray(MAXIMUM_PACKED_PLAYER_DATA_LENGTH))
    fpos: int = 0
    order_index: int = 0
    version: int = 0  # game version - ex: Myth II 1.5.0 -> 2150, multiplied by 10 for demo version (ie 21500)

@dataclass
class MythMetaserverPlayerData:
    """Metaserver player data packet"""
    coat_of_arms_bitmap_index: int = 0
    caste_bitmap_index: int = 0
    state: int = 0
    primary_color: RGBColor = field(default_factory=RGBColor)
    secondary_color: RGBColor = field(default_factory=RGBColor)
    order_index: int = 0
    version: int = 0  # game version - ex: Myth II 1.5.0 -> 2150, multiplied by 10 for demo version (ie 21500)
