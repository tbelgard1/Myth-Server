"""
Authentication interface for Myth metaserver.

This module defines the interface that all authentication services must implement.
It provides a standard contract for user authentication and session management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

@dataclass
class AuthToken:
    """Authentication token for a user session"""
    token: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    
@dataclass
class AuthResult:
    """Result of an authentication attempt"""
    success: bool
    token: Optional[AuthToken] = None
    error_message: Optional[str] = None

class AuthInterface(ABC):
    """Interface for authentication services"""
    
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate a user with username and password
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            AuthResult containing success status and optional token/error
        """
        pass
        
    @abstractmethod
    async def validate_token(self, token: str) -> Tuple[bool, Optional[int]]:
        """Validate an authentication token
        
        Args:
            token: Authentication token to validate
            
        Returns:
            Tuple of (is_valid, user_id). If token is invalid, user_id will be None
        """
        pass
        
    @abstractmethod
    async def invalidate_token(self, token: str) -> bool:
        """Invalidate an authentication token
        
        Args:
            token: Authentication token to invalidate
            
        Returns:
            True if token was invalidated successfully
        """
        pass
        
    @abstractmethod
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change a user's password
        
        Args:
            user_id: ID of user changing password
            old_password: User's current password
            new_password: User's new password
            
        Returns:
            True if password was changed successfully
        """
        pass
        
    @abstractmethod
    async def create_user(self, username: str, password: str) -> Tuple[bool, Optional[int]]:
        """Create a new user
        
        Args:
            username: Username for new user
            password: Password for new user
            
        Returns:
            Tuple of (success, user_id). If creation fails, user_id will be None
        """
        pass
        
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if user was deleted successfully
        """
        pass
        
    @abstractmethod
    async def get_user_id(self, username: str) -> Optional[int]:
        """Get a user's ID from their username
        
        Args:
            username: Username to look up
            
        Returns:
            User ID if found, None if not found
        """
        pass
