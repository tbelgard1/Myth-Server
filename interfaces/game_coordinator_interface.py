"""
Game coordinator interface for the Myth metaserver.

This module defines the interface for coordinating game sessions, including
matchmaking, game state synchronization, and player coordination.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

class GameState(Enum):
    """Possible states for a game."""
    INITIALIZING = auto()  # Game is being set up
    WAITING = auto()       # Waiting for players to ready up
    STARTING = auto()      # Game is about to start
    IN_PROGRESS = auto()   # Game is being played
    ENDING = auto()        # Game is ending
    COMPLETED = auto()     # Game has finished
    ABORTED = auto()       # Game was aborted

@dataclass
class PlayerStatus:
    """Status of a player in a game."""
    user_id: int
    ready: bool = False
    connected: bool = True
    team: Optional[int] = None
    joined_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

@dataclass
class GameStatus:
    """Current status of a game."""
    game_id: int
    state: GameState
    map_name: str
    player_count: int
    max_players: int
    team_game: bool
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class GameCoordinatorInterface(ABC):
    """Interface for game coordination operations."""
    
    @abstractmethod
    async def initialize_game(self, game_id: int, settings: Dict) -> bool:
        """Initialize a new game session.
        
        Args:
            game_id: ID of the game to initialize
            settings: Game settings including map, type, etc.
            
        Returns:
            bool: True if initialized successfully
        """
        pass
        
    @abstractmethod
    async def add_player(self, game_id: int, user_id: int, team: Optional[int] = None) -> bool:
        """Add a player to a game.
        
        Args:
            game_id: ID of the game
            user_id: ID of the user to add
            team: Optional team number for team games
            
        Returns:
            bool: True if added successfully
        """
        pass
        
    @abstractmethod
    async def remove_player(self, game_id: int, user_id: int) -> bool:
        """Remove a player from a game.
        
        Args:
            game_id: ID of the game
            user_id: ID of the user to remove
            
        Returns:
            bool: True if removed successfully
        """
        pass
        
    @abstractmethod
    async def set_player_ready(self, game_id: int, user_id: int, ready: bool = True) -> bool:
        """Set a player's ready status.
        
        Args:
            game_id: ID of the game
            user_id: ID of the user
            ready: Whether the player is ready
            
        Returns:
            bool: True if status updated successfully
        """
        pass
        
    @abstractmethod
    async def set_player_team(self, game_id: int, user_id: int, team: int) -> bool:
        """Set a player's team.
        
        Args:
            game_id: ID of the game
            user_id: ID of the user
            team: Team number to assign
            
        Returns:
            bool: True if team assigned successfully
        """
        pass
        
    @abstractmethod
    async def start_game(self, game_id: int) -> bool:
        """Start a game when all players are ready.
        
        Args:
            game_id: ID of the game
            
        Returns:
            bool: True if started successfully
        """
        pass
        
    @abstractmethod
    async def end_game(self, game_id: int, scores: Dict[int, int]) -> bool:
        """End a game and record final scores.
        
        Args:
            game_id: ID of the game
            scores: Dict mapping user_id to score
            
        Returns:
            bool: True if ended successfully
        """
        pass
        
    @abstractmethod
    async def get_game_status(self, game_id: int) -> Optional[GameStatus]:
        """Get the current status of a game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Optional[GameStatus]: Game status if found
        """
        pass
        
    @abstractmethod
    async def get_player_status(self, game_id: int, user_id: int) -> Optional[PlayerStatus]:
        """Get a player's status in a game.
        
        Args:
            game_id: ID of the game
            user_id: ID of the user
            
        Returns:
            Optional[PlayerStatus]: Player status if found
        """
        pass
        
    @abstractmethod
    async def get_all_players(self, game_id: int) -> Dict[int, PlayerStatus]:
        """Get all players in a game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Dict[int, PlayerStatus]: Dict mapping user_id to status
        """
        pass
        
    @abstractmethod
    async def update_player_activity(self, game_id: int, user_id: int) -> bool:
        """Update a player's last active timestamp.
        
        Args:
            game_id: ID of the game
            user_id: ID of the user
            
        Returns:
            bool: True if updated successfully
        """
        pass
        
    @abstractmethod
    async def check_game_ready(self, game_id: int) -> Tuple[bool, Optional[str]]:
        """Check if a game is ready to start.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Tuple[bool, Optional[str]]: (ready, reason if not ready)
        """
        pass
