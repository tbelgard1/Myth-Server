# Myth Metaserver (Python Implementation)

A modern Python implementation of the Bungie.net Myth2 Metaserver. This version has been fully converted from the original C codebase to Python, making it more maintainable and easier to extend.

## Features

- Full Python implementation of the Myth metaserver
- Support for multiple game rooms
- User authentication and management
- Game search functionality
- Modern async networking using Python's asyncio
- Type hints and dataclass-based data structures
- Comprehensive test coverage

## Requirements

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Room Configuration
Rooms are configured in `rooms.lst` with the following format:
```
GAME_TYPE ROOM_ID RANKED COUNTRY MIN_CASTE MAX_CASTE TOURNAMENT
```

Example:
```
MYTH 0 0 0 -1 99 0
MYTH1|MYTH2 1 0 0 -1 99 0
```

Where:
- GAME_TYPE: Game clients allowed (MYTH1, MYTH2, MYTH3, MYTH, MARATHON, JCHAT)
- ROOM_ID: Unique identifier (0-based)
- RANKED: 0 for unranked, 1 for ranked
- COUNTRY: Country code (legacy)
- MIN_CASTE/MAX_CASTE: Player rank requirements
- TOURNAMENT: 0 for normal room, 1 for tournament

### Server Configuration
Server settings are managed through environment variables or `.env` file:
- USERD_HOST: Server IP address
- METASERVER_ROOT_DIR: Root directory path
- Additional settings in `utils/environment.py`

## Running the Server

Use the `myth_server.py` script to manage server components:

```bash
# Start all server components
python myth_server.py start

# Stop all server components
python myth_server.py stop
```

## Client Configuration

### Myth II Configuration
1. Open Fear and locate "internal metaserver strings"
2. Set the 12th string (after "Unmute") to your server's IP/domain
3. For Myth II 1.5+:
   - Create a plugin patch file
   - Use Server Switcher with the plugin in "metaservers" directory

## Development

### Tools and Standards
- Type checking: mypy
- Code formatting: black
- Testing: pytest
- Linting: flake8

### Project Structure
```
myth/
├── common/           # Shared utilities and structures
├── game_search_new/ # Game search functionality
├── room_new/        # Room management
├── users_new/       # User management
├── utils/           # Utility functions
└── web_new/         # Web interface
```

## Improvements Over C Version

1. **Modern Architecture**
   - Async I/O for better performance
   - Type safety with Python type hints
   - Dataclasses for structured data

2. **Security**
   - Modern cryptography support
   - Secure password handling
   - Input validation

3. **Maintainability**
   - Clear module structure
   - Comprehensive documentation
   - Type hints for better IDE support

4. **Testing**
   - Unit test framework
   - Coverage reporting
   - Automated testing support

## License

This project is licensed under the Microsoft Broad Source License - see LICENSE.txt for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (`pytest`)
5. Submit a pull request
