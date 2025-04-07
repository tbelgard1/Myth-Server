"""
Environment configuration for the Myth metaserver.
"""

import os
from typing import Dict, Optional

class Environment:
    """Environment configuration."""
    
    _instance: Optional['Environment'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'Environment':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._config: Dict[str, str] = {}
            self._load_config()
            self._initialized = True
    
    def _load_config(self):
        """Load configuration from environment variables."""
        # Server settings
        self._config['HOST'] = os.getenv('MYTH_HOST', '0.0.0.0')
        self._config['PORT'] = os.getenv('MYTH_PORT', '8080')
        self._config['DEBUG'] = os.getenv('MYTH_DEBUG', 'false').lower() == 'true'
        
        # Monitoring settings
        self._config['METRICS_INTERVAL'] = os.getenv('MYTH_METRICS_INTERVAL', '5')
        self._config['LOG_LEVEL'] = os.getenv('MYTH_LOG_LEVEL', 'INFO')
        
        # Game settings
        self._config['MAX_PLAYERS'] = os.getenv('MYTH_MAX_PLAYERS', '16')
        self._config['MAX_GAMES'] = os.getenv('MYTH_MAX_GAMES', '100')
        self._config['GAME_TIMEOUT'] = os.getenv('MYTH_GAME_TIMEOUT', '3600')
    
    def get(self, key: str, default: str = '') -> str:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: str):
        """Set a configuration value."""
        self._config[key] = value
