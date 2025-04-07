# Testing Guide

## Overview
This guide covers the testing strategy and implementation for the Myth metaserver.

## Test Types

### Unit Tests
- Function-level testing
- Class-level testing
- Module-level testing
- Service-level testing
- Utility testing

### Integration Tests
- Service integration
- API endpoints
- Network protocols
- Game mechanics
- State management

### Performance Tests
- Load testing
- Stress testing
- Latency testing
- Resource testing
- Scalability testing

## Test Framework

### Setup
```python
# conftest.py
import pytest
import asyncio
from typing import AsyncGenerator

@pytest.fixture
async def game_service():
    service = GameService()
    await service.start()
    yield service
    await service.stop()

@pytest.fixture
async def room_service():
    service = RoomService()
    await service.start()
    yield service
    await service.stop()
```

### Test Structure
```python
# test_game_service.py
import pytest
from core.services import GameService

async def test_game_creation(game_service):
    game = await game_service.create_game()
    assert game is not None
    assert game.id is not None

async def test_game_join(game_service):
    game = await game_service.create_game()
    player = await game_service.join_game(game.id)
    assert player in game.players
```

### Mock Objects
```python
# test_utils.py
class MockResponse:
    def __init__(self, data, status=200):
        self.data = data
        self.status = status

    async def json(self):
        return self.data

class MockClient:
    def __init__(self, responses=None):
        self.responses = responses or {}

    async def get(self, url):
        return self.responses.get(url, 
            MockResponse({"error": "Not found"}, 404))
```

## Test Coverage

### Core Components
- Network handling
- Security features
- Data models
- Service layer
- API endpoints

### Game Features
- Game creation
- Player joining
- State updates
- Room management
- Player stats

### Error Handling
- Network errors
- Protocol errors
- State errors
- Resource errors
- Security errors

## Running Tests

### Command Line
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_game_service.py

# Run tests with coverage
pytest --cov=core

# Run tests in parallel
pytest -n auto
```

### Configuration
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
addopts = --verbose --cov=core --cov-report=term-missing
```

## Test Utilities

### Async Helpers
```python
async def wait_for_condition(condition, timeout=5.0):
    """Wait for a condition to be true."""
    start = time.time()
    while not condition():
        if time.time() - start > timeout:
            raise TimeoutError()
        await asyncio.sleep(0.1)

async def async_collect(async_gen, count):
    """Collect items from an async generator."""
    items = []
    async for item in async_gen:
        items.append(item)
        if len(items) >= count:
            break
    return items
```

### Test Data
```python
# test_data.py
TEST_USERS = [
    {"id": 1, "name": "player1"},
    {"id": 2, "name": "player2"},
]

TEST_GAMES = [
    {"id": 1, "name": "game1", "players": []},
    {"id": 2, "name": "game2", "players": []},
]
```

## Best Practices

### Test Writing
- One assertion per test
- Clear test names
- Proper setup/teardown
- Isolated tests
- Comprehensive coverage

### Async Testing
- Use async fixtures
- Handle cleanup properly
- Test timeouts
- Error scenarios
- Resource cleanup

### Mock Usage
- Mock external services
- Mock time-dependent code
- Mock resource-heavy operations
- Mock network calls
- Mock random behavior

## Continuous Integration

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: pytest
```

### Coverage Reports
- Generate HTML reports
- Track coverage trends
- Set minimum coverage
- Report per component
- Identify gaps

## Maintenance

### Regular Tasks
- Update test data
- Review coverage
- Clean up tests
- Update mocks
- Verify CI pipeline

### Documentation
- Test documentation
- Coverage reports
- Setup instructions
- Best practices
- Known issues
