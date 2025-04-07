"""
Database configuration for the Myth metaserver.

This module handles database connection configuration and provides the database
engine and session management.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/myth"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    pool_size=20,
    max_overflow=10
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session.
    
    Usage:
        async with get_session() as session:
            # Use session here
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
