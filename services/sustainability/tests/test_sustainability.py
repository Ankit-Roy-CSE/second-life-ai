"""
Tests for the Sustainability Service.

Covers:
- Calculator: pure function unit tests
- Domain: SustainabilityService upsert, idempotency, metrics aggregation
- Routes: GET /sustainability, GET /sustainability/{id}, GET /sustainability/metrics
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.calculator import (
    calculate_co2_avoided,
    calculate_green_credits,
    calculate_metrics,
    calculate_waste_diverted,
)
from app.domain.models import Base, SustainabilityRecord
from app.domain.service import SustainabilityService

# ── Test DB ──────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def _make_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


@pytest.fixture
async def db_session():
    engine = await _make_engine()
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


# ── Calculator tests ─────────────────────────────────────────────────────────

class TestCalculator:

    def test_co2_avoided_hyperlocal(self):
        """Short distance → smaller CO₂ avoided (less logistics bypassed)."""
        co2_short = calculate_co2_avoided("electronics", distance_km=5.0)
        co2_default = calculate_co2_avoided("electronics", distance_km=None)
        assert co2_short < co2_default
        assert co2_short > 0

    def test_co2_avoided_non_negative(self):
        assert calculate_co2_avoided("clothing", distance_km=0.1) >= 0.0

    def test_waste_diverted_resell_highest(self):
        """RESELL diverts more waste than RECYCLE."""
        resell = calculate_waste_diverted("electronics", "RESELL")
        recycle = calculate_waste_diverted("electronics", "RECYCLE")
        assert resell > recycle

    def test_waste_diverted_non_negative(self):
        assert calculate_waste_diverted("furniture", "DONATE") >= 0.0

    def test_green_credits_proportional_to_value(self):
        low = calculate_green_credits(co2_avoided_kg=1.0, value_recovered=10.0)
        high = calculate_green_credits(co2_avoided_kg=1.0, value_recovered=100.0)
        assert high > low

    def test_calculate_metrics_returns_all_keys(self):
        result = calculate_metrics(
            category="electronics",
            lifecycle_action="RESELL",
            value_recovered=75.0,
            distance_km=10.0,
        )
        assert set(result.keys()) == {
            "co2_avoided_kg",
            "waste_diverted_kg",
            "value_recovered",
            "green_credits",
        }
        for v in result.values():
            assert v >= 0.0

    def test_calculate_metrics_no_distance_uses_average(self):
        result = calculate_metrics(
            category="clothing",
            lifecycle_action="DONATE",
            value_recovered=20.0,
        )
        assert result["co2_avoided_kg"] > 0


# ── Service tests ─────────────────────────────────────────────────────────────

class TestSustainabilityService:

    @pytest.mark.asyncio
    async def test_process_match_found_creates_record(self, db_session):
        service = SustainabilityService(db_session)
        rid = str(uuid.uuid4())

        record = await service.process_match_found(
            return_id=rid,
            product_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            category="electronics",
            lifecycle_action="HYPERLOCAL",
            value_recovered=80.0,
            distance_km=3.5,
        )

        assert record.return_id == rid
        assert record.co2_avoided_kg > 0
        assert record.waste_diverted_kg > 0
        assert record.green_credits > 0
        assert record.lifecycle_stage == "MATCHED"

    @pytest.mark.asyncio
    async def test_idempotent_upsert(self, db_session):
        """Calling _upsert twice for the same return_id doesn't create duplicates."""
        service = SustainabilityService(db_session)
        rid = str(uuid.uuid4())

        r1 = await service.process_match_found(
            return_id=rid, product_id="p1", user_id="u1",
            category="electronics", lifecycle_action="HYPERLOCAL",
            value_recovered=50.0, distance_km=2.0,
        )
        r2 = await service.process_match_found(
            return_id=rid, product_id="p1", user_id="u1",
            category="electronics", lifecycle_action="HYPERLOCAL",
            value_recovered=50.0, distance_km=2.0,
        )
        assert r1.id == r2.id

    @pytest.mark.asyncio
    async def test_process_purchase_completed_updates_value(self, db_session):
        service = SustainabilityService(db_session)
        rid = str(uuid.uuid4())

        # First list the product
        await service.process_product_listed(
            return_id=rid, product_id="p2", user_id="u2",
            category="electronics", lifecycle_action="RESELL",
            value_recovered=40.0,
        )

        # Then complete the purchase at actual price
        record = await service.process_purchase_completed(
            return_id=rid, product_id="p2", user_id="u2", actual_price=95.0
        )

        assert record.value_recovered == 95.0
        assert record.lifecycle_stage == "COMPLETED"

    @pytest.mark.asyncio
    async def test_get_metrics_totals(self, db_session):
        service = SustainabilityService(db_session)
        uid = str(uuid.uuid4())

        for i in range(3):
            await service.process_no_match_found(
                return_id=str(uuid.uuid4()), product_id=str(uuid.uuid4()),
                user_id=uid, category="electronics", lifecycle_action="MARKETPLACE",
                value_recovered=30.0,
            )

        metrics = await service.get_metrics(user_id=uid)
        assert metrics.total_returns_processed == 3
        assert metrics.total_co2_avoided_kg > 0
        assert metrics.total_green_credits > 0

    @pytest.mark.asyncio
    async def test_list_records_filter_by_return_id(self, db_session):
        service = SustainabilityService(db_session)
        rid = str(uuid.uuid4())

        await service.process_product_listed(
            return_id=rid, product_id="p3", user_id="u3",
            category="clothing", lifecycle_action="DONATE", value_recovered=10.0,
        )

        items, total = await service.list_records(return_id=rid)
        assert total == 1
        assert items[0].return_id == rid


# ── Route tests ───────────────────────────────────────────────────────────────

@pytest.fixture
async def test_app(db_session):
    from app.api.routes import router
    from app.db.session import get_db

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session
    return app


class TestRoutes:

    @pytest.mark.asyncio
    async def test_list_records_empty(self, test_app):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/sustainability")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_get_record_not_found(self, test_app):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/sustainability/{uuid.uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_record_success(self, test_app, db_session):
        service = SustainabilityService(db_session)
        rid = str(uuid.uuid4())
        record = await service.process_match_found(
            return_id=rid, product_id="p4", user_id="u4",
            category="electronics", lifecycle_action="HYPERLOCAL",
            value_recovered=60.0, distance_km=4.0,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/sustainability/{record.id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["return_id"] == rid
        assert body["lifecycle_stage"] == "MATCHED"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, test_app, db_session):
        service = SustainabilityService(db_session)
        uid = str(uuid.uuid4())
        await service.process_match_found(
            return_id=str(uuid.uuid4()), product_id="p5", user_id=uid,
            category="electronics", lifecycle_action="HYPERLOCAL",
            value_recovered=50.0, distance_km=2.5,
        )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/sustainability/metrics", params={"user_id": uid})

        assert resp.status_code == 200
        body = resp.json()
        assert body["total_returns_processed"] == 1
        assert body["total_co2_avoided_kg"] > 0
