"""
User management interface for the Myth metaserver.

This module defines the interface and models for managing user accounts,
profiles, rankings, and statistics.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set

class UserRole(Enum):
    """User permission roles."""
    PLAYER = auto()      # Regular player
    MODERATOR = auto()   # Can moderate games and chat
    ADMIN = auto()       # Full administrative access

class UserStatus(Enum):
    """User account status."""
    ACTIVE = auto()      # Account is active
    BANNED = auto()      # Account is banned
    INACTIVE = auto()    # Account is inactive
    PENDING = auto()     # Email verification pending

@dataclass
class UserProfile:
    """User profile information."""
    user_id: int
    username: str
    email: str
    role: UserRole = UserRole.PLAYER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

@dataclass
class UserStats:
    """User gameplay statistics."""
    user_id: int
    games_played: int = 0
    games_won: int = 0
    total_score: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_game: Optional[datetime] = None

@dataclass
class UserRank:
    """User ranking information."""
    user_id: int
    rank_points: int = 0
    rank_level: int = 0
    rank_title: str = "Novice"
    highest_points: int = 0
    highest_level: int = 0
    season_points: int = 0
    season_rank: int = 0
    last_update: datetime = field(default_factory=datetime.now)

class UserInterface(ABC):
    """Interface for user management operations."""
    
    @abstractmethod
    async def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """Create a new user account.
        
        Args:
            username: Desired username
            email: User's email address
            password: User's password
            
        Returns:
            Optional[int]: User ID if created successfully
        """
        pass
        
    @abstractmethod
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get a user's profile information.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[UserProfile]: User profile if found
        """
        pass
        
    @abstractmethod
    async def update_profile(self, user_id: int, updates: Dict) -> bool:
        """Update a user's profile information.
        
        Args:
            user_id: ID of the user
            updates: Dict of profile fields to update
            
        Returns:
            bool: True if updated successfully
        """
        pass
        
    @abstractmethod
    async def set_user_status(self, user_id: int, status: UserStatus) -> bool:
        """Set a user's account status.
        
        Args:
            user_id: ID of the user
            status: New account status
            
        Returns:
            bool: True if status updated successfully
        """
        pass
        
    @abstractmethod
    async def set_user_role(self, user_id: int, role: UserRole) -> bool:
        """Set a user's permission role.
        
        Args:
            user_id: ID of the user
            role: New user role
            
        Returns:
            bool: True if role updated successfully
        """
        pass
        
    @abstractmethod
    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get a user's gameplay statistics.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[UserStats]: User stats if found
        """
        pass
        
    @abstractmethod
    async def update_stats(self, user_id: int, game_stats: Dict) -> bool:
        """Update a user's statistics after a game.
        
        Args:
            user_id: ID of the user
            game_stats: Game statistics to add
            
        Returns:
            bool: True if stats updated successfully
        """
        pass
        
    @abstractmethod
    async def get_user_rank(self, user_id: int) -> Optional[UserRank]:
        """Get a user's ranking information.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Optional[UserRank]: User rank if found
        """
        pass
        
    @abstractmethod
    async def update_rank(self, user_id: int, points_delta: int) -> bool:
        """Update a user's rank points.
        
        Args:
            user_id: ID of the user
            points_delta: Points to add (positive) or subtract (negative)
            
        Returns:
            bool: True if rank updated successfully
        """
        pass
        
    @abstractmethod
    async def get_top_players(self, limit: int = 10) -> List[Dict]:
        """Get the top ranked players.
        
        Args:
            limit: Maximum number of players to return
            
        Returns:
            List[Dict]: List of top players with rank info
        """
        pass
        
    @abstractmethod
    async def verify_password(self, user_id: int, password: str) -> bool:
        """Verify a user's password.
        
        Args:
            user_id: ID of the user
            password: Password to verify
            
        Returns:
            bool: True if password is correct
        """
        pass
        
    @abstractmethod
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change a user's password.
        
        Args:
            user_id: ID of the user
            old_password: Current password
            new_password: New password
            
        Returns:
            bool: True if password changed successfully
        """
        pass
        
    @abstractmethod
    async def reset_password(self, email: str) -> bool:
        """Initiate password reset for a user.
        
        Args:
            email: User's email address
            
        Returns:
            bool: True if reset initiated successfully
        """
        pass
        
    @abstractmethod
    async def complete_reset(self, reset_token: str, new_password: str) -> bool:
        """Complete password reset with token.
        
        Args:
            reset_token: Password reset token
            new_password: New password
            
        Returns:
            bool: True if reset completed successfully
        """
        pass
