"""
User management service for the Myth metaserver.

This module implements the user management interface, handling user accounts,
profiles, rankings, and statistics.
"""

import asyncio
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from email.message import EmailMessage

from ..interfaces.user_interface import (
    UserInterface,
    UserProfile,
    UserStats,
    UserRank,
    UserRole,
    UserStatus
)

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

class UserService(UserInterface):
    """Service for managing user accounts."""
    
    def __init__(self):
        # In-memory storage (replace with database later)
        self.profiles: Dict[int, UserProfile] = {}
        self.stats: Dict[int, UserStats] = {}
        self.ranks: Dict[int, UserRank] = {}
        self.passwords: Dict[int, str] = {}  # Stores hashed passwords
        self.reset_tokens: Dict[str, tuple] = {}  # token -> (user_id, expiry)
        self.next_user_id: int = 1
        
    async def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """Create a new user account."""
        # Check if username/email already exists
        for profile in self.profiles.values():
            if profile.username.lower() == username.lower():
                return None
            if profile.email.lower() == email.lower():
                return None
                
        user_id = self.next_user_id
        self.next_user_id += 1
        
        # Create profile
        profile = UserProfile(
            user_id=user_id,
            username=username,
            email=email
        )
        self.profiles[user_id] = profile
        
        # Initialize stats and rank
        self.stats[user_id] = UserStats(user_id=user_id)
        self.ranks[user_id] = UserRank(user_id=user_id)
        
        # Store hashed password
        self.passwords[user_id] = hash_password(password)
        
        logger.info(f"Created user account for {username}")
        return user_id
        
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get a user's profile information."""
        return self.profiles.get(user_id)
        
    async def update_profile(self, user_id: int, updates: Dict) -> bool:
        """Update a user's profile information."""
        profile = self.profiles.get(user_id)
        if not profile:
            return False
            
        # Update allowed fields
        allowed_fields = {'avatar_url', 'bio'}
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(profile, field, value)
                
        logger.info(f"Updated profile for user {user_id}")
        return True
        
    async def set_user_status(self, user_id: int, status: UserStatus) -> bool:
        """Set a user's account status."""
        profile = self.profiles.get(user_id)
        if not profile:
            return False
            
        profile.status = status
        logger.info(f"Set status {status} for user {user_id}")
        return True
        
    async def set_user_role(self, user_id: int, role: UserRole) -> bool:
        """Set a user's permission role."""
        profile = self.profiles.get(user_id)
        if not profile:
            return False
            
        profile.role = role
        logger.info(f"Set role {role} for user {user_id}")
        return True
        
    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get a user's gameplay statistics."""
        return self.stats.get(user_id)
        
    async def update_stats(self, user_id: int, game_stats: Dict) -> bool:
        """Update a user's statistics after a game."""
        stats = self.stats.get(user_id)
        if not stats:
            return False
            
        # Update stats
        stats.games_played += 1
        if game_stats.get('won', False):
            stats.games_won += 1
        stats.total_score += game_stats.get('score', 0)
        stats.kills += game_stats.get('kills', 0)
        stats.deaths += game_stats.get('deaths', 0)
        stats.assists += game_stats.get('assists', 0)
        stats.last_game = datetime.now()
        
        # Update rank points
        points = game_stats.get('rank_points', 0)
        if points:
            await self.update_rank(user_id, points)
            
        logger.info(f"Updated stats for user {user_id}")
        return True
        
    async def get_user_rank(self, user_id: int) -> Optional[UserRank]:
        """Get a user's ranking information."""
        return self.ranks.get(user_id)
        
    async def update_rank(self, user_id: int, points_delta: int) -> bool:
        """Update a user's rank points."""
        rank = self.ranks.get(user_id)
        if not rank:
            return False
            
        # Update points
        rank.rank_points += points_delta
        rank.season_points += points_delta
        
        # Update highest points if needed
        if rank.rank_points > rank.highest_points:
            rank.highest_points = rank.rank_points
            
        # Calculate new level (every 1000 points)
        new_level = rank.rank_points // 1000
        if new_level != rank.rank_level:
            rank.rank_level = new_level
            if new_level > rank.highest_level:
                rank.highest_level = new_level
                
        # Update rank title
        rank.rank_title = self._get_rank_title(rank.rank_level)
        
        rank.last_update = datetime.now()
        logger.info(f"Updated rank for user {user_id}")
        return True
        
    async def get_top_players(self, limit: int = 10) -> List[Dict]:
        """Get the top ranked players."""
        # Sort players by rank points
        sorted_ranks = sorted(
            self.ranks.values(),
            key=lambda r: r.rank_points,
            reverse=True
        )
        
        # Get top players
        top_players = []
        for rank in sorted_ranks[:limit]:
            profile = self.profiles[rank.user_id]
            top_players.append({
                'user_id': rank.user_id,
                'username': profile.username,
                'rank_points': rank.rank_points,
                'rank_level': rank.rank_level,
                'rank_title': rank.rank_title
            })
            
        return top_players
        
    async def verify_password(self, user_id: int, password: str) -> bool:
        """Verify a user's password."""
        stored_hash = self.passwords.get(user_id)
        if not stored_hash:
            return False
            
        return stored_hash == hash_password(password)
        
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        if not await self.verify_password(user_id, old_password):
            return False
            
        self.passwords[user_id] = hash_password(new_password)
        logger.info(f"Changed password for user {user_id}")
        return True
        
    async def reset_password(self, email: str) -> bool:
        """Initiate password reset for a user."""
        # Find user by email
        for profile in self.profiles.values():
            if profile.email.lower() == email.lower():
                # Generate reset token
                token = secrets.token_urlsafe(32)
                expiry = datetime.now() + timedelta(hours=24)
                self.reset_tokens[token] = (profile.user_id, expiry)
                
                # TODO: Send reset email
                logger.info(f"Generated password reset token for user {profile.user_id}")
                return True
                
        return False
        
    async def complete_reset(self, reset_token: str, new_password: str) -> bool:
        """Complete password reset with token."""
        if reset_token not in self.reset_tokens:
            return False
            
        user_id, expiry = self.reset_tokens[reset_token]
        if datetime.now() > expiry:
            del self.reset_tokens[reset_token]
            return False
            
        # Update password
        self.passwords[user_id] = hash_password(new_password)
        del self.reset_tokens[reset_token]
        
        logger.info(f"Reset password for user {user_id}")
        return True
        
    def _get_rank_title(self, level: int) -> str:
        """Get rank title for a given level."""
        if level < 5:
            return "Novice"
        elif level < 10:
            return "Apprentice"
        elif level < 20:
            return "Adept"
        elif level < 30:
            return "Expert"
        elif level < 50:
            return "Master"
        else:
            return "Grandmaster"

# Global instance
user_service = UserService()
