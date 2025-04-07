"""
Web interface for the redemption.net metaserver.

This module provides:
- Web interface for game server management
- Room and player management
- Server statistics
- Admin controls
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from ..room.games import GameManager, GameInfo, PlayerInfo
from ..room.games_log import GamesLogger
from ..room.remote_commands import RemoteCommandHandler, CommandRequest, CommandType

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Initialize components
game_manager = GameManager()
games_logger = GamesLogger()
command_handler = RemoteCommandHandler(game_manager, games_logger)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('webui')

class User(UserMixin):
    """User model for authentication."""
    def __init__(self, id: str, username: str, is_admin: bool = False):
        self.id = id
        self.username = username
        self.is_admin = is_admin

# Mock user database
users = {
    'admin': User('1', 'admin', True),
    'user': User('2', 'user', False)
}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Load user from database."""
    return users.get(user_id)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # TODO: Implement proper authentication
        if username in users and password == 'password':  # Change this in production
            user = users[username]
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard."""
    games = game_manager.get_all_games()
    stats = game_manager.get_server_stats()
    return render_template('dashboard.html', games=games, stats=stats)

@app.route('/api/games', methods=['GET'])
@login_required
def get_games():
    """Get all games."""
    games = game_manager.get_all_games()
    return jsonify([{
        'room_id': game.room_id,
        'name': game.name,
        'game_type': game.game_type.name,
        'status': game.status,
        'players': len(game.players),
        'spectators': len(game.spectators),
        'max_players': game.max_players,
        'created_at': game.created_at.isoformat()
    } for game in games])

@app.route('/api/games/<room_id>', methods=['GET'])
@login_required
def get_game(room_id: str):
    """Get game details."""
    game = game_manager.get_game(room_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    return jsonify({
        'room_id': game.room_id,
        'name': game.name,
        'game_type': game.game_type.name,
        'status': game.status,
        'players': [{
            'player_id': p.player_id,
            'name': p.name,
            'role': p.role.name,
            'team': p.team,
            'is_ready': p.is_ready
        } for p in game.players],
        'spectators': [{
            'player_id': s.player_id,
            'name': s.name
        } for s in game.spectators],
        'max_players': game.max_players,
        'created_at': game.created_at.isoformat(),
        'last_updated': game.last_updated.isoformat()
    })

@app.route('/api/games', methods=['POST'])
@login_required
def create_game():
    """Create a new game."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        request = CommandRequest(
            command_type=CommandType.CREATE_ROOM,
            parameters=data,
            timestamp=datetime.now(),
            source=request.remote_addr
        )
        
        response = command_handler.handle_command(request)
        if not response.success:
            return jsonify({'error': response.message}), 400
        
        return jsonify(response.data), 201
        
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/games/<room_id>', methods=['DELETE'])
@login_required
def delete_game(room_id: str):
    """Delete a game."""
    try:
        request = CommandRequest(
            command_type=CommandType.END_GAME,
            parameters={'room_id': room_id},
            timestamp=datetime.now(),
            source=request.remote_addr
        )
        
        response = command_handler.handle_command(request)
        if not response.success:
            return jsonify({'error': response.message}), 400
        
        return jsonify({'message': 'Game deleted'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting game: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get server statistics."""
    try:
        request = CommandRequest(
            command_type=CommandType.GET_SERVER_STATS,
            parameters={},
            timestamp=datetime.now(),
            source=request.remote_addr
        )
        
        response = command_handler.handle_command(request)
        if not response.success:
            return jsonify({'error': response.message}), 400
        
        return jsonify(response.data), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maintenance', methods=['POST'])
@login_required
def set_maintenance():
    """Set maintenance mode."""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data or 'enabled' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    try:
        request = CommandRequest(
            command_type=CommandType.MAINTENANCE,
            parameters={'enabled': data['enabled']},
            timestamp=datetime.now(),
            source=request.remote_addr,
            auth_token=session.get('auth_token')
        )
        
        response = command_handler.handle_command(request)
        if not response.success:
            return jsonify({'error': response.message}), 400
        
        return jsonify({'message': 'Maintenance mode updated'}), 200
        
    except Exception as e:
        logger.error(f"Error setting maintenance mode: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 