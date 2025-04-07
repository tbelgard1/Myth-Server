# Database Design Document

## Overview
The Myth metaserver will use PostgreSQL as the primary database, with SQLAlchemy as the ORM layer. This provides robust ACID compliance, JSON support, and excellent async capabilities.

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    caste INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    metadata JSONB
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_caste ON users(caste);
```

### Rooms Table
```sql
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    room_type VARCHAR(20) NOT NULL,
    max_players INT NOT NULL DEFAULT 32,
    min_caste INT NOT NULL DEFAULT -1,
    max_caste INT NOT NULL DEFAULT 99,
    is_ranked BOOLEAN DEFAULT false,
    is_tournament BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_rooms_type ON rooms(room_type);
```

### Games Table
```sql
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    room_id INT REFERENCES rooms(id),
    game_type VARCHAR(20) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    player_count INT NOT NULL DEFAULT 0,
    game_state JSONB,
    metadata JSONB,
    CONSTRAINT fk_room
        FOREIGN KEY(room_id)
        REFERENCES rooms(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_games_room ON games(room_id);
CREATE INDEX idx_games_type ON games(game_type);
```

### Player Stats Table
```sql
CREATE TABLE player_stats (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    game_id INT REFERENCES games(id),
    score INT NOT NULL DEFAULT 0,
    kills INT NOT NULL DEFAULT 0,
    deaths INT NOT NULL DEFAULT 0,
    assists INT NOT NULL DEFAULT 0,
    played_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_game
        FOREIGN KEY(game_id)
        REFERENCES games(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_stats_user ON player_stats(user_id);
CREATE INDEX idx_stats_game ON player_stats(game_id);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    session_token VARCHAR(256) NOT NULL,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_user ON sessions(user_id);
```

## SQLAlchemy Models

```python
# core/models/base.py
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# core/models/user.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from .base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    caste = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    metadata = Column(JSON)
```

## Database Service Layer

```python
# core/database/service.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

class DatabaseService:
    def __init__(self, connection_url: str):
        self.engine = create_async_engine(
            connection_url,
            echo=True,
            pool_size=20,
            max_overflow=10
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session
```

## Repository Pattern

```python
# core/repositories/base.py
from typing import Generic, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from core.models.base import Base

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get(self, id: int) -> T:
        return await self.session.get(self.model, id)
    
    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        return instance
```

## Migration System

Using Alembic for database migrations:

```python
# alembic/env.py
from alembic import context
from core.models.base import Base

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Configuration code...
```

## Connection Management

```python
# core/config/database.py
from pydantic import BaseSettings

class DatabaseSettings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "myth"
    DB_PASSWORD: str
    DB_NAME: str = "myth_db"
    
    @property
    def connection_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
```

## Data Migration Strategy

1. **Phase 1: Schema Creation**
   - Create initial tables
   - Set up indexes
   - Configure constraints

2. **Phase 2: Data Migration**
   - Migrate user data
   - Transfer room configurations
   - Import game history

3. **Phase 3: Validation**
   - Verify data integrity
   - Check relationships
   - Validate constraints

## Backup Strategy

1. **Regular Backups**
   ```bash
   pg_dump -Fc myth_db > backup_$(date +%Y%m%d).dump
   ```

2. **Point-in-Time Recovery**
   - Enable WAL archiving
   - Configure retention policy

## Performance Considerations

1. **Indexing Strategy**
   - B-tree indexes for equality/range queries
   - GiST indexes for spatial data
   - Hash indexes for exact matches

2. **Connection Pooling**
   - Use pgBouncer
   - Configure pool sizes

3. **Query Optimization**
   - Use EXPLAIN ANALYZE
   - Regular VACUUM
   - Monitor slow queries
