"""
Authentication service implementation for Myth metaserver.

This module implements the authentication interface using bcrypt/Argon2 for
password hashing and secure token-based session management.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from ..interfaces.auth_interface import (
    AuthInterface,
    AuthToken,
    AuthResult
)
from .auth import (
    AuthenticationToken,
    EncryptionType,
    encrypt_password,
    get_random_salt,
    passwords_match
)
from ..models.player import BungieNetPlayerDatum

logger = logging.getLogger(__name__)

class AuthService(AuthInterface):
    """Authentication service implementation"""
    
    def __init__(self):
        self.active_tokens: Dict[str, AuthToken] = {}
        self.encryption_type = EncryptionType.BCRYPT  # Use bcrypt by default
        
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate a user with username and password"""
        # Get user ID from username
        user_id = await self.get_user_id(username)
        if user_id is None:
            return AuthResult(
                success=False,
                error_message="Invalid username or password"
            )
            
        # Get user data
        user = BungieNetPlayerDatum.get_by_id(user_id)
        if user is None:
            return AuthResult(
                success=False,
                error_message="User data not found"
            )
            
        # Check password
        if not passwords_match(password, user.password, user.salt, self.encryption_type):
            return AuthResult(
                success=False,
                error_message="Invalid username or password"
            )
            
        # Generate token
        token_str = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=2)
        
        token = AuthToken(
            token=token_str,
            user_id=user_id,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        # Store token
        self.active_tokens[token_str] = token
        
        return AuthResult(success=True, token=token)
        
    async def validate_token(self, token: str) -> Tuple[bool, Optional[int]]:
        """Validate an authentication token"""
        auth_token = self.active_tokens.get(token)
        if auth_token is None:
            return False, None
            
        # Check expiration
        if datetime.now() > auth_token.expires_at:
            await self.invalidate_token(token)
            return False, None
            
        return True, auth_token.user_id
        
    async def invalidate_token(self, token: str) -> bool:
        """Invalidate an authentication token"""
        if token in self.active_tokens:
            del self.active_tokens[token]
            return True
        return False
        
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change a user's password"""
        # Get user data
        user = BungieNetPlayerDatum.get_by_id(user_id)
        if user is None:
            return False
            
        # Verify old password
        if not passwords_match(old_password, user.password, user.salt, self.encryption_type):
            return False
            
        # Generate new salt and hash new password
        new_salt = get_random_salt()
        new_hash = encrypt_password(new_password, new_salt, self.encryption_type)
        
        # Update user data
        user.password = new_hash
        user.salt = new_salt
        user.save()
        
        # Invalidate all tokens for this user
        for token_str, token in list(self.active_tokens.items()):
            if token.user_id == user_id:
                await self.invalidate_token(token_str)
                
        return True
        
    async def create_user(self, username: str, password: str) -> Tuple[bool, Optional[int]]:
        """Create a new user"""
        # Check if username exists
        if await self.get_user_id(username) is not None:
            return False, None
            
        # Generate salt and hash password
        salt = get_random_salt()
        password_hash = encrypt_password(password, salt, self.encryption_type)
        
        # Create user
        user = BungieNetPlayerDatum()
        user.username = username
        user.password = password_hash
        user.salt = salt
        user.save()
        
        return True, user.id
        
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        user = BungieNetPlayerDatum.get_by_id(user_id)
        if user is None:
            return False
            
        # Invalidate all tokens for this user
        for token_str, token in list(self.active_tokens.items()):
            if token.user_id == user_id:
                await self.invalidate_token(token_str)
                
        # Delete user
        user.delete()
        return True
        
    async def get_user_id(self, username: str) -> Optional[int]:
        """Get a user's ID from their username"""
        user = BungieNetPlayerDatum.get_by_username(username)
        if user is not None:
            return user.id
        return None

# Global instance
auth_service = AuthService()
