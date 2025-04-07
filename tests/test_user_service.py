"""
Tests for the user management service.
"""

import pytest
from datetime import datetime, timedelta

from core.interfaces.user_interface import UserRole, UserStatus
from core.services.user_service import UserService

@pytest.fixture
async def user_service():
    """Create a user service instance."""
    return UserService()

@pytest.mark.asyncio
async def test_user_creation(user_service: UserService):
    """Test user account creation."""
    # Create user
    user_id = await user_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    assert user_id is not None
    
    # Verify profile
    profile = await user_service.get_user_profile(user_id)
    assert profile is not None
    assert profile.username == "testuser"
    assert profile.email == "test@example.com"
    assert profile.role == UserRole.PLAYER
    assert profile.status == UserStatus.ACTIVE
    
    # Check duplicate username/email
    assert await user_service.create_user(
        username="testuser",
        email="other@example.com",
        password="password123"
    ) is None
    
    assert await user_service.create_user(
        username="otheruser",
        email="test@example.com",
        password="password123"
    ) is None

@pytest.mark.asyncio
async def test_profile_management(user_service: UserService):
    """Test profile management."""
    # Create user
    user_id = await user_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    # Update profile
    assert await user_service.update_profile(user_id, {
        'avatar_url': 'http://example.com/avatar.jpg',
        'bio': 'Test bio'
    })
    
    # Verify updates
    profile = await user_service.get_user_profile(user_id)
    assert profile.avatar_url == 'http://example.com/avatar.jpg'
    assert profile.bio == 'Test bio'
    
    # Set status
    assert await user_service.set_user_status(user_id, UserStatus.BANNED)
    profile = await user_service.get_user_profile(user_id)
    assert profile.status == UserStatus.BANNED
    
    # Set role
    assert await user_service.set_user_role(user_id, UserRole.MODERATOR)
    profile = await user_service.get_user_profile(user_id)
    assert profile.role == UserRole.MODERATOR

@pytest.mark.asyncio
async def test_stats_management(user_service: UserService):
    """Test statistics management."""
    # Create user
    user_id = await user_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    # Get initial stats
    stats = await user_service.get_user_stats(user_id)
    assert stats.games_played == 0
    assert stats.games_won == 0
    
    # Update stats
    assert await user_service.update_stats(user_id, {
        'won': True,
        'score': 100,
        'kills': 5,
        'deaths': 2,
        'assists': 3,
        'rank_points': 50
    })
    
    # Verify stats
    stats = await user_service.get_user_stats(user_id)
    assert stats.games_played == 1
    assert stats.games_won == 1
    assert stats.total_score == 100
    assert stats.kills == 5
    assert stats.deaths == 2
    assert stats.assists == 3
    assert stats.last_game is not None

@pytest.mark.asyncio
async def test_rank_system(user_service: UserService):
    """Test ranking system."""
    # Create user
    user_id = await user_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    # Get initial rank
    rank = await user_service.get_user_rank(user_id)
    assert rank.rank_points == 0
    assert rank.rank_level == 0
    assert rank.rank_title == "Novice"
    
    # Update rank
    assert await user_service.update_rank(user_id, 1500)
    
    # Verify rank changes
    rank = await user_service.get_user_rank(user_id)
    assert rank.rank_points == 1500
    assert rank.rank_level == 1
    assert rank.rank_title == "Novice"
    assert rank.highest_points == 1500
    assert rank.highest_level == 1
    
    # Check top players
    top_players = await user_service.get_top_players(limit=1)
    assert len(top_players) == 1
    assert top_players[0]['user_id'] == user_id
    assert top_players[0]['rank_points'] == 1500

@pytest.mark.asyncio
async def test_password_management(user_service: UserService):
    """Test password management."""
    # Create user
    user_id = await user_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    # Verify password
    assert await user_service.verify_password(user_id, "password123")
    assert not await user_service.verify_password(user_id, "wrongpass")
    
    # Change password
    assert await user_service.change_password(
        user_id,
        old_password="password123",
        new_password="newpass123"
    )
    
    # Verify new password
    assert await user_service.verify_password(user_id, "newpass123")
    assert not await user_service.verify_password(user_id, "password123")

@pytest.mark.asyncio
async def test_password_reset(user_service: UserService):
    """Test password reset flow."""
    # Create user
    await user_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    # Request reset
    assert await user_service.reset_password("test@example.com")
    assert not await user_service.reset_password("wrong@example.com")
    
    # Get reset token (normally sent via email)
    token = next(iter(user_service.reset_tokens.keys()))
    
    # Complete reset
    assert await user_service.complete_reset(token, "newpass123")
    assert not await user_service.complete_reset("wrongtoken", "newpass123")
    
    # Verify token consumed
    assert token not in user_service.reset_tokens
