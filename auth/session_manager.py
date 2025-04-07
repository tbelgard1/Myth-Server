"""
Session management for authenticated users.

This module handles user session tracking, token management, and session cleanup.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from .auth_service import auth_service
from ..interfaces.auth_interface import AuthToken
from ..network.network_service import network_service

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions and their associated network connections."""
    
    def __init__(self):
        self.user_sessions: Dict[int, Set[str]] = {}  # user_id -> set of client_ids
        self.client_sessions: Dict[str, int] = {}  # client_id -> user_id
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the session manager."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session manager started")
        
    async def stop(self) -> None:
        """Stop the session manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            
        # Cleanup all sessions
        for client_id in list(self.client_sessions.keys()):
            await self.end_session(client_id)
            
        logger.info("Session manager stopped")
        
    async def create_session(self, token: AuthToken, client_id: str) -> bool:
        """Create a new session for a user.
        
        Args:
            token: The authentication token
            client_id: The network client ID
            
        Returns:
            bool: True if session created successfully
        """
        # Validate token
        valid, user_id = await auth_service.validate_token(token.token)
        if not valid or user_id is None:
            return False
            
        # Add session mappings
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(client_id)
        self.client_sessions[client_id] = user_id
        
        logger.info(f"Created session for user {user_id} with client {client_id}")
        return True
        
    async def end_session(self, client_id: str) -> None:
        """End a client session.
        
        Args:
            client_id: The network client ID
        """
        user_id = self.client_sessions.get(client_id)
        if user_id is not None:
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(client_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
                    
            del self.client_sessions[client_id]
            logger.info(f"Ended session for user {user_id} with client {client_id}")
            
    def get_user_id(self, client_id: str) -> Optional[int]:
        """Get the user ID associated with a client.
        
        Args:
            client_id: The network client ID
            
        Returns:
            Optional[int]: The user ID if found
        """
        return self.client_sessions.get(client_id)
        
    def get_client_ids(self, user_id: int) -> Set[str]:
        """Get all client IDs for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Set[str]: Set of client IDs
        """
        return self.user_sessions.get(user_id, set())
        
    async def _cleanup_loop(self) -> None:
        """Periodically cleanup expired sessions."""
        while True:
            try:
                # Get connected clients
                connected_clients = await network_service.get_connected_clients()
                
                # Find disconnected clients
                for client_id in list(self.client_sessions.keys()):
                    if client_id not in connected_clients:
                        await self.end_session(client_id)
                        
                # Sleep for 60 seconds
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)  # Sleep on error

# Global instance
session_manager = SessionManager()
