# Myth Metaserver Developer Guide

This guide covers technical details of the Python implementation of the Myth metaserver.

## Architecture Overview

### Core Components

1. **User Management (`users_new/`)**
   - User authentication and session handling
   - Account creation and management
   - Password encryption (MD5)
   - User database operations

2. **Room Management (`room_new/`)**
   - Room state management
   - Client connections
   - Game session coordination
   - Room-specific messaging

3. **Game Search (`game_search_new/`)**
   - Game listing and discovery
   - Game state tracking
   - Player matching

4. **Web Interface (`web_new/`)**
   - HTTP API endpoints
   - Admin commands
   - User management interface

### Data Structures

Key data structures are implemented as Python dataclasses:

```python
@dataclass
class Room:
    name: str
    room_id: int
    ranked: bool
    country: int
    min_caste: int
    max_caste: int
    tournament: bool
    clients: List[Client] = field(default_factory=list)
```

### Network Protocol

The server uses async sockets for network communication:

1. **Connection Flow**
   ```
   Client -> Server: Connection request
   Server -> Client: Challenge
   Client -> Server: Authentication
   Server -> Client: Session token
   ```

2. **Room Protocol**
   ```
   Client -> Room: Join request
   Room -> Client: Room state
   Client <-> Room: Game updates
   ```

## Implementation Details

### Async Architecture

```python
async def handle_client(reader: StreamReader, writer: StreamWriter):
    while True:
        try:
            data = await reader.read(1024)
            if not data:
                break
            
            packet = decode_packet(data)
            response = await process_packet(packet)
            writer.write(response)
            await writer.drain()
        except ConnectionError:
            break
```

### Database Operations

User data is stored in structured formats:

```python
@dataclass_json
@dataclass
class UserRecord:
    username: str
    password_hash: str
    caste: int
    last_login: datetime
    stats: Dict[str, Any]
```

### Security Measures

1. **Password Handling**
   ```python
   def hash_password(password: str) -> str:
       return hashlib.md5(password.encode()).hexdigest()
   ```

2. **Session Management**
   ```python
   def create_session(user: UserRecord) -> str:
       return jwt.encode({
           'user': user.username,
           'exp': datetime.now() + timedelta(hours=1)
       }, SECRET_KEY)
   ```

## Testing

### Unit Tests

```python
def test_room_creation():
    room = Room("Test Room", 0, False, 0, -1, 99, False)
    assert room.name == "Test Room"
    assert len(room.clients) == 0
```

### Integration Tests

```python
async def test_client_connection():
    server = await start_test_server()
    client = await connect_test_client()
    
    response = await client.authenticate("test", "password")
    assert response.status == AuthStatus.SUCCESS
```

## Error Handling

```python
class MythError(Exception):
    """Base class for Myth server errors"""
    pass

class AuthenticationError(MythError):
    """Raised when authentication fails"""
    pass

class RoomError(MythError):
    """Raised for room-related errors"""
    pass
```

## Performance Considerations

1. **Connection Pooling**
   - Reuse connections when possible
   - Limit maximum concurrent connections
   - Implement timeout handling

2. **Memory Management**
   - Clear inactive sessions
   - Remove disconnected clients
   - Cache frequently accessed data

3. **Load Balancing**
   - Distribute rooms across processes
   - Monitor room populations
   - Implement room migration

## Debugging

1. **Logging**
   ```python
   import structlog
   logger = structlog.get_logger()
   
   logger.info("client_connected",
               client_id=client.id,
               room=room.name)
   ```

2. **Metrics**
   ```python
   def collect_metrics():
       return {
           'active_users': len(active_users),
           'room_count': len(rooms),
           'memory_usage': get_memory_usage()
       }
   ```

## Common Tasks

### Adding a New Room Type

1. Create room class:
   ```python
   @dataclass
   class TournamentRoom(Room):
       prize_pool: int
       min_players: int
       start_time: datetime
   ```

2. Implement handlers:
   ```python
   async def handle_tournament_start(room: TournamentRoom):
       if len(room.clients) >= room.min_players:
           await start_tournament(room)
   ```

### Implementing New Commands

1. Define command:
   ```python
   @dataclass
   class CustomCommand:
       command_type: int
       payload: bytes
   ```

2. Add handler:
   ```python
   async def handle_custom_command(command: CustomCommand):
       # Process command
       return create_response(command)
   ```

## Deployment

### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```python
# config.py
class Config:
    MAX_CLIENTS = 100
    ROOM_TIMEOUT = 300  # seconds
    LOG_LEVEL = "INFO"
```

### Monitoring

1. Set up logging
2. Monitor system resources
3. Track connection counts
4. Watch for errors

## Troubleshooting

Common issues and solutions:

1. **Connection Timeouts**
   - Check network configuration
   - Verify client settings
   - Monitor server load

2. **Room State Issues**
   - Validate room configuration
   - Check client permissions
   - Review room logs

3. **Authentication Failures**
   - Verify user credentials
   - Check encryption settings
   - Review auth logs
