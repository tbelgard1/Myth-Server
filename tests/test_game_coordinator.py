"""
Tests for the game coordinator service.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict

from core.interfaces.game_coordinator_interface import GameState
from core.services.game_coordinator import GameCoordinator

@pytest.fixture
async def coordinator():
    """Create a game coordinator instance."""
    coord = GameCoordinator()
    await coord.start()
    yield coord
    await coord.stop()

@pytest.fixture
def game_settings():
    """Create test game settings."""
    return {
        'map': 'Test Map',
        'max_players': 4,
        'team_game': False
    }

@pytest.mark.asyncio
async def test_game_initialization(coordinator: GameCoordinator, game_settings: Dict):
    """Test game initialization."""
    # Initialize game
    assert await coordinator.initialize_game(1, game_settings)
    
    # Verify game status
    status = await coordinator.get_game_status(1)
    assert status is not None
    assert status.state == GameState.INITIALIZING
    assert status.map_name == game_settings['map']
    assert status.max_players == game_settings['max_players']
    assert status.team_game == game_settings['team_game']
    assert status.player_count == 0

@pytest.mark.asyncio
async def test_player_management(coordinator: GameCoordinator, game_settings: Dict):
    """Test player management."""
    # Initialize game
    await coordinator.initialize_game(1, game_settings)
    
    # Add players
    assert await coordinator.add_player(1, 101)
    assert await coordinator.add_player(1, 102)
    
    # Verify player count
    status = await coordinator.get_game_status(1)
    assert status.player_count == 2
    
    # Get player statuses
    players = await coordinator.get_all_players(1)
    assert len(players) == 2
    assert 101 in players
    assert 102 in players
    
    # Remove player
    assert await coordinator.remove_player(1, 101)
    status = await coordinator.get_game_status(1)
    assert status.player_count == 1

@pytest.mark.asyncio
async def test_team_game(coordinator: GameCoordinator):
    """Test team game coordination."""
    # Initialize team game
    settings = {
        'map': 'Team Map',
        'max_players': 4,
        'team_game': True
    }
    await coordinator.initialize_game(1, settings)
    
    # Add players
    await coordinator.add_player(1, 101)
    await coordinator.add_player(1, 102)
    await coordinator.add_player(1, 103)
    await coordinator.add_player(1, 104)
    
    # Assign teams
    assert await coordinator.set_player_team(1, 101, 0)
    assert await coordinator.set_player_team(1, 102, 0)
    assert await coordinator.set_player_team(1, 103, 1)
    assert await coordinator.set_player_team(1, 104, 1)
    
    # Set all ready
    for user_id in (101, 102, 103, 104):
        assert await coordinator.set_player_ready(1, user_id)
    
    # Verify game ready
    ready, reason = await coordinator.check_game_ready(1)
    assert ready
    assert reason is None

@pytest.mark.asyncio
async def test_game_lifecycle(coordinator: GameCoordinator, game_settings: Dict):
    """Test game lifecycle."""
    # Initialize and add players
    await coordinator.initialize_game(1, game_settings)
    await coordinator.add_player(1, 101)
    await coordinator.add_player(1, 102)
    
    # Set players ready
    await coordinator.set_player_ready(1, 101)
    await coordinator.set_player_ready(1, 102)
    
    # Start game
    assert await coordinator.start_game(1)
    status = await coordinator.get_game_status(1)
    assert status.state == GameState.IN_PROGRESS
    assert status.start_time is not None
    
    # End game
    scores = {101: 10, 102: 5}
    assert await coordinator.end_game(1, scores)
    
    # Verify game cleaned up
    status = await coordinator.get_game_status(1)
    assert status is None

@pytest.mark.asyncio
async def test_inactive_cleanup(coordinator: GameCoordinator, game_settings: Dict):
    """Test cleanup of inactive games."""
    # Initialize and start game
    await coordinator.initialize_game(1, game_settings)
    await coordinator.add_player(1, 101)
    await coordinator.set_player_ready(1, 101)
    await coordinator.start_game(1)
    
    # Set last active time to long ago
    game_players = coordinator.players[1]
    old_time = datetime.now() - timedelta(minutes=31)
    for status in game_players.values():
        status.last_active = old_time
    
    # Wait for cleanup
    await asyncio.sleep(65)
    
    # Verify game cleaned up
    status = await coordinator.get_game_status(1)
    assert status is None

@pytest.mark.asyncio
async def test_player_activity(coordinator: GameCoordinator, game_settings: Dict):
    """Test player activity tracking."""
    # Initialize game
    await coordinator.initialize_game(1, game_settings)
    await coordinator.add_player(1, 101)
    
    # Update activity
    old_time = coordinator.players[1][101].last_active
    await asyncio.sleep(1)
    
    assert await coordinator.update_player_activity(1, 101)
    new_time = coordinator.players[1][101].last_active
    
    assert new_time > old_time
