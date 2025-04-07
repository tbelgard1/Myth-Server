"""
Tests for the authentication service.
"""

import pytest
from core.auth.auth_service import AuthService
from core.interfaces.auth_interface import AuthResult

@pytest.mark.asyncio
async def test_auth_service_create_user(auth_service: AuthService):
    """Test user creation."""
    # Create test user
    success, user_id = await auth_service.create_user("testuser", "password123")
    assert success
    assert user_id is not None
    
    # Verify user exists
    found_id = await auth_service.get_user_id("testuser")
    assert found_id == user_id

@pytest.mark.asyncio
async def test_auth_service_authenticate(auth_service: AuthService):
    """Test user authentication."""
    # Create test user
    success, user_id = await auth_service.create_user("authuser", "password123")
    assert success
    
    # Test valid authentication
    result = await auth_service.authenticate("authuser", "password123")
    assert result.success
    assert result.token is not None
    assert result.token.user_id == user_id
    
    # Test invalid password
    result = await auth_service.authenticate("authuser", "wrongpass")
    assert not result.success
    assert result.token is None
    assert result.error_message is not None
    
    # Test invalid username
    result = await auth_service.authenticate("nonexistent", "password123")
    assert not result.success
    assert result.token is None
    assert result.error_message is not None

@pytest.mark.asyncio
async def test_auth_service_token_validation(auth_service: AuthService):
    """Test token validation."""
    # Create and authenticate user
    success, user_id = await auth_service.create_user("tokenuser", "password123")
    assert success
    
    result = await auth_service.authenticate("tokenuser", "password123")
    assert result.success
    assert result.token is not None
    
    # Test token validation
    is_valid, found_id = await auth_service.validate_token(result.token.token)
    assert is_valid
    assert found_id == user_id
    
    # Test invalid token
    is_valid, found_id = await auth_service.validate_token("invalid-token")
    assert not is_valid
    assert found_id is None

@pytest.mark.asyncio
async def test_auth_service_change_password(auth_service: AuthService):
    """Test password change."""
    # Create test user
    success, user_id = await auth_service.create_user("pwuser", "oldpass123")
    assert success
    
    # Change password
    success = await auth_service.change_password(user_id, "oldpass123", "newpass123")
    assert success
    
    # Verify old password no longer works
    result = await auth_service.authenticate("pwuser", "oldpass123")
    assert not result.success
    
    # Verify new password works
    result = await auth_service.authenticate("pwuser", "newpass123")
    assert result.success

@pytest.mark.asyncio
async def test_auth_service_delete_user(auth_service: AuthService):
    """Test user deletion."""
    # Create test user
    success, user_id = await auth_service.create_user("deleteuser", "password123")
    assert success
    
    # Delete user
    success = await auth_service.delete_user(user_id)
    assert success
    
    # Verify user no longer exists
    found_id = await auth_service.get_user_id("deleteuser")
    assert found_id is None
