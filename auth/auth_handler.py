"""
Authentication message handler.

This module handles authentication-related network messages and maintains the
connection between network clients and authenticated users.
"""

import json
import logging
from typing import Dict, Optional, Tuple

from .auth_service import auth_service
from .session_manager import session_manager
from ..network.network_service import network_service

logger = logging.getLogger(__name__)

class AuthHandler:
    """Handles authentication-related network messages."""
    
    async def handle_auth_request(self, client_id: str, data: bytes) -> None:
        """Handle an authentication request from a client.
        
        Args:
            client_id: The network client ID
            data: The raw message data
        """
        try:
            # Parse auth request
            request = json.loads(data.decode())
            username = request.get("username")
            password = request.get("password")
            
            if not username or not password:
                await self._send_error(client_id, "Missing username or password")
                return
                
            # Authenticate user
            result = await auth_service.authenticate(username, password)
            
            if not result.success:
                await self._send_error(client_id, result.error_message or "Authentication failed")
                return
                
            # Create session
            if not await session_manager.create_session(result.token, client_id):
                await self._send_error(client_id, "Failed to create session")
                return
                
            # Send success response
            response = {
                "success": True,
                "token": result.token.token,
                "user_id": result.token.user_id,
                "expires_at": result.token.expires_at.isoformat()
            }
            await network_service.send_to_client(client_id, json.dumps(response))
            
        except json.JSONDecodeError:
            await self._send_error(client_id, "Invalid request format")
        except Exception as e:
            logger.error(f"Error handling auth request: {e}")
            await self._send_error(client_id, "Internal server error")
            
    async def handle_auth_check(self, client_id: str, data: bytes) -> None:
        """Handle a token validation request from a client.
        
        Args:
            client_id: The network client ID
            data: The raw message data
        """
        try:
            # Parse token check request
            request = json.loads(data.decode())
            token = request.get("token")
            
            if not token:
                await self._send_error(client_id, "Missing token")
                return
                
            # Validate token
            valid, user_id = await auth_service.validate_token(token)
            
            response = {
                "success": valid,
                "user_id": user_id if valid else None
            }
            await network_service.send_to_client(client_id, json.dumps(response))
            
        except json.JSONDecodeError:
            await self._send_error(client_id, "Invalid request format")
        except Exception as e:
            logger.error(f"Error handling token check: {e}")
            await self._send_error(client_id, "Internal server error")
            
    async def handle_password_change(self, client_id: str, data: bytes) -> None:
        """Handle a password change request from a client.
        
        Args:
            client_id: The network client ID
            data: The raw message data
        """
        try:
            # Get user ID from session
            user_id = session_manager.get_user_id(client_id)
            if user_id is None:
                await self._send_error(client_id, "Not authenticated")
                return
                
            # Parse password change request
            request = json.loads(data.decode())
            old_password = request.get("old_password")
            new_password = request.get("new_password")
            
            if not old_password or not new_password:
                await self._send_error(client_id, "Missing old or new password")
                return
                
            # Change password
            success = await auth_service.change_password(user_id, old_password, new_password)
            
            response = {
                "success": success,
                "error": None if success else "Failed to change password"
            }
            await network_service.send_to_client(client_id, json.dumps(response))
            
        except json.JSONDecodeError:
            await self._send_error(client_id, "Invalid request format")
        except Exception as e:
            logger.error(f"Error handling password change: {e}")
            await self._send_error(client_id, "Internal server error")
            
    async def _send_error(self, client_id: str, message: str) -> None:
        """Send an error response to a client.
        
        Args:
            client_id: The network client ID
            message: The error message
        """
        response = {
            "success": False,
            "error": message
        }
        await network_service.send_to_client(client_id, json.dumps(response))

# Global instance
auth_handler = AuthHandler()
