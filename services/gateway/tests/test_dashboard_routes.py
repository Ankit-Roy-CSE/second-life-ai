"""
Tests for Gateway dashboard aggregation routes.

Tests the BFF endpoints that aggregate sustainability data for the dashboard.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.fixture
def mock_service_client():
    """Mock the service_client singleton for testing."""
    with patch("app.api.routes.service_client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_auth():
    """Mock authentication to return a test user_id."""
    with patch("app.api.routes.get_current_user_id") as mock_get_user:
        mock_get_user.return_value = "test-user-123"
        yield mock_get_user


@pytest.mark.asyncio
async def test_get_sustainability_metrics_success(mock_service_client, mock_auth):
    """Test GET /dashboard/sustainability/metrics returns aggregated metrics."""
    # Arrange
    mock_metrics = {
        "total_co2_avoided_kg": 45.8,
        "total_waste_diverted_kg": 23.4,
        "total_value_recovered": 850.50,
        "total_green_credits": 125,
        "record_count": 12,
    }
    mock_service_client.get_sustainability_metrics = AsyncMock(return_value=mock_metrics)

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/dashboard/sustainability/metrics")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_co2_avoided_kg"] == 45.8
    assert data["total_green_credits"] == 125
    mock_service_client.get_sustainability_metrics.assert_called_once()


@pytest.mark.asyncio
async def test_get_sustainability_metrics_with_user_filter(mock_service_client, mock_auth):
    """Test GET /dashboard/sustainability/metrics with user_id filter."""
    # Arrange
    mock_metrics = {
        "total_co2_avoided_kg": 12.3,
        "total_waste_diverted_kg": 8.1,
        "total_value_recovered": 250.00,
        "total_green_credits": 35,
        "record_count": 3,
    }
    mock_service_client.get_sustainability_metrics = AsyncMock(return_value=mock_metrics)

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/dashboard/sustainability/metrics",
            params={"user_id": "user-abc-123"}
        )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total_co2_avoided_kg"] == 12.3
    mock_service_client.get_sustainability_metrics.assert_called_once_with(
        user_id="user-abc-123",
        requesting_user_id="test-user-123",
    )


@pytest.mark.asyncio
async def test_list_sustainability_records_success(mock_service_client, mock_auth):
    """Test GET /dashboard/sustainability/records returns paginated list."""
    # Arrange
    mock_records = {
        "items": [
            {
                "id": "record-1",
                "return_id": "return-1",
                "co2_avoided_kg": 3.5,
                "waste_diverted_kg": 2.1,
                "value_recovered": 80.0,
                "green_credits": 12,
            },
            {
                "id": "record-2",
                "return_id": "return-2",
                "co2_avoided_kg": 5.2,
                "waste_diverted_kg": 3.8,
                "value_recovered": 120.0,
                "green_credits": 18,
            },
        ],
        "total": 2,
    }
    mock_service_client.list_sustainability_records = AsyncMock(return_value=mock_records)

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/dashboard/sustainability/records")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert data["items"][0]["co2_avoided_kg"] == 3.5
    mock_service_client.list_sustainability_records.assert_called_once()


@pytest.mark.asyncio
async def test_list_sustainability_records_with_filters(mock_service_client, mock_auth):
    """Test GET /dashboard/sustainability/records with filters and pagination."""
    # Arrange
    mock_records = {
        "items": [
            {
                "id": "record-1",
                "return_id": "return-abc",
                "user_id": "user-123",
                "co2_avoided_kg": 4.2,
                "waste_diverted_kg": 2.5,
                "value_recovered": 95.0,
                "green_credits": 15,
            }
        ],
        "total": 1,
    }
    mock_service_client.list_sustainability_records = AsyncMock(return_value=mock_records)

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/dashboard/sustainability/records",
            params={
                "user_id": "user-123",
                "return_id": "return-abc",
                "limit": 10,
                "offset": 0,
            }
        )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["return_id"] == "return-abc"
    mock_service_client.list_sustainability_records.assert_called_once_with(
        user_id="user-123",
        return_id="return-abc",
        limit=10,
        offset=0,
        requesting_user_id="test-user-123",
    )


@pytest.mark.asyncio
async def test_get_sustainability_metrics_unauthenticated():
    """Test that dashboard endpoints require authentication."""
    # Mock to return None (unauthenticated)
    with patch("app.api.routes.get_current_user_id", return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/dashboard/sustainability/metrics")

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "unauthenticated"


@pytest.mark.asyncio
async def test_get_sustainability_metrics_upstream_unreachable(mock_service_client, mock_auth):
    """Test that dashboard endpoints handle upstream failures gracefully."""
    # Arrange
    from shared_py.web.errors import AppError

    mock_service_client.get_sustainability_metrics = AsyncMock(
        side_effect=AppError(
            status_code=502,
            code="upstream_unreachable",
            message="Sustainability Service unreachable",
        )
    )

    # Act
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/dashboard/sustainability/metrics")

    # Assert
    assert response.status_code == 502
    data = response.json()
    assert data["error"]["code"] == "upstream_unreachable"
