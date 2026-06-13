"""
Pytest configuration for Gateway Service tests.

Sets up test database and mocks for external dependencies.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.models import Base

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """
    Create a test database and yield a session.
    
    Each test gets a fresh database.
    """
    # Create async engine
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Yield session for test
    async with async_session() as session:
        yield session

    # Cleanup: drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def mock_publish(monkeypatch):
    """Mock the event publish function."""
    mock = AsyncMock()
    monkeypatch.setattr("app.api.routes.publish", mock)
    return mock


@pytest.fixture
def mock_service_client(monkeypatch):
    """Mock the HTTP service client."""
    mock = MagicMock()
    mock.proxy_to_user_service = AsyncMock()
    monkeypatch.setattr("app.api.routes.service_client", mock)
    return mock
