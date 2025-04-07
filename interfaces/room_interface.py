"""
Room management interface for the Myth metaserver.

This module defines the interface for managing game rooms, including room
creation, player management, and room state tracking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set

class RoomState(Enum):
    """Possible states for a room."""
    WAITING = auto()  # Room is waiting for players
    STARTING = auto()  # Game is about to start
    IN_GAME = auto()  # Game is in progress
    ENDING = auto()  # Game is ending
    CLOSED = auto()  # Room is closed

@dataclass
class RoomSettings:
    """Settings for a game room."""
    name: str
    max_players: int
    password: Optional[str] = None
    map_name: Optional[str] = None
    game_type: Optional[str] = None
    team_game: bool = False
    allow_spectators: bool = True

@dataclass
class RoomInfo:
    """Information about a game room."""
    room_id: int
    settings: RoomSettings
    host_id: int
    state: RoomState
    player_count: int
    spectator_count: int
    created_at: datetime
    game_id: Optional[int] = None

class RoomInterface(ABC):
    """Interface for room management operations."""
    
    @abstractmethod
    async def create_room(self, host_id: int, settings: RoomSettings) -> Optional[int]:
        """Create a new game room.
        
        Args:
            host_id: ID of the user creating the room
            settings: Room settings
            
        Returns:
            Optional[int]: Room ID if created successfully
        """
        pass
        
    @abstractmethod
    async def close_room(self, room_id: int) -> bool:
        """Close a game room.
        
        Args:
            room_id: ID of the room to close
            
        Returns:
            bool: True if closed successfully
        """
        pass
        
    @abstractmethod
    async def get_room_info(self, room_id: int) -> Optional[RoomInfo]:
        """Get information about a room.
        
        Args:
            room_id: ID of the room
            
        Returns:
            Optional[RoomInfo]: Room information if found
        """
        pass
        
    @abstractmethod
    async def list_rooms(self, include_closed: bool = False) -> List[RoomInfo]:
        """List all game rooms.
        
        Args:
            include_closed: Whether to include closed rooms
            
        Returns:
            List[RoomInfo]: List of room information
        """
        pass
        
    @abstractmethod
    async def join_room(self, room_id: int, user_id: int, password: Optional[str] = None, as_spectator: bool = False) -> bool:
        """Join a game room.
        
        Args:
            room_id: ID of the room to join
            user_id: ID of the user joining
            password: Room password if required
            as_spectator: Whether to join as a spectator
            
        Returns:
            bool: True if joined successfully
        """
        pass
        
    @abstractmethod
    async def leave_room(self, room_id: int, user_id: int) -> bool:
        """Leave a game room.
        
        Args:
            room_id: ID of the room to leave
            user_id: ID of the user leaving
            
        Returns:
            bool: True if left successfully
        """
        pass
        
    @abstractmethod
    async def start_game(self, room_id: int, host_id: int) -> Optional[int]:
        """Start a game in a room.
        
        Args:
            room_id: ID of the room
            host_id: ID of the host starting the game
            
        Returns:
            Optional[int]: Game ID if started successfully
        """
        pass
        
    @abstractmethod
    async def end_game(self, room_id: int) -> bool:
        """End the game in a room.
        
        Args:
            room_id: ID of the room
            
        Returns:
            bool: True if ended successfully
        """
        pass
        
    @abstractmethod
    async def get_room_players(self, room_id: int) -> Optional[Dict[str, Set[int]]]:
        """Get players in a room.
        
        Args:
            room_id: ID of the room
            
        Returns:
            Optional[Dict[str, Set[int]]]: Dict with 'players' and 'spectators' sets
                                         of user IDs if room found
        """
        pass
        
    @abstractmethod
    async def update_settings(self, room_id: int, host_id: int, settings: RoomSettings) -> bool:
        """Update room settings.
        
        Args:
            room_id: ID of the room
            host_id: ID of the host making changes
            settings: New room settings
            
        Returns:
            bool: True if updated successfully
        """
        pass
