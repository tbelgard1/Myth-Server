"""
Game service interface for Myth metaserver.

This module defines the interface that all game services must implement.
It provides a standard contract for game management functionality.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from ..models.game import (
    GameData,
    GameType,
    MetaserverGameDescription,
    MetaserverGameAuxData
)
from ..models.game_search_types import NewGameParameterData

class GameServiceInterface(ABC):
    """Interface for game services"""
    
    @abstractmethod
    async def create_game(self, params: NewGameParameterData) -> Optional[int]:
        """Create a new game
        
        Args:
            params: Game parameters
            
        Returns:
            Game ID if created successfully, None if error
        """
        pass
        
    @abstractmethod
    async def start_game(self, game_id: int, map_name: str) -> bool:
        """Start a game
        
        Args:
            game_id: ID of game to start
            map_name: Name of map being played
            
        Returns:
            True if started successfully
        """
        pass
        
    @abstractmethod
    async def end_game(self, game_id: int, player_scores: Dict[int, int]) -> bool:
        """End a game and record results
        
        Args:
            game_id: ID of game to end
            player_scores: Dict mapping player IDs to scores
            
        Returns:
            True if ended successfully
        """
        pass
        
    @abstractmethod
    async def add_player(self, game_id: int, player_id: int) -> bool:
        """Add a player to a game
        
        Args:
            game_id: ID of game to add player to
            player_id: ID of player to add
            
        Returns:
            True if added successfully
        """
        pass
        
    @abstractmethod
    async def remove_player(self, game_id: int, player_id: int) -> bool:
        """Remove a player from a game
        
        Args:
            game_id: ID of game to remove player from
            player_id: ID of player to remove
            
        Returns:
            True if removed successfully
        """
        pass
        
    @abstractmethod
    async def get_game_data(self, game_id: int) -> Optional[GameData]:
        """Get data for a game
        
        Args:
            game_id: ID of game to get data for
            
        Returns:
            Game data if found, None if not found
        """
        pass
        
    @abstractmethod
    async def get_game_description(self, game_id: int) -> Optional[MetaserverGameDescription]:
        """Get metaserver description for a game
        
        Args:
            game_id: ID of game to get description for
            
        Returns:
            Game description if found, None if not found
        """
        pass
        
    @abstractmethod
    async def get_game_logs(self, start_time: datetime, end_time: datetime) -> List[GameData]:
        """Get game logs for a time period
        
        Args:
            start_time: Start of time period
            end_time: End of time period
            
        Returns:
            List of game data entries in the time period
        """
        pass
