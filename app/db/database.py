# ==============================================================
# app/db/database.py
#
# WHAT THIS FILE DOES:
#   Sets up the async connection to PostgreSQL using SQLAlchemy.
#   Provides:
#     - engine: the low-level connection pool
#     - AsyncSessionLocal: a factory that creates database sessions
#     - Base: the parent class all our models will inherit from
#     - get_db: a dependency function that opens/closes sessions
# ==============================================================

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ==============================================================
# CONCEPT — The Engine:
# The engine is the foundation. It holds the connection pool.
# We pass it our database URL and it handles everything else.
#
# echo=settings.DEBUG means: if DEBUG=True in .env, SQLAlchemy
# will print every SQL query it runs to the terminal. This is
# incredibly useful for learning — you see exactly what SQL
# your Python code generates. Turn it off in production.
# ==============================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,     # Print SQL queries in development
    pool_size=5,             # Keep 5 connections open and ready
    max_overflow=10,         # Allow up to 10 extra when needed
    pool_timeout=30,         # Wait up to 30 seconds for a free connection
    pool_recycle=1800,       # Recycle connections every 30 minutes
)


# ==============================================================
# CONCEPT — Session Factory:
# async_sessionmaker is a FACTORY — a function that creates
# sessions. We configure it once here, then call it wherever
# we need a new session.
#
# expire_on_commit=False means: after we commit a transaction,
# SQLAlchemy should NOT immediately invalidate the objects we
# just saved. This prevents errors when we try to access
# attributes of an object right after saving it.
# ==============================================================
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ==============================================================
# CONCEPT — DeclarativeBase:
# All our database models (User, Asset, Incident) will inherit
# from this Base class. It is what connects them to SQLAlchemy's
# mapping system. SQLAlchemy uses it to know which Python classes
# correspond to which database tables.
# ==============================================================
class Base(DeclarativeBase):
    pass


# ==============================================================
# CONCEPT — Dependency Injection with `yield`:
# This is one of the most important FastAPI patterns.
#
# get_db is an "async generator" function. It:
#   1. Opens a database session
#   2. `yield`s it to the endpoint that needs it
#   3. After the endpoint finishes (success OR error), the code
#      after `yield` runs — closing the session cleanly
#
# The `yield` keyword is the handoff point. Think of it as:
#   "Here is your session. Use it. When you are done,
#    control returns here and I will clean up."
#
# The `async with` block ensures the session is properly closed
# even if an exception is raised inside the endpoint.
#
# In your routers, you will use it like this:
#   async def get_assets(db: AsyncSession = Depends(get_db)):
#       ...
# FastAPI sees `Depends(get_db)` and calls this function
# automatically, giving the endpoint a ready-to-use session.
# ==============================================================
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()