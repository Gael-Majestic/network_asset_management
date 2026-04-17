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
# ==============================================================

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

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

# Override the database URL from alembic.ini with our settings
# This uses the SYNCHRONOUS URL (Alembic does not support async)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)


def run_migrations_offline() -> None:
    """
    CONCEPT — Offline mode:
    Generates SQL migration scripts without connecting to the DB.
    Useful when you want to review SQL before running it.
    Run with: alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    CONCEPT — Online mode (the normal mode):
    Connects to the database and runs migrations directly.
    Run with: alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Run the appropriate mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()