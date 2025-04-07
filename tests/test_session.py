"""
Tests for session management.
"""

import asyncio
import pytest
from datetime import datetime, timedelta

from core.auth.session_manager import SessionManager
from core.interfaces.auth_interface import AuthToken

@pytest.fixture
async def session_manager():
    """Create a session manager instance."""
    manager = SessionManager()
    await manager.start()
    yield manager
    await manager.stop()

@pytest.fixture
def auth_token():
    """Create a test auth token."""
    return AuthToken(
        token="test-token",
        user_id=1,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=1)
    )

@pytest.mark.asyncio
async def test_session_create(session_manager: SessionManager, auth_token: AuthToken):
    """Test session creation."""
    # Create session
    success = await session_manager.create_session(auth_token, "client1")
    assert success
    
    # Verify session mappings
    assert session_manager.get_user_id("client1") == auth_token.user_id
    assert "client1" in session_manager.get_client_ids(auth_token.user_id)

@pytest.mark.asyncio
async def test_session_end(session_manager: SessionManager, auth_token: AuthToken):
    """Test session ending."""
    # Create and end session
    await session_manager.create_session(auth_token, "client1")
    await session_manager.end_session("client1")
    
    # Verify session removed
    assert session_manager.get_user_id("client1") is None
    assert "client1" not in session_manager.get_client_ids(auth_token.user_id)

@pytest.mark.asyncio
async def test_multiple_sessions(session_manager: SessionManager, auth_token: AuthToken):
    """Test multiple sessions for same user."""
    # Create multiple sessions
    await session_manager.create_session(auth_token, "client1")
    await session_manager.create_session(auth_token, "client2")
    
    # Verify both sessions exist
    assert session_manager.get_user_id("client1") == auth_token.user_id
    assert session_manager.get_user_id("client2") == auth_token.user_id
    
    client_ids = session_manager.get_client_ids(auth_token.user_id)
    assert "client1" in client_ids
    assert "client2" in client_ids
    
    # End one session
    await session_manager.end_session("client1")
    
    # Verify only client2 remains
    assert session_manager.get_user_id("client1") is None
    assert session_manager.get_user_id("client2") == auth_token.user_id
    assert session_manager.get_client_ids(auth_token.user_id) == {"client2"}

@pytest.mark.asyncio
async def test_invalid_token(session_manager: SessionManager):
    """Test session creation with invalid token."""
    invalid_token = AuthToken(
        token="invalid",
        user_id=999,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=1)
    )
    
    success = await session_manager.create_session(invalid_token, "client1")
    assert not success
    assert session_manager.get_user_id("client1") is None
