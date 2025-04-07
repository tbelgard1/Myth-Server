"""
Tests for the game service.
"""

import pytest
from datetime import datetime, timedelta
from core.services.game_service import GameService
from core.models.game import GameType, GameFlags, GameOptions
from core.models.game_search_types import NewGameParameterData

@pytest.mark.asyncio
async def test_game_service_create_game(game_service: GameService):
    """Test game creation."""
    # Create game parameters
    params = NewGameParameterData()
    params.type = GameType.BODY_COUNT
    params.maximum_players = 8
    
    # Create game
    game_id = await game_service.create_game(params)
    assert game_id is not None
    
    # Verify game exists
    game = await game_service.get_game_data(game_id)
    assert game is not None
    assert game.game_id == game_id
    assert game.game_type == GameType.BODY_COUNT
    assert game.max_players == 8
    assert game.player_count == 0

@pytest.mark.asyncio
async def test_game_service_player_management(game_service: GameService):
    """Test adding/removing players."""
    # Create game
    params = NewGameParameterData()
    params.type = GameType.BODY_COUNT
    params.maximum_players = 4
    game_id = await game_service.create_game(params)
    assert game_id is not None
    
    # Add players
    assert await game_service.add_player(game_id, 1)
    assert await game_service.add_player(game_id, 2)
    
    # Verify players added
    game = await game_service.get_game_data(game_id)
    assert game is not None
    assert game.player_count == 2
    assert 1 in game.player_ids
    assert 2 in game.player_ids
    
    # Remove player
    assert await game_service.remove_player(game_id, 1)
    
    # Verify player removed
    game = await game_service.get_game_data(game_id)
    assert game is not None
    assert game.player_count == 1
    assert 1 not in game.player_ids
    assert 2 in game.player_ids

@pytest.mark.asyncio
async def test_game_service_game_lifecycle(game_service: GameService):
    """Test game lifecycle (create -> start -> end)."""
    # Create game
    params = NewGameParameterData()
    params.type = GameType.BODY_COUNT
    params.maximum_players = 2
    game_id = await game_service.create_game(params)
    assert game_id is not None
    
    # Add players
    assert await game_service.add_player(game_id, 1)
    assert await game_service.add_player(game_id, 2)
    
    # Start game
    assert await game_service.start_game(game_id, "Test Map")
    
    # Verify game started
    game = await game_service.get_game_data(game_id)
    assert game is not None
    assert game.flags & GameFlags.IN_PROGRESS
    assert game.map_name == "Test Map"
    
    # End game with scores
    player_scores = {1: 100, 2: 50}
    assert await game_service.end_game(game_id, player_scores)
    
    # Verify game ended and logged
    game = await game_service.get_game_data(game_id)
    assert game is None  # Game should be removed from active games
    
    # Check game logs
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)
    logs = await game_service.get_game_logs(start_time, end_time)
    assert len(logs) > 0
    latest_log = logs[-1]
    assert latest_log.game_id == game_id
    assert latest_log.player_ids == [1, 2]
    assert latest_log.player_scores == [100, 50]

@pytest.mark.asyncio
async def test_game_service_game_description(game_service: GameService):
    """Test game description retrieval."""
    # Create game
    params = NewGameParameterData()
    params.type = GameType.CAPTURE_THE_FLAG
    params.maximum_players = 6
    game_id = await game_service.create_game(params)
    assert game_id is not None
    
    # Get description
    desc = await game_service.get_game_description(game_id)
    assert desc is not None
    assert desc.parameters.type == GameType.CAPTURE_THE_FLAG
    assert desc.player_count == 0
