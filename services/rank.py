"""
Part of the Bungie.net Myth2 Metaserver source code
Copyright (c) 1997-2002 Bungie Studios
Refer to the file "License.txt" for details
"""

import enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from functools import lru_cache
import logging
from pathlib import Path

from ..utils.environment import Environment
from ..models.stats import Stats
from ..security.authentication import Authentication
from ..models.metaserver_common_structs import MetaserverCommonStructs, RGBColor
from ..models.bungie_net_player import BungieNetPlayerDatum, BungieNetPlayerScoreDatum
from ..models.bungie_net_order import BungieNetOrderDatum
from .users import Users
from .orders import order_database

# Cache size for frequently accessed data
RANK_CACHE_SIZE = 1024

# Constants
NUMBER_OF_RANKING_PASSES = 17
MAXIMUM_DATABASE_OPERATIONS_PER_CALL = 1000
MAXIMUM_LOGIN_LENGTH = 15
MAXIMUM_PLAYER_NAME_LENGTH = 31
MAXIMUM_ORDER_NAME_LENGTH = 31
MAXIMUM_DESCRIPTION_LENGTH = 431
MAXIMUM_NUMBER_OF_GAME_TYPES = 16

class BungieRank(enum.IntEnum):
    """Enumeration of Bungie ranks"""
    DAGGER = 0
    DAGGER_WITH_HILT = 1
    KRIS_KNIFE = 2
    SWORD_AND_DAGGER = 3
    CROSSED_SWORDS = 4
    CROSSED_AXES = 5
    SHIELD = 6
    SHIELD_CROSSED_SWORDS = 7
    SHIELD_CROSSED_AXES = 8
    SIMPLE_CROWN = 9
    CROWN = 10
    NICE_CROWN = 11
    ECLIPSED_MOON = 12
    MOON = 13
    ECLIPSED_SUN = 14
    SUN = 15
    COMET = 16
    NUMBER_OF_BUNGIE_RANKS = 17

class RankConstants(enum.IntEnum):
    """Game ranking constants"""
    GAMES_PLAYED_DAGGER_CASTE = 1
    GAMES_PLAYED_DAGGER_WITH_HILT_CASTE = 2
    GAMES_PLAYED_KRIS_DAGGER_CASTE = 3
    ECLIPSED_MOON_PLAYER_COUNT = 3
    MOON_PLAYER_COUNT = 2
    ECLIPSED_SUN_PLAYER_COUNT = 1
    SUN_PLAYER_COUNT = 1
    COMET_PLAYER_COUNT = 1
    TOTAL_NAMED_PLAYER_COUNT = 8
    NUMBER_OF_RANKED_GAME_TYPES = 8
    NUMBER_OF_NORMAL_CASTES = 12

class UserIndex(enum.IntEnum):
    """User index constants"""
    COMET = 0
    SUN = 1
    ECLIPSED_SUN = 2
    MOON_1 = 3
    MOON_0 = 4
    ECLIPSED_MOON_2 = 5
    ECLIPSED_MOON_1 = 6
    ECLIPSED_MOON_0 = 7

# Rank percentages for each caste level
RANK_PERCENTAGES = [
    0.00, 0.00, 0.00, 0.16, 0.15, 0.14,
    0.12, 0.11, 0.10, 0.09, 0.07, 0.06
]

