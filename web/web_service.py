"""
Web service for the Myth metaserver.
Provides web interface for monitoring and managing the server.
"""

import asyncio
import logging
from aiohttp import web
import aiohttp_jinja2
import jinja2
from pathlib import Path
from typing import Dict, List

from ..models.game import GameManager
from ..models.room import RoomInfo
from ..services.room_service import RoomService
from ..services.game_search_service import GameSearchService

logger = logging.getLogger(__name__)

class WebService:
    """Web interface service"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.setup_jinja()
        
        # Services
        self.room_service = RoomService()
        self.game_service = GameSearchService()
        self.game_manager = GameManager()

    def setup_routes(self):
        """Set up web routes"""
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/rooms', self.handle_rooms)
        self.app.router.add_get('/games', self.handle_games)
        self.app.router.add_get('/stats', self.handle_stats)
        
    def setup_jinja(self):
        """Set up Jinja2 templating"""
        template_path = Path(__file__).parent / 'templates'
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader(str(template_path))
        )

    async def start(self):
        """Start the web service"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f'Web interface running at http://{self.host}:{self.port}')

    @aiohttp_jinja2.template('index.html')
    async def handle_index(self, request):
        """Handle index page"""
        return {
            'room_count': len(self.room_service.rooms),
            'game_count': len(self.game_manager.games),
            'uptime': 0  # TODO: Add uptime tracking
        }

    @aiohttp_jinja2.template('rooms.html')
    async def handle_rooms(self, request):
        """Handle rooms page"""
        rooms = self.room_service.list_rooms()
        return {'rooms': rooms}

    @aiohttp_jinja2.template('games.html')
    async def handle_games(self, request):
        """Handle games page"""
        games = self.game_manager.list_games()
        return {'games': games}

    @aiohttp_jinja2.template('stats.html')
    async def handle_stats(self, request):
        """Handle stats page"""
        return {
            'stats': {
                'rooms': len(self.room_service.rooms),
                'games': len(self.game_manager.games),
                'players': 0  # TODO: Add player tracking
            }
        }
