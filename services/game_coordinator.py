"""
Game coordinator service for the Myth metaserver.

This module implements the game coordinator interface, managing game sessions,
player coordination, and game state synchronization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from ..interfaces.game_coordinator_interface import (
    GameCoordinatorInterface,
    GameState,
    GameStatus,
    PlayerStatus
)
from ..services.game_service import game_service
from ..network.network_service import network_service

logger = logging.getLogger(__name__)

class GameCoordinator(GameCoordinatorInterface):
    """Service for coordinating game sessions."""
    
    def __init__(self):
        self.games: Dict[int, GameStatus] = {}
        self.players: Dict[int, Dict[int, PlayerStatus]] = {}  # game_id -> {user_id -> status}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the coordinator service."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Game coordinator started")
        
    async def stop(self) -> None:
        """Stop the coordinator service."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            
        logger.info("Game coordinator stopped")
        
    async def initialize_game(self, game_id: int, settings: Dict) -> bool:
        """Initialize a new game session."""
        if game_id in self.games:
            return False
            
        status = GameStatus(
            game_id=game_id,
            state=GameState.INITIALIZING,
            map_name=settings.get('map', 'unknown'),
            player_count=0,
            max_players=settings.get('max_players', 8),
            team_game=settings.get('team_game', False)
        )
        
        self.games[game_id] = status
        self.players[game_id] = {}
        
        logger.info(f"Initialized game {game_id}")
        return True
        
    async def add_player(self, game_id: int, user_id: int, team: Optional[int] = None) -> bool:
        """Add a player to a game."""
        if game_id not in self.games:
            return False
            
        game = self.games[game_id]
        if game.state not in (GameState.INITIALIZING, GameState.WAITING):
            return False
            
        if game.player_count >= game.max_players:
            return False
            
        if user_id in self.players[game_id]:
            return True  # Already in game
            
        status = PlayerStatus(
            user_id=user_id,
            team=team if game.team_game else None
        )
        
        self.players[game_id][user_id] = status
        game.player_count = len(self.players[game_id])
        
        if game.state == GameState.INITIALIZING:
            game.state = GameState.WAITING
            
        logger.info(f"Added player {user_id} to game {game_id}")
        return True
        
    async def remove_player(self, game_id: int, user_id: int) -> bool:
        """Remove a player from a game."""
        if game_id not in self.games or user_id not in self.players[game_id]:
            return False
            
        del self.players[game_id][user_id]
        self.games[game_id].player_count = len(self.players[game_id])
        
        # End game if no players left
        if not self.players[game_id]:
            await self.end_game(game_id, {})
            
        logger.info(f"Removed player {user_id} from game {game_id}")
        return True
        
    async def set_player_ready(self, game_id: int, user_id: int, ready: bool = True) -> bool:
        """Set a player's ready status."""
        if game_id not in self.games or user_id not in self.players[game_id]:
            return False
            
        self.players[game_id][user_id].ready = ready
        
        # Check if all players ready
        if ready:
            ready, reason = await self.check_game_ready(game_id)
            if ready:
                await self.start_game(game_id)
                
        logger.info(f"Player {user_id} {'ready' if ready else 'not ready'} in game {game_id}")
        return True
        
    async def set_player_team(self, game_id: int, user_id: int, team: int) -> bool:
        """Set a player's team."""
        if game_id not in self.games or user_id not in self.players[game_id]:
            return False
            
        game = self.games[game_id]
        if not game.team_game:
            return False
            
        self.players[game_id][user_id].team = team
        logger.info(f"Set player {user_id} to team {team} in game {game_id}")
        return True
        
    async def start_game(self, game_id: int) -> bool:
        """Start a game when all players are ready."""
        if game_id not in self.games:
            return False
            
        game = self.games[game_id]
        if game.state != GameState.WAITING:
            return False
            
        ready, reason = await self.check_game_ready(game_id)
        if not ready:
            logger.warning(f"Cannot start game {game_id}: {reason}")
            return False
            
        game.state = GameState.IN_PROGRESS
        game.start_time = datetime.now()
        
        # Notify all players
        for user_id in self.players[game_id]:
            await network_service.send_to_client(str(user_id), {
                "type": "game_start",
                "game_id": game_id,
                "start_time": game.start_time.isoformat()
            })
            
        logger.info(f"Started game {game_id}")
        return True
        
    async def end_game(self, game_id: int, scores: Dict[int, int]) -> bool:
        """End a game and record final scores."""
        if game_id not in self.games:
            return False
            
        game = self.games[game_id]
        if game.state not in (GameState.IN_PROGRESS, GameState.ENDING):
            return False
            
        game.state = GameState.COMPLETED
        game.end_time = datetime.now()
        
        # Record scores and notify players
        for user_id, score in scores.items():
            if user_id in self.players[game_id]:
                await network_service.send_to_client(str(user_id), {
                    "type": "game_end",
                    "game_id": game_id,
                    "score": score,
                    "end_time": game.end_time.isoformat()
                })
                
        # Cleanup game data
        del self.games[game_id]
        del self.players[game_id]
        
        logger.info(f"Ended game {game_id}")
        return True
        
    async def get_game_status(self, game_id: int) -> Optional[GameStatus]:
        """Get the current status of a game."""
        return self.games.get(game_id)
        
    async def get_player_status(self, game_id: int, user_id: int) -> Optional[PlayerStatus]:
        """Get a player's status in a game."""
        if game_id not in self.players:
            return None
        return self.players[game_id].get(user_id)
        
    async def get_all_players(self, game_id: int) -> Dict[int, PlayerStatus]:
        """Get all players in a game."""
        if game_id not in self.players:
            return {}
        return self.players[game_id].copy()
        
    async def update_player_activity(self, game_id: int, user_id: int) -> bool:
        """Update a player's last active timestamp."""
        if game_id not in self.players or user_id not in self.players[game_id]:
            return False
            
        self.players[game_id][user_id].last_active = datetime.now()
        return True
        
    async def check_game_ready(self, game_id: int) -> Tuple[bool, Optional[str]]:
        """Check if a game is ready to start."""
        if game_id not in self.games:
            return False, "Game not found"
            
        game = self.games[game_id]
        if game.state != GameState.WAITING:
            return False, f"Game in wrong state: {game.state}"
            
        if not self.players[game_id]:
            return False, "No players in game"
            
        # Check all players ready
        for status in self.players[game_id].values():
            if not status.ready:
                return False, f"Player {status.user_id} not ready"
                
        # Check teams balanced for team games
        if game.team_game:
            team_counts: Dict[int, int] = {}
            for status in self.players[game_id].values():
                if status.team is None:
                    return False, f"Player {status.user_id} not assigned to team"
                team_counts[status.team] = team_counts.get(status.team, 0) + 1
                
            if len(set(team_counts.values())) > 1:
                return False, "Teams not balanced"
                
        return True, None
        
    async def _cleanup_loop(self) -> None:
        """Periodically cleanup inactive games and players."""
        while True:
            try:
                now = datetime.now()
                
                # Check each game
                for game_id in list(self.games.keys()):
                    game = self.games[game_id]
                    
                    # End games that have been inactive too long
                    if game.state == GameState.IN_PROGRESS:
                        inactive_time = timedelta(minutes=30)
                        all_inactive = True
                        
                        for status in self.players[game_id].values():
                            if now - status.last_active < inactive_time:
                                all_inactive = False
                                break
                                
                        if all_inactive:
                            logger.warning(f"Ending inactive game {game_id}")
                            await self.end_game(game_id, {})
                            
                    # Clean up completed/aborted games after a while
                    elif game.state in (GameState.COMPLETED, GameState.ABORTED):
                        if now - game.end_time > timedelta(minutes=5):
                            del self.games[game_id]
                            del self.players[game_id]
                            
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in game cleanup: {e}")
                await asyncio.sleep(60)

# Global instance
game_coordinator = GameCoordinator()
