"""
Test utilities and helper functions.
"""

import asyncio
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar('T')

async def async_test_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float = 5.0
) -> T:
    """Run an async test with a timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Test timed out after {timeout} seconds")

def async_test(timeout: float = 5.0) -> Callable:
    """Decorator for async test functions."""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            return await async_test_with_timeout(
                func(*args, **kwargs),
                timeout=timeout
            )
        return wrapper
    return decorator

class AsyncContextManager:
    """Helper for async context management in tests."""
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def mock_coro(return_value: Any = None) -> Coroutine:
    """Create a coroutine mock."""
    async def mock_coro_func(*args, **kwargs):
        return return_value
    return mock_coro_func()

class MockResponse:
    """Mock HTTP response for testing."""
    def __init__(self, status: int = 200, data: Any = None):
        self.status = status
        self.data = data or {}

    async def json(self) -> Any:
        return self.data

    async def text(self) -> str:
        return str(self.data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
