# ==============================================================
# tests/conftest.py
#
# WHAT THIS FILE DOES:
#   Defines shared fixtures for all tests.
#   Pytest automatically discovers and uses this file.
#
# CONCEPT — conftest.py:
#   This is a special Pytest file. Any fixture defined here
#   is available to ALL test files in the tests/ folder
#   without needing to import it. Pytest handles that automatically.
#
# CONCEPT — Fixtures:
#   A fixture is a function decorated with @pytest.fixture.
#   When a test function declares a parameter with the same
#   name as a fixture, Pytest calls the fixture and passes
#   the result in automatically.
#
#   Example:
#     @pytest.fixture
#     def my_number():
#         return 42
#
#     def test_something(my_number):  # Pytest injects 42 here
#         assert my_number == 42
# ==============================================================

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.database import Base, get_db
from app.main import app

# ==============================================================
# CONCEPT — Test database:
# We use SQLite (an in-memory database) for tests instead of
# PostgreSQL. Reasons:
#   1. No need to run a real PostgreSQL server for tests
#   2. Each test run starts with a clean empty database
#   3. Tests run faster
#
# "sqlite+aiosqlite:///:memory:" means:
#   sqlite    = use SQLite
#   +aiosqlite = use the async driver
#   :memory:  = store in RAM, not on disk (wiped when tests end)
#
# In production your app uses PostgreSQL. Tests use SQLite.
# SQLAlchemy abstracts the difference — your code does not change.
# ==============================================================
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Creates the test database engine once for the entire test session.

    CONCEPT — scope="session":
    This fixture is created once and shared across ALL tests.
    The engine (connection pool) is expensive to create, so we
    reuse it. Other scopes: "function" (default, one per test),
    "module" (one per file), "session" (one for all tests).
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create all tables defined in our models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Tear down — drop all tables after all tests finish
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """
    Provides a clean database session for each test.

    CONCEPT — Transaction rollback for test isolation:
    We wrap each test in a transaction and roll it back at the end.
    This means:
      - Test 1 creates a user → rolls back → user gone
      - Test 2 starts with a clean database
    No test can affect another test's data. This is called
    "test isolation" and is essential for reliable tests.
    """
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """
    Provides an HTTP test client with the test database injected.

    CONCEPT — Dependency override:
    Our app's endpoints use get_db() to get a database session.
    Here we override that dependency to use the TEST session instead.
    The app never knows it is talking to a test database.

    app.dependency_overrides is a dict where:
      key   = the real dependency function
      value = the replacement function for tests
    """

    async def override_get_db():
        yield db_session

    # Replace the real get_db with our test version
    app.dependency_overrides[get_db] = override_get_db

    # CONCEPT — ASGITransport:
    # This lets httpx talk directly to our FastAPI app in memory,
    # without starting a real HTTP server on a port.
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Clean up the override after each test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client):
    """
    Creates a real registered user and returns their credentials.
    Used by tests that need an existing user to log in.
    """
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
    }
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest_asyncio.fixture
async def auth_token(client, registered_user):
    """
    Logs in with the registered user and returns a JWT token.
    Used by tests that need an authenticated request.

    CONCEPT — OAuth2 form data:
    The login endpoint expects form data (not JSON).
    httpx sends form data using the `data=` parameter.
    """
    response = await client.post(
        "/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """
    Returns the Authorization header dict needed for protected endpoints.

    CONCEPT — Bearer token header:
    Protected endpoints require:
      Authorization: Bearer eyJhbGciOi...
    We build this header once here and inject it into requests.
    """
    return {"Authorization": f"Bearer {auth_token}"}