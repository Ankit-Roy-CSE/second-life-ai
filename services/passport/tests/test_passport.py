"""
Tests for the Product Passport Service.

Covers:
- Domain: PassportService.handle_product_graded — creates passport, idempotent
- Domain: PassportService.handle_lifecycle_decision — merges data, idempotent
- Domain: Passport status progression PENDING→GRADED→ACTIVE
- Route: GET /passports/{id} — happy path + 404
- Route: GET /passports/by-product/{product_id} — happy path
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.models import Base
from app.domain.service import PassportService

# ── Test database (SQLite in-memory) ─────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _make_test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def db_session():
    """Provide a fresh in-memory SQLite session per test."""
    engine = await _make_test_engine()
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def return_id():
    return str(uuid.uuid4())


@pytest.fixture
def product_id():
    return str(uuid.uuid4())


@pytest.fixture
def user_id():
    return str(uuid.uuid4())


# ── Domain tests ─────────────────────────────────────────────────────────────


class TestPassportService:

    @pytest.mark.asyncio
    async def test_handle_product_graded_creates_passport(
        self, db_session, return_id, product_id, user_id
    ):
        """handle_product_graded should create a new Passport in GRADED status."""
        service = PassportService(db_session)

        passport = await service.handle_product_graded(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade="B",
            confidence=0.88,
            damage_summary="Minor cosmetic wear on casing",
            correlation_id=return_id,
        )

        assert passport.return_id == return_id
        assert passport.product_id == product_id
        assert passport.current_grade == "B"
        assert passport.grade_confidence == 0.88
        assert passport.damage_summary == "Minor cosmetic wear on casing"
        assert passport.status == "GRADED"
        assert len(passport.ownership_history) == 1
        assert passport.ownership_history[0]["event"] == "graded"
        assert passport.ownership_history[0]["grade"] == "B"

    @pytest.mark.asyncio
    async def test_handle_product_graded_idempotent(
        self, db_session, return_id, product_id, user_id
    ):
        """Calling handle_product_graded twice for the same return_id should not duplicate."""
        service = PassportService(db_session)

        passport1 = await service.handle_product_graded(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade="A",
            confidence=0.95,
            damage_summary="Like new",
            correlation_id=return_id,
        )
        passport2 = await service.handle_product_graded(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade="A",
            confidence=0.95,
            damage_summary="Like new",
            correlation_id=return_id,
        )

        # Same passport object returned both times
        assert passport1.id == passport2.id
        # Ownership history not doubled
        assert len(passport2.ownership_history) == 1

    @pytest.mark.asyncio
    async def test_handle_lifecycle_decision_merges_and_activates(
        self, db_session, return_id, product_id, user_id
    ):
        """handle_lifecycle_decision should merge data and set status=ACTIVE."""
        service = PassportService(db_session)

        # First: grade the product
        await service.handle_product_graded(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade="C",
            confidence=0.72,
            damage_summary="Moderate wear",
            correlation_id=return_id,
        )

        # Then: apply lifecycle decision
        passport = await service.handle_lifecycle_decision(
            return_id=return_id,
            action="REFURBISH",
            value_recovery_estimate=45.0,
            sustainability_score=78.5,
            correlation_id=return_id,
        )

        assert passport.return_id == return_id
        assert passport.lifecycle_action == "REFURBISH"
        assert passport.value_recovery_estimate == 45.0
        assert passport.sustainability_score == 78.5
        assert passport.status == "ACTIVE"
        # Sustainability summary populated
        assert passport.sustainability["score"] == 78.5
        assert passport.sustainability["action"] == "REFURBISH"
        # Ownership history has both events
        events = [e["event"] for e in passport.ownership_history]
        assert "graded" in events
        assert "lifecycle_decided" in events
        # Refurb history entry added for REFURBISH action
        assert len(passport.refurb_history) == 1
        assert passport.refurb_history[0]["event"] == "refurb_started"

    @pytest.mark.asyncio
    async def test_handle_lifecycle_decision_idempotent(
        self, db_session, return_id, product_id, user_id
    ):
        """Calling handle_lifecycle_decision twice should not duplicate data."""
        service = PassportService(db_session)

        await service.handle_product_graded(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade="A",
            confidence=0.93,
            damage_summary="Near perfect",
        )

        passport1 = await service.handle_lifecycle_decision(
            return_id=return_id,
            action="RESELL",
            value_recovery_estimate=120.0,
            sustainability_score=90.0,
        )
        passport2 = await service.handle_lifecycle_decision(
            return_id=return_id,
            action="RESELL",
            value_recovery_estimate=120.0,
            sustainability_score=90.0,
        )

        assert passport1.id == passport2.id
        # Ownership history not doubled for lifecycle event
        lifecycle_events = [e for e in passport2.ownership_history if e["event"] == "lifecycle_decided"]
        assert len(lifecycle_events) == 1

    @pytest.mark.asyncio
    async def test_get_passport_by_id_not_found(self, db_session):
        """get_passport_by_id returns None for unknown id."""
        service = PassportService(db_session)
        result = await service.get_passport_by_id("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_passports_by_product_empty(self, db_session, product_id):
        """get_passports_by_product returns empty list for a product with no passports."""
        service = PassportService(db_session)
        items, total = await service.get_passports_by_product(product_id)
        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_passport_ensures_product_created(
        self, db_session, return_id, product_id, user_id
    ):
        """handle_product_graded should create a canonical Product stub if none exists."""
        service = PassportService(db_session)

        await service.handle_product_graded(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade="D",
            confidence=0.50,
            damage_summary="Heavy damage",
        )

        product = await service.get_product(product_id)
        assert product is not None
        assert product.id == product_id
        assert product.owner_user_id == user_id


# ── Route tests ───────────────────────────────────────────────────────────────


@pytest.fixture
async def test_app(db_session):
    """Minimal test app with passport routes and DB overridden."""
    from app.api.routes import router
    from app.db.session import get_db

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session

    return app


class TestPassportRoutes:

    @pytest.mark.asyncio
    async def test_get_passport_not_found(self, test_app):
        """GET /passports/{id} returns 404 when passport doesn't exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/passports/{uuid.uuid4()}")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_passport_success(
        self, test_app, db_session, return_id, product_id, user_id
    ):
        """GET /passports/{id} returns the passport when it exists."""
        # Create a passport via the service
        service = PassportService(db_session)
        passport = await service.handle_product_graded(
            return_id=return_id,
            product_id=product_id,
            user_id=user_id,
            grade="A",
            confidence=0.97,
            damage_summary="Excellent condition",
        )
        await service.handle_lifecycle_decision(
            return_id=return_id,
            action="RESELL",
            value_recovery_estimate=200.0,
            sustainability_score=95.0,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/passports/{passport.id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == passport.id
        assert body["return_id"] == return_id
        assert body["product_id"] == product_id
        assert body["current_grade"] == "A"
        assert body["status"] == "ACTIVE"
        assert body["lifecycle_action"] == "RESELL"

    @pytest.mark.asyncio
    async def test_get_passports_by_product_empty(self, test_app, product_id):
        """GET /passports/by-product/{product_id} returns empty for unknown product."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/passports/by-product/{product_id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    @pytest.mark.asyncio
    async def test_get_passports_by_product_returns_items(
        self, test_app, db_session, product_id, user_id
    ):
        """GET /passports/by-product/{product_id} returns passports after insertion."""
        service = PassportService(db_session)

        # Create two passports for the same product (different returns)
        for _ in range(2):
            rid = str(uuid.uuid4())
            await service.handle_product_graded(
                return_id=rid,
                product_id=product_id,
                user_id=user_id,
                grade="B",
                confidence=0.80,
                damage_summary="Minor scratches",
            )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/passports/by-product/{product_id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
