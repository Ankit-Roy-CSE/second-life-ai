"""
Tests for Gateway auth proxy endpoints.

Tests:
- POST /auth/register (proxy to User Service)
- POST /auth/login (proxy to User Service)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_proxy_success(mock_service_client):
    """Test successful registration proxy to User Service."""
    # Mock User Service response
    mock_service_client.proxy_to_user_service.return_value = {
        "id": "user-123",
        "email": "test@example.com",
        "display_name": "Test User",
        "green_credits": 0.0,
        "interests": [],
        "location": None,
        "created_at": "2026-06-14T00:00:00Z",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "display_name": "Test User",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["id"] == "user-123"

    # Verify User Service was called
    mock_service_client.proxy_to_user_service.assert_called_once()


@pytest.mark.asyncio
async def test_login_proxy_success(mock_service_client):
    """Test successful login proxy to User Service."""
    # Mock User Service response
    mock_service_client.proxy_to_user_service.return_value = {
        "access_token": "fake-jwt-token-12345",
        "user": {
            "id": "user-123",
            "email": "test@example.com",
            "display_name": "Test User",
            "green_credits": 0.0,
            "interests": [],
            "location": None,
            "created_at": "2026-06-14T00:00:00Z",
        },
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] == "fake-jwt-token-12345"
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"

    # Verify User Service was called
    mock_service_client.proxy_to_user_service.assert_called_once()


@pytest.mark.asyncio
async def test_register_proxy_validation_error():
    """Test registration with invalid data."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                # Missing required fields
            },
        )

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_login_proxy_validation_error():
    """Test login with invalid data."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                # Missing password
            },
        )

    assert response.status_code == 422  # Pydantic validation error
