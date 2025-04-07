"""
Statistics tracking for player orders and rankings.

This module contains the OrderStats class for tracking player statistics
and functions for calculating rating changes using the ELO system.
"""

import math
import dataclasses
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Constants for score calculation
K = 32  # K-factor for ELO calculation
G = 400  # Rating difference scale factor

@dataclasses.dataclass
class OrderStats:
    """Statistics tracking for player orders/rankings"""
    score: int = 0
    points_killed: int = 0
    points_lost: int = 0
    updates_since_last_game_played: int = 0
    games_played: int = 0
    first_place_wins: int = 0
    caste: int = 0
    default_room: int = 0

    def __add__(self, other: 'OrderStats') -> 'OrderStats':
        """Add two OrderStats together
        
        Args:
            other: OrderStats to add to this one
            
        Returns:
            New OrderStats with combined values
        """
        result = OrderStats(
            score=max(0, self.score + other.score),  # Don't let score go negative
            points_killed=self.points_killed + other.points_killed,
            points_lost=self.points_lost + other.points_lost,
            updates_since_last_game_played=self.updates_since_last_game_played,  # Keep original
            games_played=self.games_played + other.games_played,
            first_place_wins=self.first_place_wins + other.first_place_wins,
            caste=self.caste + other.caste,
            default_room=self.default_room + other.default_room
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
        )

    def to_score(self) -> int:
        """Convert stats to a numerical score
        
        Returns:
            Current score value
        """
        return self.score

def calculate_order_delta_score(friendly_rating: int, enemy_rating: int, won: bool) -> int:
    """Calculate change in rating when friendly player faces enemy player
    
    Uses ELO rating system:
    - Expected win probability based on rating difference
    - Actual result compared to expected
    - K-factor scales rating change
    
    Args:
        friendly_rating: Rating of player we're calculating for
        enemy_rating: Rating of opponent
        won: Whether friendly player won
        
    Returns:
        Change in rating points
    """
    # Calculate expected win probability using ELO formula
    power = (enemy_rating - friendly_rating) / G
    wins_expected = 1.0 / (1.0 + math.pow(10.0, power))
    
    # Calculate rating change
    actual_score = 1.0 if won else 0.0
    delta_score = int((actual_score - wins_expected) * K)
    
    return delta_score
