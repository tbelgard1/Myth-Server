"""
Room list file handling for the Myth metaserver.

This module handles reading and writing the room list configuration file
that defines available game rooms and their properties.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RoomDefinition:
    """Definition of a game room."""
    name: str = ""
    description: str = ""
    max_players: int = 32
    port: int = 0
    password_required: bool = False
    allow_observers: bool = True
    ranked: bool = True

@dataclass 
class RoomListFile:
    """Handles reading and writing room configuration files."""
    
    filename: str = "rooms.lst"
    rooms: List[RoomDefinition] = field(default_factory=list)
    
    def load(self) -> bool:
        """Load room definitions from file.
        
        Returns:
            True if successful, False if error
        """
        try:
            path = Path(self.filename)
            if not path.exists():
                logger.warning(f"Room list file {self.filename} not found")
                return False
                
            with open(self.filename, 'r') as f:
                data = json.load(f)
                
            self.rooms.clear()
            for room_data in data.get('rooms', []):
                room = RoomDefinition(
                    name=room_data.get('name', ''),
                    description=room_data.get('description', ''),
                    max_players=room_data.get('max_players', 32),
                    port=room_data.get('port', 0),
                    password_required=room_data.get('password_required', False),
                    allow_observers=room_data.get('allow_observers', True),
                    ranked=room_data.get('ranked', True)
                )
                self.rooms.append(room)
                
            logger.info(f"Loaded {len(self.rooms)} rooms from {self.filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading room list: {e}")
            return False
    
    def save(self) -> bool:
        """Save room definitions to file.
        
        Returns:
            True if successful, False if error
        """
        try:
            data = {
                'rooms': [
                    {
                        'name': room.name,
                        'description': room.description,
                        'max_players': room.max_players,
                        'port': room.port,
                        'password_required': room.password_required,
                        'allow_observers': room.allow_observers,
                        'ranked': room.ranked
                    }
                    for room in self.rooms
                ]
            }
            
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
                
            logger.info(f"Saved {len(self.rooms)} rooms to {self.filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving room list: {e}")
            return False
    
    def add_room(self, room: RoomDefinition) -> bool:
        """Add a new room definition.
        
        Args:
            room: Room definition to add
            
        Returns:
            True if successful, False if error
        """
        try:
            # Validate room
            if not room.name:
                logger.error("Room name cannot be empty")
                return False
                
            if room.port <= 0:
                logger.error("Invalid room port")
                return False
                
            # Check for duplicate name/port
            for existing in self.rooms:
                if existing.name == room.name:
                    logger.error(f"Room {room.name} already exists")
                    return False
                if existing.port == room.port:
                    logger.error(f"Port {room.port} already in use")
                    return False
            
            self.rooms.append(room)
            return True
            
        except Exception as e:
            logger.error(f"Error adding room: {e}")
            return False
    
    def remove_room(self, name: str) -> bool:
        """Remove a room definition by name.
        
        Args:
            name: Name of room to remove
            
        Returns:
            True if found and removed, False if not found
        """
        try:
            for i, room in enumerate(self.rooms):
                if room.name == name:
                    del self.rooms[i]
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing room: {e}")
            return False
    
    def get_room(self, name: str) -> Optional[RoomDefinition]:
        """Get a room definition by name.
        
        Args:
            name: Name of room to get
            
        Returns:
            Room definition if found, None if not found
        """
        try:
            for room in self.rooms:
                if room.name == name:
                    return room
            return None
            
        except Exception as e:
            logger.error(f"Error getting room: {e}")
            return None