@dataclass
class BungieNetPlayerStats:
    __slots__ = [
        'administrator_flag', 'bungie_employee_flag', 'order_index', 'icon_index',
        'primary_color', 'secondary_color', 'unranked_score_datum', 'ranked_score_datum',
        'ranked_score_datum_by_game_type', 'order_unranked_score_datum', 'order_ranked_score_datum',
        'order_ranked_score_datum_by_game_type', 'login', 'name', 'order_name', 'description'
    ]
    """Player statistics structure"""
    administrator_flag: bool = False
    bungie_employee_flag: bool = False
    order_index: int = 0
    icon_index: int = 0
    primary_color: RGBColor = field(default_factory=RGBColor)
    secondary_color: RGBColor = field(default_factory=RGBColor)
    unranked_score_datum: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    ranked_score_datum: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    ranked_score_datum_by_game_type: List[BungieNetPlayerScoreDatum] = field(
        default_factory=lambda: [BungieNetPlayerScoreDatum() for _ in range(MAXIMUM_NUMBER_OF_GAME_TYPES)]
    )
    order_unranked_score_datum: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    order_ranked_score_datum: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)
    order_ranked_score_datum_by_game_type: List[BungieNetPlayerScoreDatum] = field(
        default_factory=lambda: [BungieNetPlayerScoreDatum() for _ in range(MAXIMUM_NUMBER_OF_GAME_TYPES)]
    )
    login: str = ""
    name: str = ""
    order_name: str = ""
    description: str = ""

@dataclass
class RawRankData:
    """Raw rank data structure"""
    __slots__ = ['id', 'score']
    id: int = 0
    score: BungieNetPlayerScoreDatum = field(default_factory=BungieNetPlayerScoreDatum)

@dataclass
class RankingData:
    """Ranking data structure"""
    __slots__ = ['average', 'best']
    average: int = 0
    best: int = 0

@dataclass
class GameRankData:
    """Game rank data structure"""
    __slots__ = ['top_ranked_player', 'points', 'games_played', 'wins', 'damage_inflicted', 'damage_received']
    top_ranked_player: str = ""
    points: RankingData = field(default_factory=RankingData)
    games_played: RankingData = field(default_factory=RankingData)
    wins: RankingData = field(default_factory=RankingData)
    damage_inflicted: RankingData = field(default_factory=RankingData)
    damage_received: RankingData = field(default_factory=RankingData)

@dataclass
class OverallRankingData:
    """Overall ranking data structure"""
    __slots__ = [
        'total_users', 'total_orders', 'unranked_game_data', 'ranked_game_data',
        'ranked_game_data_by_game_type', 'order_unranked_game_data', 'order_ranked_game_data',
        'order_ranked_game_data_by_game_type'
    ]
    total_users: int = 0
    total_orders: int = 0
    unranked_game_data: GameRankData = field(default_factory=GameRankData)
    ranked_game_data: GameRankData = field(default_factory=GameRankData)
    ranked_game_data_by_game_type: List[GameRankData] = field(
        default_factory=lambda: [GameRankData() for _ in range(MAXIMUM_NUMBER_OF_GAME_TYPES)]
    )
    order_unranked_game_data: GameRankData = field(default_factory=GameRankData)
    order_ranked_game_data: GameRankData = field(default_factory=GameRankData)
    order_ranked_game_data_by_game_type: List[GameRankData] = field(
        default_factory=lambda: [GameRankData() for _ in range(MAXIMUM_NUMBER_OF_GAME_TYPES)]
    )

@dataclass
class CasteBreakpointData:
    """Caste breakpoint data structure"""
    __slots__ = [
        'normal_caste_breakpoints', 'eclipsed_moon_player_ids', 'moon_player_ids',
        'eclipsed_sun_player_ids', 'sun_player_ids', 'comet_player_ids'
    ]
    normal_caste_breakpoints: List[int] = field(
        default_factory=lambda: [0] * RankConstants.NUMBER_OF_NORMAL_CASTES
    )
    eclipsed_moon_player_ids: List[int] = field(
        default_factory=lambda: [0] * RankConstants.ECLIPSED_MOON_PLAYER_COUNT
    )
    moon_player_ids: List[int] = field(
        default_factory=lambda: [0] * RankConstants.MOON_PLAYER_COUNT
    )
    eclipsed_sun_player_ids: List[int] = field(
        default_factory=lambda: [0] * RankConstants.ECLIPSED_SUN_PLAYER_COUNT
    )
    sun_player_ids: List[int] = field(
        default_factory=lambda: [0] * RankConstants.SUN_PLAYER_COUNT
    )
    comet_player_ids: List[int] = field(
        default_factory=lambda: [0] * RankConstants.COMET_PLAYER_COUNT
    )

