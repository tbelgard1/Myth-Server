"""
Message types and codes for metaserver communication.

Defines error codes, message types and their corresponding string messages
for server-client communication.
"""

import enum

class MetaserverMessageType(enum.IntEnum):
    """Types of metaserver messages"""
    SYNTAX_ERROR = 0
    LOGIN_FAILED_GAMES_NOT_ALLOWED = 1
    LOGIN_FAILED_INVALID_VERSION = 2
    LOGIN_FAILED_BAD_USER_OR_PASSWORD = 3
    USER_NOT_LOGGED_IN = 4
    BAD_METASERVER_VERSION = 5
    USER_ALREADY_LOGGED_IN = 6
    UNKNOWN_GAME_TYPE = 7
    LOGIN_SUCCESSFUL = 8
    LOGOUT_SUCCESSFUL = 9
    PLAYER_NOT_IN_ROOM = 10
    GAME_ALREADY_EXISTS = 11
    ACCOUNT_ALREADY_LOGGED_IN = 12
    ROOM_FULL = 13
    ACCOUNT_LOCKED = 14
    METASERVER_NOT_SUPPORTED = 15

# Version constants
METASERVER_MAJOR_VERSION = 1

# Message strings
MESSAGES = {
    MetaserverMessageType.SYNTAX_ERROR: "Syntax error (unrecognized command).",
    MetaserverMessageType.LOGIN_FAILED_GAMES_NOT_ALLOWED: "Login failed (Games not allowed at this time).",
    MetaserverMessageType.LOGIN_FAILED_INVALID_VERSION: "Login failed (Invalid Game Version number).",
    MetaserverMessageType.LOGIN_FAILED_BAD_USER_OR_PASSWORD: "Login failed (Bad user or Password).",
    MetaserverMessageType.USER_NOT_LOGGED_IN: "User not logged in.",
    MetaserverMessageType.BAD_METASERVER_VERSION: "Bad metaserver version.",
    MetaserverMessageType.USER_ALREADY_LOGGED_IN: "User already logged in!",
    MetaserverMessageType.UNKNOWN_GAME_TYPE: "Unknown game type!",
    MetaserverMessageType.LOGIN_SUCCESSFUL: "User logged in.",
    MetaserverMessageType.LOGOUT_SUCCESSFUL: "User logged out.",
    MetaserverMessageType.PLAYER_NOT_IN_ROOM: "Player not in a room!",
    MetaserverMessageType.GAME_ALREADY_EXISTS: "You already created a game!",
    MetaserverMessageType.ACCOUNT_ALREADY_LOGGED_IN: "This account is already logged in!",
    MetaserverMessageType.ROOM_FULL: "The desired room is full!",
    MetaserverMessageType.ACCOUNT_LOCKED: "Your account has been locked",
    MetaserverMessageType.METASERVER_NOT_SUPPORTED: "The game server for your product has been shutdown"
}

def get_message(message_type: MetaserverMessageType) -> str:
    """Get message string for message type"""
    return MESSAGES.get(message_type, "Unknown message type")
