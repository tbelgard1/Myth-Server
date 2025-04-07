"""
Tests for the room service.
"""

import pytest
from datetime import datetime
from typing import Dict, Set

from core.interfaces.room_interface import RoomSettings, RoomState, RoomInfo
from core.services.room_service import RoomService

@pytest.fixture
async def room_service():
    """Create a room service instance."""
    return RoomService()

@pytest.fixture
def room_settings():
    """Create test room settings."""
    return RoomSettings(
        name="Test Room",
        max_players=4,
        password=None,
        map_name="Test Map",
        game_type="deathmatch",
        team_game=False,
        allow_spectators=True
    )

@pytest.mark.asyncio
async def test_room_creation(room_service: RoomService, room_settings: RoomSettings):
    """Test room creation."""
    # Create room
    room_id = await room_service.create_room(1, room_settings)
    assert room_id is not None
    
    # Verify room info
    room_info = await room_service.get_room_info(room_id)
    assert room_info is not None
    assert room_info.settings == room_settings
    assert room_info.host_id == 1
    assert room_info.state == RoomState.WAITING
    assert room_info.player_count == 0
    assert room_info.spectator_count == 0

@pytest.mark.asyncio
async def test_room_joining(room_service: RoomService, room_settings: RoomSettings):
    """Test joining rooms."""
    # Create room
    room_id = await room_service.create_room(1, room_settings)
    
    # Join as player
    assert await room_service.join_room(room_id, 2)
    
    # Verify player count
    room_info = await room_service.get_room_info(room_id)
    assert room_info.player_count == 1
    
    # Join as spectator
    assert await room_service.join_room(room_id, 3, as_spectator=True)
    
    # Verify spectator count
    room_info = await room_service.get_room_info(room_id)
    assert room_info.spectator_count == 1
    
    # Get room players
    players = await room_service.get_room_players(room_id)
    assert players is not None
    assert players['players'] == {2}
    assert players['spectators'] == {3}

@pytest.mark.asyncio
async def test_room_password(room_service: RoomService, room_settings: RoomSettings):
    """Test password-protected rooms."""
    # Create password-protected room
    room_settings.password = "secret123"
    room_id = await room_service.create_room(1, room_settings)
    
    # Try joining without password
    assert not await room_service.join_room(room_id, 2)
    
    # Try joining with wrong password
    assert not await room_service.join_room(room_id, 2, password="wrong")
    
    # Try joining with correct password
    assert await room_service.join_room(room_id, 2, password="secret123")

@pytest.mark.asyncio
async def test_room_game_lifecycle(room_service: RoomService, room_settings: RoomSettings):
    """Test game starting and ending in a room."""
    # Create room and add players
    room_id = await room_service.create_room(1, room_settings)
    await room_service.join_room(room_id, 1)
    await room_service.join_room(room_id, 2)
    
    # Start game
    game_id = await room_service.start_game(room_id, 1)
    assert game_id is not None
    
    # Verify room state
    room_info = await room_service.get_room_info(room_id)
    assert room_info.state == RoomState.IN_GAME
    assert room_info.game_id == game_id
    
    # End game
    assert await room_service.end_game(room_id)
    
    # Verify room state
    room_info = await room_service.get_room_info(room_id)
    assert room_info.state == RoomState.WAITING
    assert room_info.game_id is None

@pytest.mark.asyncio
async def test_room_settings_update(room_service: RoomService, room_settings: RoomSettings):
    """Test updating room settings."""
    # Create room
    room_id = await room_service.create_room(1, room_settings)
    
    # Update settings
    new_settings = RoomSettings(
        name="Updated Room",
        max_players=8,
        password="newpass",
        map_name="New Map",
        game_type="ctf",
        team_game=True,
        allow_spectators=False
    )
    
    # Try updating as non-host
    assert not await room_service.update_settings(room_id, 2, new_settings)
    
    # Update as host
    assert await room_service.update_settings(room_id, 1, new_settings)
    
    # Verify settings updated
    room_info = await room_service.get_room_info(room_id)
    assert room_info.settings == new_settings
    
    # Try joining without new password
    assert not await room_service.join_room(room_id, 2)
    
    # Try joining with new password
    assert await room_service.join_room(room_id, 2, password="newpass")

@pytest.mark.asyncio
async def test_room_cleanup(room_service: RoomService, room_settings: RoomSettings):
    """Test room cleanup when empty."""
    # Create room and add player
    room_id = await room_service.create_room(1, room_settings)
    await room_service.join_room(room_id, 1)
    
    # Leave room
    assert await room_service.leave_room(room_id, 1)
    
    # Verify room closed
    room_info = await room_service.get_room_info(room_id)
    assert room_info is None
