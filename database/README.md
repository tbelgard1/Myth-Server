# Database Setup Guide

## Prerequisites

1. Install PostgreSQL 13 or higher
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Initial Setup

1. Start PostgreSQL service:
   ```bash
   # Windows
   net start postgresql

   # Linux/Mac
   sudo service postgresql start
   ```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update database credentials if needed

3. Initialize database:
   ```bash
   python scripts/init_db.py
   ```

## Database Structure

The database uses SQLAlchemy for ORM and Alembic for migrations. Key components:

- `config.py`: Database configuration and connection management
- `models/`: SQLAlchemy models
- `migrations/`: Alembic migration scripts

## Connection Management

The database module provides async connection management:

```python
from core.database.config import get_session

async with get_session() as session:
    # Use session here
    result = await session.execute(query)
```

## Environment Variables

- `DATABASE_URL`: Connection string (default: postgresql+asyncpg://postgres:postgres@localhost:5432/myth)
- `DATABASE_POOL_SIZE`: Connection pool size (default: 20)
- `DATABASE_MAX_OVERFLOW`: Max pool overflow (default: 10)
- `DATABASE_ECHO`: Enable SQL logging (default: false)

## Migrations

Migrations are handled by Alembic:

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```