@dataclass
class RankingMetrics:
    """Metrics for ranking calculations"""
    __slots__ = ['points', 'games_played', 'wins', 'damage_inflicted', 'damage_received']
    points: int = 0
    games_played: int = 0
    wins: int = 0
    damage_inflicted: float = 0.0
    damage_received: float = 0.0

    def update(self, score: BungieNetPlayerScoreDatum) -> None:
        """Update metrics with a player's score"""
        self.points += score.points
        self.games_played += score.games_played
        self.wins += score.wins
        self.damage_inflicted += score.damage_inflicted
        self.damage_received += score.damage_received

class RankingSystem:
    """Handles player ranking calculations and updates with optimizations"""
    
    def __init__(self):
        self.logger = logging.getLogger("RankingSystem")
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset internal state - useful for testing and cleanup"""
        self.ranking_data: List[RawRankData] = []
        self.present_ranking: int = 0
        self.rank_cache: Dict[int, Tuple[int, int]] = {}  # player_id -> (rank, points)
        self.caste_breakpoints: Optional[CasteBreakpointData] = None

    def _clear_caches(self) -> None:
        """Clear all cached data"""
        self.rank_cache.clear()
        self.caste_breakpoints = None

    @lru_cache(maxsize=RANK_CACHE_SIZE)
    def get_player_rank(self, player_id: int) -> Tuple[int, int]:
        """Get a player's rank and points (cached)"""
        if player_id in self.rank_cache:
            return self.rank_cache[player_id]
        return (BungieRank.DAGGER, 0)

    def get_caste_breakpoints(self) -> CasteBreakpointData:
        """Calculate and cache caste breakpoints"""
        if self.caste_breakpoints:
            return self.caste_breakpoints

        breakpoints = CasteBreakpointData()
        total_players = len(self.ranking_data)
        
        if total_players == 0:
            return breakpoints

        # Calculate normal caste breakpoints
        players_placed = 0
        for i in range(RankConstants.NUMBER_OF_NORMAL_CASTES):
            players_in_caste = int(total_players * RANK_PERCENTAGES[i])
            if players_in_caste > 0:
                breakpoints.normal_caste_breakpoints[i] = self.ranking_data[players_placed].score.points
                players_placed += players_in_caste

        # Assign special ranks
        current_index = 0

        # Comet
        for i in range(RankConstants.COMET_PLAYER_COUNT):
            if current_index < total_players:
                breakpoints.comet_player_ids[i] = self.ranking_data[current_index].id
                current_index += 1

        # Sun
        for i in range(RankConstants.SUN_PLAYER_COUNT):
            if current_index < total_players:
                breakpoints.sun_player_ids[i] = self.ranking_data[current_index].id
                current_index += 1

        # Eclipsed Sun
        for i in range(RankConstants.ECLIPSED_SUN_PLAYER_COUNT):
            if current_index < total_players:
                breakpoints.eclipsed_sun_player_ids[i] = self.ranking_data[current_index].id
                current_index += 1

        # Moon
        for i in range(RankConstants.MOON_PLAYER_COUNT):
            if current_index < total_players:
                breakpoints.moon_player_ids[i] = self.ranking_data[current_index].id
                current_index += 1

        # Eclipsed Moon
        for i in range(RankConstants.ECLIPSED_MOON_PLAYER_COUNT):
            if current_index < total_players:
                breakpoints.eclipsed_moon_player_ids[i] = self.ranking_data[current_index].id
                current_index += 1

        self.caste_breakpoints = breakpoints
        return breakpoints

    def build_overall_ranking_data(self, caste_breakpoints: CasteBreakpointData,
                                 overall_rank_data: OverallRankingData) -> None:
        """Build overall ranking data with optimizations"""
        if not self.ranking_data:
            return

        # Update top ranked player
        if len(self.ranking_data) > 0:
            top_player = self.ranking_data[0]
            overall_rank_data.ranked_game_data.top_ranked_player = str(top_player.id)
            
            # Calculate aggregate statistics efficiently
            metrics = RankingMetrics()
            for rank_data in self.ranking_data:
                metrics.update(rank_data.score)
            
            # Update overall statistics
            if len(self.ranking_data) > 0:
                overall_rank_data.ranked_game_data.points.average = metrics.points // len(self.ranking_data)
                overall_rank_data.ranked_game_data.points.best = metrics.points
                overall_rank_data.ranked_game_data.games_played.average = metrics.games_played // len(self.ranking_data)
                overall_rank_data.ranked_game_data.games_played.best = metrics.games_played
                overall_rank_data.ranked_game_data.wins.average = metrics.wins // len(self.ranking_data)
                overall_rank_data.ranked_game_data.wins.best = metrics.wins
                overall_rank_data.ranked_game_data.damage_inflicted.average = int(metrics.damage_inflicted / len(self.ranking_data))
                overall_rank_data.ranked_game_data.damage_inflicted.best = int(metrics.damage_inflicted)
                overall_rank_data.ranked_game_data.damage_received.average = int(metrics.damage_received / len(self.ranking_data))
                overall_rank_data.ranked_game_data.damage_received.best = int(metrics.damage_received)

    def update_database_on_ranking(self, order: bool = False) -> bool:
        """Update database with current rankings"""
        if not self.ranking_data:
            return False

        BATCH_SIZE = MAXIMUM_DATABASE_OPERATIONS_PER_CALL
        last_ranked_id = 1
        
        while last_ranked_id <= len(self.ranking_data):
            batch_end = min(last_ranked_id + BATCH_SIZE, len(self.ranking_data) + 1)
            
            for i in range(last_ranked_id, batch_end):
                player = BungieNetPlayerDatum()
                if Users.get_player_information(self.ranking_data[i-1].id, player):
                    if order:
                        if self.present_ranking == 0:  # Overall ranking
                            player.ranked_score_datum = self.ranking_data[i-1].score
                        else:  # Game type specific ranking
                            player.ranked_score_datum_by_game_type[self.present_ranking - 1] = self.ranking_data[i-1].score
                    else:
                        if self.present_ranking == 0:  # Overall ranking
                            player.order_ranked_score_datum = self.ranking_data[i-1].score
                        else:  # Game type specific ranking
                            player.order_ranked_score_datum_by_game_type[self.present_ranking - 1] = self.ranking_data[i-1].score
                    
                    Users.update_player_information(player.player_id, player)
            
            last_ranked_id = batch_end
            
        if last_ranked_id > len(self.ranking_data):
            self.present_ranking += 1
            return True
            
        return False

    def compare_rankings(self, r0: RawRankData, r1: RawRankData) -> int:
        """Compare two rankings efficiently"""
        if (r0.score.games_played > RankConstants.GAMES_PLAYED_KRIS_DAGGER_CASTE and
            r1.score.games_played <= RankConstants.GAMES_PLAYED_KRIS_DAGGER_CASTE):
            return -1
        elif (r1.score.games_played > RankConstants.GAMES_PLAYED_KRIS_DAGGER_CASTE and
              r0.score.games_played <= RankConstants.GAMES_PLAYED_KRIS_DAGGER_CASTE):
            return 1
        
        # Compare points first
        if r0.score.points != r1.score.points:
            return -1 if r0.score.points > r1.score.points else 1
            
        # If points are equal, compare games played
        if r0.score.games_played != r1.score.games_played:
            return -1 if r0.score.games_played > r1.score.games_played else 1
            
        return 0  # Rankings are equal

# Global instance
ranking_system = RankingSystem()
