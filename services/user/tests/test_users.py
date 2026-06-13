"""
Tests for User Service profile and candidates endpoints.

Tests:
- GET /users/{id} (happy path + not found)
- PATCH /users/{id} (update profile)
- GET /users/{id}/credits
- GET /users/candidates (cross-service call)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_user_success():
    """Test getting user profile by ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "getuser@example.com",
                "password": "password123",
                "display_name": "Get User",
            },
        )
        user_id = register_response.json()["id"]

        # Get user
        response = await client.get(f"/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "getuser@example.com"
    assert data["display_name"] == "Get User"


@pytest.mark.asyncio
async def test_get_user_not_found():
    """Test getting non-existent user returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/nonexistent-id-12345")

    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "user_not_found"


@pytest.mark.asyncio
async def test_update_user_profile():
    """Test updating user profile fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "updateuser@example.com",
                "password": "password123",
                "display_name": "Original Name",
                "interests": ["Electronics"],
            },
        )
        user_id = register_response.json()["id"]

        # Update user
        response = await client.patch(
            f"/users/{user_id}",
            json={
                "display_name": "Updated Name",
                "interests": ["Electronics", "Books", "Fashion"],
                "location": {"lat": 13.0, "lng": 77.0, "city": "Bengaluru"},
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"
    assert len(data["interests"]) == 3
    assert "Books" in data["interests"]
    assert data["location"]["city"] == "Bengaluru"


@pytest.mark.asyncio
async def test_get_credits():
    """Test getting green credit balance."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register user
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "credits@example.com",
                "password": "password123",
                "display_name": "Credits User",
            },
        )
        user_id = register_response.json()["id"]

        # Get credits
        response = await client.get(f"/users/{user_id}/credits")

    assert response.status_code == 200
    data = response.json()
    assert "green_credits" in data
    assert data["green_credits"] == 0.0  # New users start with 0


@pytest.mark.asyncio
async def test_find_candidates_by_category():
    """Test finding candidate buyers filtered by category."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register users with different interests
        await client.post(
            "/auth/register",
            json={
                "email": "buyer1@example.com",
                "password": "password123",
                "display_name": "Electronics Buyer",
                "location": {"lat": 12.9716, "lng": 77.5946, "city": "Bengaluru"},
                "interests": ["Electronics", "Books"],
            },
        )

        await client.post(
            "/auth/register",
            json={
                "email": "buyer2@example.com",
                "password": "password123",
                "display_name": "Fashion Buyer",
                "location": {"lat": 12.98, "lng": 77.60, "city": "Bengaluru"},
                "interests": ["Fashion", "Home"],
            },
        )

        # Find candidates for Electronics
        response = await client.get("/users/candidates?category=Electronics")

    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data
    assert data["total"] >= 1

    # Should include Electronics buyer, not Fashion buyer
    electronics_buyers = [
        c for c in data["candidates"] if "Electronics" in c["interests"]
    ]
    assert len(electronics_buyers) >= 1


@pytest.mark.asyncio
async def test_find_candidates_with_location():
    """Test finding candidate buyers with distance calculation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register buyers at different locations
        await client.post(
            "/auth/register",
            json={
                "email": "nearby@example.com",
                "password": "password123",
                "display_name": "Nearby Buyer",
                "location": {"lat": 12.9716, "lng": 77.5946, "city": "Bengaluru"},
                "interests": ["Electronics"],
            },
        )

        await client.post(
            "/auth/register",
            json={
                "email": "far@example.com",
                "password": "password123",
                "display_name": "Far Buyer",
                "location": {"lat": 13.5, "lng": 78.5, "city": "Far City"},
                "interests": ["Electronics"],
            },
        )

        # Find candidates within 50km of product location
        response = await client.get(
            "/users/candidates?category=Electronics&lat=12.9716&lng=77.5946&radius_km=50"
        )

    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data

    # All candidates should have distance_km calculated
    for candidate in data["candidates"]:
        assert "distance_km" in candidate
        assert candidate["distance_km"] is not None
        # Within 50km radius
        assert candidate["distance_km"] <= 50

    # Should be sorted by distance (closest first)
    distances = [c["distance_km"] for c in data["candidates"]]
    assert distances == sorted(distances)
