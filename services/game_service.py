"""
Game service for Myth metaserver.

This module provides functionality for managing games, including:
- Game creation and configuration
- Game state management
- Game logging and statistics
- Game evaluation and scoring
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..models.game import (
    GameData,
    GameType,
    GameFlags,
    GameOptions,
    MetaserverGameDescription,
    MetaserverGameAuxData
)
from ..models.bungie_net_structures import BungieNetPlayerScoreDatum, BungieNetGameDatum
from ..models.game_search_types import NewGameParameterData
from ..utils.environment import Environment

logger = logging.getLogger(__name__)

@dataclass
class GameLogEntry:
    """Entry in the game log"""
    timestamp: datetime
    game_id: int
    game_type: GameType
    map_name: str
    player_count: int
    max_players: int
    player_ids: List[int] = field(default_factory=list)
    player_scores: List[int] = field(default_factory=list)

from ..interfaces.game_interface import GameServiceInterface

class GameService(GameServiceInterface):
    """Game service for managing games and game logs"""
    
    def __init__(self):
        self.active_games: Dict[int, GameData] = {}
        self.game_logs: List[GameLogEntry] = []
        self.next_game_id: int = 1
        self.game_lock = asyncio.Lock()
        
    async def create_game(self, params: NewGameParameterData) -> Optional[int]:
        """Create a new game
        
        Args:
            params: Game parameters
            
        Returns:
            Game ID if created successfully, None if error
        """
        async with self.game_lock:
            game_id = self.next_game_id
            self.next_game_id += 1
            
            game = GameData(
                game_id=game_id,
                game_type=GameType(params.type),
                flags=GameFlags(0),
                options=GameOptions(params.option_flags),
                map_name="",  # Will be set when game starts
                player_count=0,
                max_players=params.maximum_players
            )
            
            self.active_games[game_id] = game
            logger.info(f"Created game {game_id}")
            return game_id
            
    async def start_game(self, game_id: int, map_name: str) -> bool:
        """Start a game
        
        Args:
            game_id: ID of game to start
            map_name: Name of map being played
            
        Returns:
            True if started successfully
        """
        async with self.game_lock:
            game = self.active_games.get(game_id)
            if not game:
                logger.error(f"Game {game_id} not found")
                return False
                
            game.flags |= GameFlags.IN_PROGRESS
            game.map_name = map_name
            logger.info(f"Started game {game_id} on map {map_name}")
            return True
            
    async def end_game(self, game_id: int, player_scores: Dict[int, int]) -> bool:
        """End a game and record results
        
        Args:
            game_id: ID of game to end
            player_scores: Dict mapping player IDs to scores
            
        Returns:
            True if ended successfully
        """
        async with self.game_lock:
            game = self.active_games.get(game_id)
            if not game:
                logger.error(f"Game {game_id} not found")
                return False
                
            # Update scores
            for player_id, score in player_scores.items():
                try:
                    idx = game.player_ids.index(player_id)
                    game.player_scores[idx] = score
                except ValueError:
                    logger.error(f"Player {player_id} not found in game {game_id}")
                    
            # Log game results
            log_entry = GameLogEntry(
                timestamp=datetime.now(),
                game_id=game.game_id,
                game_type=game.game_type,
                map_name=game.map_name,
                player_count=game.player_count,
                max_players=game.max_players,
                player_ids=game.player_ids.copy(),
                player_scores=game.player_scores.copy()
            )
            self.game_logs.append(log_entry)
            
            # Clean up
            del self.active_games[game_id]
            logger.info(f"Ended game {game_id}")
            return True
            
    async def add_player(self, game_id: int, player_id: int) -> bool:
        """Add a player to a game
        
        Args:
            game_id: ID of game to add player to
            player_id: ID of player to add
            
        Returns:
            True if added successfully
        """
        async with self.game_lock:
            game = self.active_games.get(game_id)
            if not game:
                logger.error(f"Game {game_id} not found")
                return False
                
            if player_id in game.player_ids:
                logger.warning(f"Player {player_id} already in game {game_id}")
                return True
                
            if game.player_count >= game.max_players:
                logger.error(f"Game {game_id} is full")
                return False
                
            game.player_ids.append(player_id)
            game.player_scores.append(0)
            game.player_count += 1
            logger.info(f"Added player {player_id} to game {game_id}")
            return True
            
    async def remove_player(self, game_id: int, player_id: int) -> bool:
        """Remove a player from a game
        
        Args:
            game_id: ID of game to remove player from
            player_id: ID of player to remove
            
        Returns:
            True if removed successfully
        """
        async with self.game_lock:
            game = self.active_games.get(game_id)
            if not game:
                logger.error(f"Game {game_id} not found")
                return False
                
            try:
                idx = game.player_ids.index(player_id)
                game.player_ids.pop(idx)
                game.player_scores.pop(idx)
                game.player_count -= 1
                logger.info(f"Removed player {player_id} from game {game_id}")
                return True
            except ValueError:
                logger.error(f"Player {player_id} not found in game {game_id}")
                return False
                
    async def get_game_data(self, game_id: int) -> Optional[GameData]:
        """Get data for a game
        
        Args:
            game_id: ID of game to get data for
            
        Returns:
            Game data if found, None if not found
        """
        async with self.game_lock:
            return self.active_games.get(game_id)
            
    async def get_game_description(self, game_id: int) -> Optional[MetaserverGameDescription]:
        """Get metaserver description for a game
        
        Args:
            game_id: ID of game to get description for
            
        Returns:
            Game description if found, None if not found
        """
        async with self.game_lock:
            game = self.active_games.get(game_id)
            if not game:
                return None
                
            desc = MetaserverGameDescription()
            desc.parameters.type = game.game_type
            desc.parameters.option_flags = game.options
            desc.flags = game.flags
            desc.player_count = game.player_count
            return desc
            
    async def get_game_logs(self, start_time: datetime, end_time: datetime) -> List[GameLogEntry]:
        """Get game logs for a time period
        
        Args:
            start_time: Start of time period
            end_time: End of time period
            
        Returns:
            List of game log entries in the time period
        """
        return [log for log in self.game_logs 
                if start_time <= log.timestamp <= end_time]

# Global instance
game_service = GameService()
