# ==============================================================
# tests/test_auth.py
#
# WHAT THIS FILE DOES:
#   Tests every authentication scenario:
#     - Successful registration
#     - Duplicate email rejected
#     - Short password rejected
#     - Successful login
#     - Wrong password rejected
#     - Non-existent user rejected
#
# CONCEPT — Test naming convention:
#   Test functions must start with "test_".
#   Pytest discovers them automatically.
#   Name them clearly: test_<what>_<expected_outcome>
#   e.g. test_register_duplicate_email_returns_400
#   A good test name reads like a sentence describing behaviour.
# ==============================================================

import pytest


# ==============================================================
# CONCEPT — @pytest.mark.asyncio:
# Our endpoints are async. To test async functions, Pytest needs
# this decorator (provided by pytest-asyncio).
# Without it, Pytest would not await the coroutine and the test
# would pass vacuously (without actually running).
# ==============================================================


class TestRegister:
    """
    CONCEPT — Grouping tests in a class:
    Grouping related tests in a class keeps the file organized.
    All registration tests live here. All login tests live below.
    No fixtures or inheritance needed — it is purely organisational.
    """

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """A valid registration creates a user and returns 201."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "securepassword123",
            },
        )

        # CONCEPT — What to assert:
        # Always assert at minimum: status code and key response fields.
        # Do not assert timestamps or IDs exactly — they change.
        # Assert the shape and meaning of the response.
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_admin"] is False

        # CONCEPT — Negative assertion:
        # Verify that sensitive fields are NOT in the response.
        # This is as important as asserting what IS there.
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_400(self, client):
        """Registering the same email twice returns 400."""
        payload = {
            "email": "duplicate@example.com",
            "password": "password123",
        }

        # First registration — should succeed
        first = await client.post("/auth/register", json=payload)
        assert first.status_code == 201

        # Second registration with same email — should fail
        second = await client.post("/auth/register", json=payload)
        assert second.status_code == 400
        assert "already exists" in second.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email_returns_422(self, client):
        """An invalid email format is rejected by Pydantic validation."""
        response = await client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        # 422 = Unprocessable Entity — Pydantic validation failed
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password_returns_422(self, client):
        """A password shorter than 8 characters is rejected."""
        response = await client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:

    @pytest.mark.asyncio
    async def test_login_success_returns_token(self, client, registered_user):
        """A valid login returns a JWT token."""
        response = await client.post(
            "/auth/login",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # The response must have these two fields
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # The token must be a non-empty string
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client, registered_user):
        """Wrong password returns 401 Unauthorized."""
        response = await client.post(
            "/auth/login",
            data={
                "username": registered_user["email"],
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_returns_401(self, client):
        """Login with an email that does not exist returns 401."""
        response = await client.post(
            "/auth/login",
            data={
                "username": "nobody@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401