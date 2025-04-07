"""
Room list management service for Myth metaserver.

This module provides functionality for managing room templates, including:
- Loading/saving room lists from files
- Adding/updating/deleting room templates
- Converting between game names and flags
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import IntFlag
import os
import sys
import logging

logger = logging.getLogger(__name__)

class GameTypeFlags(IntFlag):
    """Game type flags"""
    MYTH1 = 1 << 0
    MYTH2 = 1 << 1
    MYTH3 = 1 << 2
    MARATHON = 1 << 3
    JCHAT = 1 << 4

# Room type mapping
ROOM_TYPES: List[Tuple[str, GameTypeFlags]] = [
    ("MYTH", GameTypeFlags.MYTH1 | GameTypeFlags.MYTH2 | GameTypeFlags.MYTH3),
    ("MYTH1", GameTypeFlags.MYTH1),
    ("MYTH2", GameTypeFlags.MYTH2),
    ("MYTH3", GameTypeFlags.MYTH3),
    ("MARATHON", GameTypeFlags.MARATHON),
    ("JCHAT", GameTypeFlags.JCHAT),
]

@dataclass
class RoomData:
    """Room data structure"""
    supported_application_flags: GameTypeFlags
    ranked_room: bool
    room_identifier: int
    country_code: int
    minimum_caste: int
    maximum_caste: int
    tournament_room: bool
    used: bool = False
    next: Optional['RoomData'] = None

def get_supported_application_flags_from_name_list(name_list: str) -> GameTypeFlags:
    """Convert a comma-separated list of game names to application flags
    
    Args:
        name_list: Comma-separated list of game names
        
    Returns:
        Combined game type flags
    """
    flags = GameTypeFlags(0)
    names = name_list.split(',')
    
    for name in names:
        name = name.strip().upper()
        for room_type, type_flags in ROOM_TYPES:
            if name == room_type:
                # Special case: old Myth2 1.3.x clients reporting as "MYTH"
                if name == "MYTH":
                    flags |= GameTypeFlags.MYTH2
                else:
                    flags |= type_flags
                break
    
    return flags

def get_name_list_from_supported_application_flags(flags: GameTypeFlags) -> str:
    """Convert application flags to a comma-separated list of game names
    
    Args:
        flags: Game type flags
        
    Returns:
        Comma-separated list of game names
    """
    names = []
    for room_type, type_flags in ROOM_TYPES:
        if flags & type_flags == type_flags:
            names.append(room_type)
    return ','.join(names) if names else "UNKNOWN"

def get_application_type_from_name(name: str) -> GameTypeFlags:
    """Get application flags for a single game name
    
    Args:
        name: Game name
        
    Returns:
        Game type flags
    """
    name = name.strip().upper()
    for room_type, type_flags in ROOM_TYPES:
        if name == room_type:
            # Special case: old Myth2 1.3.x clients reporting as "MYTH"
            return GameTypeFlags.MYTH2 if name == "MYTH" else type_flags
    return GameTypeFlags(0)

def load_room_list(filename: str) -> Optional[RoomData]:
    """Load room list from file
    
    Args:
        filename: Path to room list file
        
    Returns:
        Linked list of room data, or None if error
    """
    if not os.path.exists(filename):
        logger.error("No rooms list file found! The server will not be able to load any rooms!")
        return None

    rooms = None
    with open(filename, 'r') as fp:
        for line in fp:
            parts = line.strip().split()
            if len(parts) != 7:
                continue

            name_list = parts[0]
            room_id = int(parts[1])
            ranked = int(parts[2])
            country_code = int(parts[3])
            min_caste = int(parts[4])
            max_caste = int(parts[5])
            tournament_room = int(parts[6])

            flags = get_supported_application_flags_from_name_list(name_list)
            if flags:
                rooms = add_room(rooms, flags, room_id, ranked, country_code, 
                               min_caste, max_caste, tournament_room)
            else:
                logger.warning(f"Unrecognized name list in room list file '{name_list}'")

    return rooms

def save_room_list(rooms: Optional[RoomData], filename: str) -> bool:
    """Save room list to file
    
    Args:
        rooms: Linked list of room data
        filename: Path to save room list to
        
    Returns:
        True if saved successfully
    """
    try:
        with open(filename, 'w') as fp:
            room = rooms
            while room:
                fp.write(f"{get_name_list_from_supported_application_flags(room.supported_application_flags)} "
                        f"{room.room_identifier} {int(room.ranked_room)} {room.country_code} "
                        f"{room.minimum_caste} {room.maximum_caste} {int(room.tournament_room)}\n")
                room = room.next
        return True
    except IOError as e:
        logger.error(f"Error saving room list: {e}")
        return False

def list_room_templates(rooms: Optional[RoomData]) -> None:
    """List all room templates
    
    Args:
        rooms: Linked list of room data
    """
    print("Game\tRoomID\tRanked\tCountry\tMin Caste\tMax Caste\tTournament Room#")
    room = rooms
    while room:
        print(f"{get_name_list_from_supported_application_flags(room.supported_application_flags)} "
              f"{room.room_identifier} {int(room.ranked_room)} {room.country_code} "
              f"{room.minimum_caste} {room.maximum_caste} {int(room.tournament_room)}")
        room = room.next

def delete_room_template(rooms: Optional[RoomData], supported_application_flags: GameTypeFlags, 
                        room_identifier: int) -> Optional[RoomData]:
    """Delete a room template
    
    Args:
        rooms: Linked list of room data
        supported_application_flags: Game type flags for room
        room_identifier: Room ID to delete
        
    Returns:
        Updated room list
    """
    if not supported_application_flags:
        logger.error("No supported client flags!")
        return rooms

    previous = None
    room = rooms
    while room and (room.supported_application_flags != supported_application_flags or 
                   room.room_identifier != room_identifier):
        previous = room
        room = room.next

    if room:
        if previous:
            previous.next = room.next
        else:
            rooms = room.next
        logger.info("Room deleted!")
    else:
        logger.warning("Room not found!")

    return rooms

def add_or_update_room(rooms: Optional[RoomData], supported_application_flags: GameTypeFlags,
                       room_identifier: int, ranked_room: bool, country_code: int,
                       minimum_caste: int, maximum_caste: int, tournament_room: bool) -> Optional[RoomData]:
    """Add or update a room template
    
    Args:
        rooms: Linked list of room data
        supported_application_flags: Game type flags for room
        room_identifier: Room ID
        ranked_room: Whether room is ranked
        country_code: Country code for room
        minimum_caste: Minimum caste level required
        maximum_caste: Maximum caste level allowed
        tournament_room: Whether room is tournament mode
        
    Returns:
        Updated room list
    """
    if not supported_application_flags:
        logger.error("No supported client flags!")
        return rooms

    # Try to find and update existing room
    room = rooms
    while room:
        if (room.supported_application_flags == supported_application_flags and 
            room.room_identifier == room_identifier):
            room.ranked_room = ranked_room
            room.country_code = country_code
            room.minimum_caste = minimum_caste
            room.maximum_caste = maximum_caste
            room.tournament_room = tournament_room
            logger.info("Room updated!")
            return rooms
        room = room.next

    # Room not found, add new one
    return add_room(rooms, supported_application_flags, room_identifier, ranked_room,
                   country_code, minimum_caste, maximum_caste, tournament_room)

def add_room(rooms: Optional[RoomData], supported_application_flags: GameTypeFlags,
             room_id: int, ranked_room: bool, country_code: int,
             minimum_caste: int, maximum_caste: int, tournament_room: bool) -> Optional[RoomData]:
    """Add a new room
    
    Args:
        rooms: Linked list of room data
        supported_application_flags: Game type flags for room
        room_id: Room ID
        ranked_room: Whether room is ranked
        country_code: Country code for room
        minimum_caste: Minimum caste level required
        maximum_caste: Maximum caste level allowed
        tournament_room: Whether room is tournament mode
        
    Returns:
        Updated room list
    """
    new_room = RoomData(
        supported_application_flags=supported_application_flags,
        room_identifier=room_id,
        ranked_room=ranked_room,
        country_code=country_code,
        minimum_caste=minimum_caste,
        maximum_caste=maximum_caste,
        tournament_room=tournament_room
    )

    if not rooms:
        return new_room

    # Add to end of list
    current = rooms
    while current.next:
        current = current.next
    current.next = new_room
    return rooms
