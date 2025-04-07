"""
Part of the Bungie.net Myth2 Metaserver source code
Copyright (c) 1997-2002 Bungie Studios
Refer to the file "License.txt" for details

Converted to Python by Codeium
"""

import os
from dataclasses import dataclass
from typing import Optional

# Configuration flag
HARDCODE_USERD_SETTINGS = True
RUNNING_LOCALLY = True
BN2_DEMOVERSION = False

@dataclass
class EnvironmentConfig:
    """Environment configuration"""
    METASERVER_ROOT_DIR: str = "./"
    MOTD_FILE_NAME: str = ""
    USERD_HOST: str = ""
    USERD_PORT: str = ""
    USERD_ROOM_PORT: str = ""
    USERD_WEB_PORT: str = ""
    DB_DIRECTORY: str = ""
    ORDERS_DB_FILE_NAME: str = ""
    USERS_DB_FILE_NAME: str = ""
    LOG_DIRECTORY: str = ""
    ROOMS_LIST_FILE: str = ""
    ADMIN_LOG_FILE_NAME: str = ""
    GAMES_LOG_FILE: str = ""
    GUEST_ACCOUNT_NAME: str = "guest"

    def __post_init__(self):
        """Initialize paths based on root directory"""
        self.MOTD_FILE_NAME = os.path.join(self.METASERVER_ROOT_DIR, "motd")
        self.DB_DIRECTORY = os.path.join(self.METASERVER_ROOT_DIR, "db/")
        self.LOG_DIRECTORY = os.path.join(self.METASERVER_ROOT_DIR, "log/")
        self.ROOMS_LIST_FILE = os.path.join(self.METASERVER_ROOT_DIR, "rooms.lst")
        self.ORDERS_DB_FILE_NAME = os.path.join(self.DB_DIRECTORY, "orders.dat")
        self.USERS_DB_FILE_NAME = os.path.join(self.DB_DIRECTORY, "users.dat")
        self.ADMIN_LOG_FILE_NAME = os.path.join(self.LOG_DIRECTORY, "adminlog.txt")
        self.GAMES_LOG_FILE = os.path.join(self.LOG_DIRECTORY, "games_log")

        # Set host and ports based on configuration
        if RUNNING_LOCALLY:
            self.USERD_HOST = "127.0.0.1"
        else:
            self.USERD_HOST = "65.94.230.234"  # Replace with your static IP

        if BN2_DEMOVERSION:
            self.USERD_PORT = "6321"
            self.USERD_ROOM_PORT = "6333"
            self.USERD_WEB_PORT = "6332"
        else:
            self.USERD_PORT = "6321"
            self.USERD_ROOM_PORT = "6323"
            self.USERD_WEB_PORT = "6322"

# Global configuration instance
config = EnvironmentConfig()

def bnet_getenv(var: str) -> str:
    """Get environment variable with empty string as default"""
    return os.getenv(var, "")

if not HARDCODE_USERD_SETTINGS:
    # If not hardcoded, get settings from environment variables
    config.METASERVER_ROOT_DIR = bnet_getenv("METASERVER_ROOT_DIR")
    config.MOTD_FILE_NAME = bnet_getenv("MOTD_FILE_NAME")
    config.USERD_HOST = bnet_getenv("USERD_HOST")
    config.USERD_PORT = bnet_getenv("USERD_PORT")
    config.USERD_ROOM_PORT = bnet_getenv("USERD_ROOM_PORT")
    config.USERD_WEB_PORT = bnet_getenv("USERD_WEB_PORT")
    config.DB_DIRECTORY = bnet_getenv("DB_DIRECTORY")
    config.ORDERS_DB_FILE_NAME = bnet_getenv("ORDERS_DB_FILE_NAME")
    config.USERS_DB_FILE_NAME = bnet_getenv("USERS_DB_FILE_NAME")
    config.LOG_DIRECTORY = bnet_getenv("LOG_DIRECTORY")
    config.ROOMS_LIST_FILE = bnet_getenv("ROOMS_LIST_FILE")
    config.ADMIN_LOG_FILE_NAME = bnet_getenv("ADMIN_LOG_FILE_NAME")

# Getter functions for compatibility with C code
def get_metaserver_root_dir() -> str:
    """Get metaserver root directory"""
    return config.METASERVER_ROOT_DIR

def get_motd_file_name() -> str:
    """Get MOTD file name"""
    return config.MOTD_FILE_NAME

def get_userd_host() -> str:
    """Get user daemon host"""
    return config.USERD_HOST

def get_userd_port() -> str:
    """Get user daemon port"""
    return config.USERD_PORT

def get_userd_room_port() -> str:
    """Get user daemon room port"""
    return config.USERD_ROOM_PORT

def get_userd_web_port() -> str:
    """Get user daemon web port"""
    return config.USERD_WEB_PORT

def get_db_directory() -> str:
    """Get database directory"""
    return config.DB_DIRECTORY

def get_orders_db_file_name() -> str:
    """Get orders database file name"""
    return config.ORDERS_DB_FILE_NAME

def get_users_db_file_name() -> str:
    """Get users database file name"""
    return config.USERS_DB_FILE_NAME

def get_log_directory() -> str:
    """Get log directory"""
    return config.LOG_DIRECTORY

def get_rooms_list_file() -> str:
    """Get rooms list file"""
    return config.ROOMS_LIST_FILE

def get_admin_log_file_name() -> str:
    """Get admin log file name"""
    return config.ADMIN_LOG_FILE_NAME

def ensure_directories_exist() -> None:
    """Create required directories if they don't exist"""
    dirs = [
        config.METASERVER_ROOT_DIR,
        config.DB_DIRECTORY,
        config.LOG_DIRECTORY
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
