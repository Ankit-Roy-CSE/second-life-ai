"""
Tests for Gateway returns endpoints.

Tests:
- POST /returns (create return, emit event)
- GET /returns (list returns)
- GET /returns/{id} (get return detail)
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.domain.models import Return
from app.main import app


@pytest.mark.asyncio
async def test_create_return_success(test_db, mock_publish, monkeypatch):
    """Test creating a return successfully."""
    # Mock JWT verification to return a user_id
    async def mock_get_current_user_id(authorization=None):
        return "user-123"

    monkeypatch.setattr("app.api.routes.get_current_user_id", mock_get_current_user_id)
    
    # Mock the database session
    async def mock_get_db():
        yield test_db
    
    monkeypatch.setattr("app.api.routes.get_db", mock_get_db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/returns",
            json={
                "product_id": "product-456",
                "reason": "Defective screen",
                "media_urls": ["media/image1.jpg", "media/image2.jpg"],
            },
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == "product-456"
    assert data["user_id"] == "user-123"
    assert data["reason"] == "Defective screen"
    assert data["status"] == "SUBMITTED"
    assert len(data["media"]) == 2
    assert "id" in data
    assert "created_at" in data

    # Verify event was published
    mock_publish.assert_called_once()
    call_args = mock_publish.call_args
    assert call_args[1]["event_type"] == "ReturnSubmitted"
    assert call_args[1]["data"]["product_id"] == "product-456"

    # Verify Return was created in database
    result = await test_db.execute(select(Return))
    returns = result.scalars().all()
    assert len(returns) == 1
    assert returns[0].product_id == "product-456"


@pytest.mark.asyncio
async def test_create_return_without_auth(mock_publish):
    """Test creating a return without authentication fails."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/returns",
            json={
                "product_id": "product-456",
                "reason": "Defective screen",
            },
        )

    assert response.status_code == 401
    # Verify no event was published
    mock_publish.assert_not_called()


@pytest.mark.asyncio
async def test_list_returns_empty(test_db, monkeypatch):
    """Test listing returns when database is empty."""
    # Mock the database session
    async def mock_get_db():
        yield test_db
    
    monkeypatch.setattr("app.api.routes.get_db", mock_get_db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/returns")

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_returns_with_data(test_db, monkeypatch):
    """Test listing returns with data."""
    # Create test returns
    return1 = Return(
        id="return-1",
        product_id="product-1",
        user_id="user-123",
        reason="Defective",
        media=["media/img1.jpg"],
        status="SUBMITTED",
    )
    return2 = Return(
        id="return-2",
        product_id="product-2",
        user_id="user-123",
        reason="Wrong item",
        media=[],
        status="GRADED",
    )
    test_db.add_all([return1, return2])
    await test_db.commit()

    # Mock the database session
    async def mock_get_db():
        yield test_db
    
    monkeypatch.setattr("app.api.routes.get_db", mock_get_db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/returns")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_returns_with_filter(test_db, monkeypatch):
    """Test listing returns with user_id filter."""
    # Create test returns for different users
    return1 = Return(
        id="return-1",
        product_id="product-1",
        user_id="user-123",
        reason="Defective",
        media=[],
        status="SUBMITTED",
    )
    return2 = Return(
        id="return-2",
        product_id="product-2",
        user_id="user-456",
        reason="Wrong item",
        media=[],
        status="SUBMITTED",
    )
    test_db.add_all([return1, return2])
    await test_db.commit()

    # Mock the database session
    async def mock_get_db():
        yield test_db
    
    monkeypatch.setattr("app.api.routes.get_db", mock_get_db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/returns?user_id=user-123")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == "user-123"
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_get_return_detail_success(test_db, monkeypatch):
    """Test getting return detail."""
    # Create test return
    return1 = Return(
        id="return-1",
        product_id="product-1",
        user_id="user-123",
        reason="Defective",
        media=["media/img1.jpg"],
        status="SUBMITTED",
    )
    test_db.add(return1)
    await test_db.commit()

    # Mock the database session
    async def mock_get_db():
        yield test_db
    
    monkeypatch.setattr("app.api.routes.get_db", mock_get_db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/returns/return-1")

    assert response.status_code == 200
    data = response.json()
    assert "return_data" in data
    assert data["return_data"]["id"] == "return-1"
    assert data["return_data"]["product_id"] == "product-1"
    # P1-A2: only return data, no aggregation yet
    assert data["grade"] is None
    assert data["decision"] is None
    assert data["passport"] is None
    assert data["matches"] == []


@pytest.mark.asyncio
async def test_get_return_detail_not_found(test_db, monkeypatch):
    """Test getting non-existent return."""
    # Mock the database session
    async def mock_get_db():
        yield test_db
    
    monkeypatch.setattr("app.api.routes.get_db", mock_get_db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/returns/nonexistent-id")

    assert response.status_code == 404
