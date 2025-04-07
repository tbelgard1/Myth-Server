# Changelog

## [2.0.0] - 2025-04-06
### Major Changes
- Complete conversion from C to Python
- Modernized entire codebase architecture

### Added
- Type hints throughout the codebase
- Async/await pattern for network operations
- Dataclasses for structured data
- Modern Python packaging setup
- Comprehensive test suite
- Development tools integration (black, mypy, flake8)

### Changed
- Replaced C structs with Python dataclasses
- Converted all network code to use Python's asyncio
- Modernized authentication system
- Improved error handling with Python exceptions
- Enhanced logging with structlog
- Updated configuration management

### Removed
- All C source files and headers
- Make-based build system
- C-specific memory management
- Legacy shell scripts
- Outdated build configurations

### Security
- Updated password hashing
- Improved session management
- Enhanced input validation
- Modern cryptography implementation

### Developer Experience
- Added comprehensive documentation
- Improved code organization
- Added type checking
- Enhanced debugging capabilities

## [1.0.0] - 2002-01-23
- Initial release of C-based Myth metaserver

## File Conversions

### Common Directory
- ✅ `caste.h` → Integrated into Python classes
- ✅ `room_list_file.c/h` → `room_list_file.py`
- ✅ `metaserver_common_structs.h` → Python dataclasses

### Game Search Directory
- ✅ `game_search_server.c` → `game_search_server.py`
- ✅ `games_list.c/h` → `games_list.py`

### Room Directory
- ✅ `games.c/h` → `games.py`
- ✅ `games_log.c/h` → `games_log.py`
- ✅ `remote_commands.c/h` → `remote_commands.py`
- ✅ `roomd_new.c` → `roomd_new.py`
- ✅ `server_code.c/h` → `server_code.py`

### Users Directory
- ✅ `bungie_net_order.h` → Python dataclasses
- ✅ `bungie_net_player.h` → Python dataclasses
- ✅ `game_evaluator.c` → `game_evaluator.py`
- ✅ `main.c` → `main.py`
- ✅ `orders.c/h` → `orders.py`
- ✅ `rank.c/h` → `rank.py`
- ✅ `users.c/h` → `users.py`

### Utils Directory
- ✅ `environment.c/h` → `environment.py`

### Web Directory
- ✅ `webd_new.c` → `webd_new.py`

## Modernization Details

### Network Layer
- Replaced socket code with asyncio
- Added proper connection handling
- Improved error recovery
- Enhanced protocol implementation

### Data Structures
- Converted C structs to dataclasses
- Added type hints
- Improved data validation
- Enhanced serialization

### Authentication
- Modern password hashing
- Secure session management
- Enhanced user validation
- Improved token handling

### Configuration
- Environment-based config
- Enhanced room configuration
- Improved server settings
- Better defaults

### Testing
- Added unit tests
- Added integration tests
- Added test coverage
- Improved test documentation

### Documentation
- Added API documentation
- Improved code comments
- Added development guide
- Updated setup instructions
