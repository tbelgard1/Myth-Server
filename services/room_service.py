"""
Room service for the Myth metaserver.

This module implements the room management interface, providing functionality
for creating and managing game rooms, handling player joins/leaves, and
coordinating game starts/ends.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from core.interfaces.room_interface import RoomInterface, RoomInfo, RoomSettings, RoomState
from core.models.game import GameData
from core.services.game_service import game_service

logger = logging.getLogger(__name__)

@dataclass
class Room:
    """Internal room state."""
    info: RoomInfo
    players: Set[int] = field(default_factory=set)
    spectators: Set[int] = field(default_factory=set)
    password: Optional[str] = None

class RoomService(RoomInterface):
    """Service for managing game rooms."""
    def __init__(self):
        self.rooms: Dict[int, Room] = {}
        self.next_room_id: int = 1

    async def create_room(self, host_id: int, settings: RoomSettings) -> Optional[int]:
        """Create a new game room."""
        room_id = self.next_room_id
        self.next_room_id += 1
        
        room_info = RoomInfo(
            room_id=room_id,
            settings=settings,
            host_id=host_id,
            state=RoomState.WAITING,
            player_count=0,
            spectator_count=0,
            created_at=datetime.now()
        )
        
        room = Room(info=room_info)
        if settings.password:
            room.password = settings.password
            
        self.rooms[room_id] = room
        logger.info(f"Created room {room_id}: {settings.name}")
        return room_id
        
    async def close_room(self, room_id: int) -> bool:
        """Close a game room."""
        room = self.rooms.get(room_id)
        if not room:
            return False
            
        # End game if in progress
        if room.info.game_id is not None:
            await game_service.end_game(room.info.game_id)
            
        del self.rooms[room_id]
        logger.info(f"Closed room {room_id}")
        return True
        
    async def get_room_info(self, room_id: int) -> Optional[RoomInfo]:
        """Get information about a room."""
        room = self.rooms.get(room_id)
        return room.info if room else None
        
    async def list_rooms(self, include_closed: bool = False) -> List[RoomInfo]:
        """List all game rooms."""
        rooms = []
        for room in self.rooms.values():
            if include_closed or room.info.state != RoomState.CLOSED:
                rooms.append(room.info)
        return rooms
        
    async def join_room(self, room_id: int, user_id: int, password: Optional[str] = None, as_spectator: bool = False) -> bool:
        """Join a game room."""
        room = self.rooms.get(room_id)
        if not room:
            return False
            
        # Check room state
        if room.info.state not in (RoomState.WAITING, RoomState.STARTING):
            return False
            
        # Check password
        if room.password and password != room.password:
            return False
            
        # Check capacity for players
        if not as_spectator:
            if len(room.players) >= room.info.settings.max_players:
                return False
                
            if user_id in room.players:
                return True  # Already in room
                
            room.players.add(user_id)
            room.info.player_count = len(room.players)
            
        # Handle spectators
        else:
            if not room.info.settings.allow_spectators:
                return False
                
            if user_id in room.spectators:
                return True  # Already spectating
                
            room.spectators.add(user_id)
            room.info.spectator_count = len(room.spectators)
            
        logger.info(f"User {user_id} joined room {room_id} as {'spectator' if as_spectator else 'player'}")
        return True
        
    async def leave_room(self, room_id: int, user_id: int) -> bool:
        """Leave a game room."""
        room = self.rooms.get(room_id)
        if not room:
            return False
            
        # Remove from players
        if user_id in room.players:
            room.players.remove(user_id)
            room.info.player_count = len(room.players)
            
        # Remove from spectators
        if user_id in room.spectators:
            room.spectators.remove(user_id)
            room.info.spectator_count = len(room.spectators)
            
        # Close empty rooms
        if not room.players and not room.spectators:
            await self.close_room(room_id)
            
        logger.info(f"User {user_id} left room {room_id}")
        return True
        
    async def start_game(self, room_id: int, host_id: int) -> Optional[int]:
        """Start a game in a room."""
        room = self.rooms.get(room_id)
        if not room or room.info.host_id != host_id:
            return None
            
        # Check room state
        if room.info.state != RoomState.WAITING:
            return None
            
        # Need at least one player
        if not room.players:
            return None
            
        # Create game
        game_id = await game_service.create_game({
            'type': room.info.settings.game_type,
            'map': room.info.settings.map_name,
            'team_game': room.info.settings.team_game,
            'max_players': room.info.settings.max_players
        })
        
        if game_id is None:
            return None
            
        # Add players to game
        for player_id in room.players:
            await game_service.add_player(game_id, player_id)
            
        # Update room state
        room.info.state = RoomState.IN_GAME
        room.info.game_id = game_id
        
        logger.info(f"Started game {game_id} in room {room_id}")
        return game_id
        
    async def end_game(self, room_id: int) -> bool:
        """End the game in a room."""
        room = self.rooms.get(room_id)
        if not room or room.info.game_id is None:
            return False
            
        # End game
        await game_service.end_game(room.info.game_id)
        
        # Update room state
        room.info.state = RoomState.WAITING
        room.info.game_id = None
        
        logger.info(f"Ended game in room {room_id}")
        return True
        
    async def get_room_players(self, room_id: int) -> Optional[Dict[str, Set[int]]]:
        """Get players in a room."""
        room = self.rooms.get(room_id)
        if not room:
            return None
            
        return {
            'players': room.players.copy(),
            'spectators': room.spectators.copy()
        }
        
    async def update_settings(self, room_id: int, host_id: int, settings: RoomSettings) -> bool:
        """Update room settings."""
        room = self.rooms.get(room_id)
        if not room or room.info.host_id != host_id:
            return False
            
        # Can't change settings during game
        if room.info.state == RoomState.IN_GAME:
            return False
            
        # Update settings
        room.info.settings = settings
        if settings.password:
            room.password = settings.password
            
        logger.info(f"Updated settings for room {room_id}")
        return True
