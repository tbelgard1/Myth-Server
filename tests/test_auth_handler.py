"""
Tests for the authentication handler.
"""

import json
import pytest
from datetime import datetime

from core.auth.auth_handler import AuthHandler
from core.auth.session_manager import session_manager

@pytest.fixture
async def auth_handler():
    """Create an auth handler instance."""
    return AuthHandler()

@pytest.mark.asyncio
async def test_auth_request(auth_handler: AuthHandler):
    """Test authentication request handling."""
    # Create test request
    request = {
        "username": "testuser",
        "password": "password123"
    }
    data = json.dumps(request).encode()
    
    # Handle request
    await auth_handler.handle_auth_request("client1", data)
    
    # Verify session created
    user_id = session_manager.get_user_id("client1")
    assert user_id is not None

@pytest.mark.asyncio
async def test_auth_check(auth_handler: AuthHandler):
    """Test token validation request handling."""
    # First authenticate
    auth_request = {
        "username": "testuser",
        "password": "password123"
    }
    await auth_handler.handle_auth_request("client1", json.dumps(auth_request).encode())
    
    # Get token from session
    user_id = session_manager.get_user_id("client1")
    assert user_id is not None
    
    # Create token check request
    check_request = {
        "token": "test-token"  # Use actual token from auth response
    }
    data = json.dumps(check_request).encode()
    
    # Handle request
    await auth_handler.handle_auth_check("client1", data)

@pytest.mark.asyncio
async def test_password_change(auth_handler: AuthHandler):
    """Test password change request handling."""
    # First authenticate
    auth_request = {
        "username": "testuser",
        "password": "password123"
    }
    await auth_handler.handle_auth_request("client1", json.dumps(auth_request).encode())
    
    # Create password change request
    change_request = {
        "old_password": "password123",
        "new_password": "newpass123"
    }
    data = json.dumps(change_request).encode()
    
    # Handle request
    await auth_handler.handle_password_change("client1", data)
    
    # Verify can authenticate with new password
    new_auth_request = {
        "username": "testuser",
        "password": "newpass123"
    }
    await auth_handler.handle_auth_request("client2", json.dumps(new_auth_request).encode())
    assert session_manager.get_user_id("client2") is not None

@pytest.mark.asyncio
async def test_invalid_requests(auth_handler: AuthHandler):
    """Test handling of invalid requests."""
    # Invalid JSON
    await auth_handler.handle_auth_request("client1", b"invalid json")
    assert session_manager.get_user_id("client1") is None
    
    # Missing fields
    request = {}
    await auth_handler.handle_auth_request("client1", json.dumps(request).encode())
    assert session_manager.get_user_id("client1") is None
    
    # Invalid credentials
    request = {
        "username": "testuser",
        "password": "wrongpass"
    }
    await auth_handler.handle_auth_request("client1", json.dumps(request).encode())
    assert session_manager.get_user_id("client1") is None
