"""
Player statistics tracking for Myth metaserver.

This module contains the PlayerStats class for tracking various player
statistics like scores, kills, wins, etc. and calculating ranking scores.
"""

import dataclasses
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

# Game constants
MYTH = 0

# Fixed point math constants
SHORT_FIXED_ONE = 1 << 16

@dataclasses.dataclass
class PlayerStats:
    """Statistics tracking for players"""
    score: int = 0
    points_killed: int = 0
    points_lost: int = 0
    units_killed: int = 0
    units_lost: int = 0
    updates_since_last_game_played: int = 0
    games_played: int = 0
    first_place_wins: int = 0
    last_place_wins: int = 0  # host drops
    caste: int = 0
    default_room: int = 0
    time_at_initial_login: int = dataclasses.field(default_factory=lambda: int(time.time()))

    def __add__(self, other: 'PlayerStats') -> 'PlayerStats':
        """Add two PlayerStats together
        
        Args:
            other: PlayerStats to add to this one
            
        Returns:
            New PlayerStats with combined values
        """
        result = PlayerStats(
            score=max(0, self.score + other.score),  # Don't let score go negative
            points_killed=self.points_killed + other.points_killed,
            points_lost=self.points_lost + other.points_lost,
            units_killed=self.units_killed + other.units_killed,
            units_lost=self.units_lost + other.units_lost,
            updates_since_last_game_played=self.updates_since_last_game_played,  # Keep original
            games_played=self.games_played + other.games_played,
            first_place_wins=self.first_place_wins + other.first_place_wins,
            last_place_wins=self.last_place_wins + other.last_place_wins,
            caste=self.caste + other.caste,
            default_room=self.default_room + other.default_room,
            time_at_initial_login=self.time_at_initial_login  # Keep original
        )
        return result

    def is_empty(self) -> bool:
        """Check if these stats are empty (all zeros)
        
        Returns:
            True if all stats are 0
        """
        return all(
            getattr(self, field.name) == 0 
            for field in dataclasses.fields(self)
            if field.name != 'time_at_initial_login'
        )

    def to_score(self) -> int:
        """Convert stats to a numerical score
        
        This uses a complex formula based on:
        - Win/loss ratio weighted by rank (A)
        - Kill/death ratio weighted by rank (B)
        - Games played weighted by rank (C)
        - Time-based attenuation
        
        Returns:
            Calculated score value
        """
        days_online = (int(time.time()) - self.time_at_initial_login) // (24 * 60 * 60)
        days_online = max(1, days_online)
        max_attenuation = SHORT_FIXED_ONE + (SHORT_FIXED_ONE // 4)

        # Set coefficients based on caste (rank)
        if self.caste <= 2:  # dagger to sword
            A = B = 0
            C = SHORT_FIXED_ONE
            days_per_game = 5 * SHORT_FIXED_ONE
        elif self.caste <= 5:  # sword & dagger to crossed axes
            A = 2 * SHORT_FIXED_ONE
            B = SHORT_FIXED_ONE
            C = SHORT_FIXED_ONE
            days_per_game = 4 * SHORT_FIXED_ONE
        else:  # shield to imperial crown
            A = 3 * SHORT_FIXED_ONE
            B = 2 * SHORT_FIXED_ONE
            C = SHORT_FIXED_ONE
            days_per_game = 3 * SHORT_FIXED_ONE

        # Calculate win component
        if self.games_played:
            wins = ((self.first_place_wins - self.last_place_wins) * A) // self.games_played
            attenuation = (days_per_game * days_online) // self.games_played
        else:
            wins = 0
            attenuation = SHORT_FIXED_ONE

        # Calculate damage component
        if self.points_lost:
            damage = (self.points_killed * B) // self.points_lost
        else:
            damage = 0  # Haven't really played yet

        # Games played component
        played = self.games_played * C

        # Combine components
        score = (wins + damage + played) // SHORT_FIXED_ONE

        # Apply time-based attenuation
        attenuation = min(attenuation, max_attenuation)
        score = (score * attenuation) // SHORT_FIXED_ONE

        return max(0, score)

    def print_stats(self) -> None:
        """Print human-readable stats to stdout"""
        print(f" Played: {self.games_played} Score: {self.score}")
        print(f" Points: Killed: {self.points_killed} Lost: {self.points_lost}")
        print(f" Units: Killed: {self.units_killed} Lost: {self.units_lost}")
        print(f" First Place Wins: {self.first_place_wins} Last place wins: {self.last_place_wins}")
        print(f" Caste: {self.caste} Default Room: {self.default_room}")
        print(f" Updates since last game played: {self.updates_since_last_game_played}")
