"""
Pytest configuration and fixtures.
"""

import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import MagicMock

# Set test environment
os.environ["MYTH_ENV"] = "test"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def auth_service() -> AsyncGenerator:
    """Get the auth service instance."""
    from core.auth.auth_service import auth_service
    await auth_service.initialize()
    yield auth_service
    await auth_service.cleanup()

@pytest.fixture
async def game_service() -> AsyncGenerator:
    """Get the game service instance."""
    from core.services.game_service import game_service
    await game_service.initialize()
    yield game_service
    await game_service.cleanup()

@pytest.fixture
async def room_service() -> AsyncGenerator:
    """Get the room service instance."""
    from core.services.room_service import room_service
    await room_service.initialize()
    yield room_service
    await room_service.cleanup()

@pytest.fixture
async def user_service() -> AsyncGenerator:
    """Get the user service instance."""
    from core.services.user_service import user_service
    await user_service.initialize()
    yield user_service
    await user_service.cleanup()

@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Get a mock configuration for testing."""
    return {
        "server": {
            "host": "127.0.0.1",
            "port": 5000,
            "debug": True
        },
        "database": {
            "url": "sqlite:///:memory:"
        },
        "auth": {
            "token_expiry": 3600,
            "session_timeout": 1800
        }
    }

@pytest.fixture
def mock_logger() -> MagicMock:
    """Get a mock logger for testing."""
    return MagicMock()

@pytest.fixture
def test_data() -> Dict[str, Any]:
    """Get common test data."""
    return {
        "test_user": {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        },
        "test_room": {
            "name": "Test Room",
            "max_players": 8,
            "game_type": "deathmatch",
            "map_name": "test_map"
        },
        "test_game": {
            "type": "deathmatch",
            "map": "test_map",
            "max_players": 8,
            "team_game": False
        }
    }
