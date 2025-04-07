"""
Data models for Myth metaserver.
"""

from .game import (
    GameType,
    GameFlags,
    GameOptions,
    GameData,
    MetaserverGameDescription,
    MetaserverGameAuxData
)

from .player import (
    PlayerFlags,
    PlayerStatus,
    BungieNetPlayerStats,
    PlayerInfo
)

from .room import (
    RoomFlags,
    RoomInfo,
    RoomListEntry
)

from .stats import (
    CasteBreakpointData,
    OverallRankingData,
    PlayerStats
)

from .buddy import (
    BuddyFlags,
    BuddyEntry,
    BuddyList
)

from .order import (
    OrderFlags,
    OrderMember,
    OrderInfo
)

__all__ = [
    # Game models
    'GameType',
    'GameFlags',
    'GameOptions',
    'GameData',
    'MetaserverGameDescription',
    'MetaserverGameAuxData',
    
    # Player models
    'PlayerFlags',
    'PlayerStatus',
    'BungieNetPlayerStats',
    'PlayerInfo',
    
    # Room models
    'RoomFlags',
    'RoomInfo',
    'RoomListEntry',
    
    # Stats models
    'CasteBreakpointData',
    'OverallRankingData',
    'PlayerStats',
    
    # Buddy models
    'BuddyFlags',
    'BuddyEntry',
    'BuddyList',
    
    # Order models
    'OrderFlags',
    'OrderMember',
    'OrderInfo'
]
