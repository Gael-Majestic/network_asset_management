# ==============================================================
# alembic/env.py
#
# WHAT THIS FILE DOES:
#   Configures how Alembic connects to the database and
#   discovers your models to generate migrations automatically.
#
# CONCEPT — Autogenerate migrations:
# When you run `alembic revision --autogenerate -m "your message"`,
# Alembic:
#   1. Connects to your database
#   2. Compares current DB schema vs your SQLAlchemy models
#   3. Generates a Python migration script with the differences
#
# For this to work, Alembic needs to import your Base AND
# all your model files so it knows what tables should exist.
#
# CONCEPT — Async migrations:
# The app talks to PostgreSQL through asyncpg, an async driver.
# Alembic itself runs migrations synchronously, so this file
# follows the "asyncio" recipe from the Alembic documentation:
# open an async connection, then hand it to Alembic through
# connection.run_sync(). One driver serves both the app and the
# migrations, so no second (synchronous) driver is needed.
# https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
# ==============================================================

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import our settings to get the database URL
from app.core.config import settings

# Import Base — Alembic needs it to compare models vs DB
from app.db.database import Base

# Import ALL models so Alembic can "see" them
# If you add a new model file, import it here too
from app.models import asset, incident, user  # noqa: F401

# Alembic Config object (reads from alembic.ini)
config = context.config

# Set up logging from the alembic.ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# CONCEPT — target_metadata:
# This tells Alembic what your DESIRED schema looks like.
# It reads all models that are registered with Base.
# Alembic compares this against the current database state
# to figure out what migrations are needed.
target_metadata = Base.metadata

# The URL comes from our settings (the same POSTGRES_* variables the app
# reads). A sqlalchemy.url set in alembic.ini or by a script takes priority,
# which is handy for pointing Alembic at a throwaway database.
DATABASE_URL = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL


def run_migrations_offline() -> None:
    """
    CONCEPT — Offline mode:
    Generates SQL migration scripts without connecting to the DB.
    Useful when you want to review SQL before running it.
    Run with: alembic upgrade head --sql
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Runs the migrations on a connection that Alembic can use synchronously."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    CONCEPT — Online mode (the normal mode):
    Connects to the database and runs migrations directly.
    Run with: alembic upgrade head

    NullPool: migrations run once and exit, so there is no point
    keeping a pool of connections open.
    """
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# Run the appropriate mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
