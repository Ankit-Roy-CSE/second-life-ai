"""
Tests for User Service auth endpoints.

Tests:
- POST /auth/register (happy path + duplicate email)
- POST /auth/login (happy path + invalid credentials)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_success():
    """Test successful user registration."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Test User",
                "location": {"lat": 12.9716, "lng": 77.5946, "city": "Bengaluru"},
                "interests": ["Electronics", "Books"],
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data
    assert "password" not in data  # Never return password
    assert "password_hash" not in data
    assert data["green_credits"] == 0.0


@pytest.mark.asyncio
async def test_register_duplicate_email():
    """Test registration with duplicate email returns 409."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register first user
        await client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "display_name": "First User",
            },
        )

        # Try to register with same email
        response = await client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "different-password",
                "display_name": "Second User",
            },
        )

    assert response.status_code == 409
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "email_exists"


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login returns JWT and user profile."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        await client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "password123",
                "display_name": "Login User",
            },
        )

        # Login
        response = await client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert len(data["access_token"]) > 20  # JWT is a long string
    assert "user" in data
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_invalid_email():
    """Test login with non-existent email returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_login_invalid_password():
    """Test login with wrong password returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        await client.post(
            "/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "correct-password",
                "display_name": "User",
            },
        )

        # Login with wrong password
        response = await client.post(
            "/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "invalid_credentials"
