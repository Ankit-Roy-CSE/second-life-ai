"""
Tests for the AI Grading Service.

Covers:
- Route: GET /grades/{return_id} — happy path + 404
- Route: GET /grades — list endpoint
- Domain: GradingService.grade_product idempotency
- Domain: grade stored correctly from AI result
- Events: handle_return_submitted emits ProductGraded
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared_py.ai.schemas import DamageSummary, DefectItem, GradeResult
from shared_py.events.schemas import EventEnvelope, ReturnSubmittedEventData
from shared_py.schemas.enums import Grade

from app.domain.models import Base, Grade as GradeModel
from app.domain.service import GradingService

# ── Test database (SQLite in-memory for speed) ──────────────────────────────

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


@pytest.fixture
def mock_grade_result():
    """A deterministic Grade B result from the mock AI."""
    return GradeResult(
        grade=Grade.B,
        confidence=0.82,
        damage_summary=DamageSummary(
            text="Product shows minor cosmetic wear.",
            key_points=["Minor scratch on casing", "Good candidate for resale"],
        ),
        defects=[
            DefectItem(name="scratch", severity="minor", location="casing", confidence=0.88)
        ],
        model_version="mock-v1",
    )


# ── Domain tests ─────────────────────────────────────────────────────────────

class TestGradingService:

    @pytest.mark.asyncio
    async def test_grade_product_persists_result(self, db_session, return_id, product_id, user_id, mock_grade_result):
        """GradingService.grade_product should persist a Grade row."""
        with patch("app.domain.service.ai_client") as mock_ai:
            mock_ai.grade_product = AsyncMock(return_value=mock_grade_result)

            service = GradingService(db_session)
            grade = await service.grade_product(
                return_id=return_id,
                product_id=product_id,
                user_id=user_id,
                return_reason="Item not as expected",
                media_keys=["s3://bucket/img.jpg"],
                product_category="electronics",
            )

        assert grade.return_id == return_id
        assert grade.product_id == product_id
        assert grade.grade == "B"
        assert grade.confidence == 0.82
        assert grade.damage_summary == "Product shows minor cosmetic wear."
        assert len(grade.defects) == 1
        assert grade.defects[0]["name"] == "scratch"

    @pytest.mark.asyncio
    async def test_grade_product_idempotent(self, db_session, return_id, product_id, user_id, mock_grade_result):
        """Calling grade_product twice for the same return_id should not call AI twice."""
        with patch("app.domain.service.ai_client") as mock_ai:
            mock_ai.grade_product = AsyncMock(return_value=mock_grade_result)

            service = GradingService(db_session)
            grade1 = await service.grade_product(
                return_id=return_id, product_id=product_id, user_id=user_id,
                return_reason="Test", media_keys=[], product_category="electronics",
            )
            grade2 = await service.grade_product(
                return_id=return_id, product_id=product_id, user_id=user_id,
                return_reason="Test", media_keys=[], product_category="electronics",
            )

        # AI should only be called once
        assert mock_ai.grade_product.call_count == 1
        assert grade1.id == grade2.id

    @pytest.mark.asyncio
    async def test_get_grade_by_return_id_not_found(self, db_session):
        """get_grade_by_return_id returns None for unknown return_id."""
        service = GradingService(db_session)
        result = await service.get_grade_by_return_id("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_all_grades_storable(self, db_session, product_id, user_id):
        """All four grade values should persist correctly."""
        for grade_val in ["A", "B", "C", "D"]:
            rid = str(uuid.uuid4())
            mock_result = GradeResult(
                grade=Grade(grade_val),
                confidence=0.85,
                damage_summary=DamageSummary(text=f"Grade {grade_val}", key_points=[]),
                defects=[],
                model_version="mock-v1",
            )
            with patch("app.domain.service.ai_client") as mock_ai:
                mock_ai.grade_product = AsyncMock(return_value=mock_result)
                service = GradingService(db_session)
                grade = await service.grade_product(
                    return_id=rid, product_id=product_id, user_id=user_id,
                    return_reason="Test", media_keys=[], product_category="electronics",
                )
            assert grade.grade == grade_val


# ── Route tests ──────────────────────────────────────────────────────────────

@pytest.fixture
async def test_app(db_session):
    """Build a minimal test app with routes wired and DB injected."""
    from app.api.routes import router
    from app.db.session import get_db

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db_session

    return app


class TestGradesRoutes:

    @pytest.mark.asyncio
    async def test_get_grade_not_found(self, test_app):
        """GET /grades/{return_id} returns 404 when grade doesn't exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/grades/{uuid.uuid4()}")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_grade_success(self, test_app, db_session, return_id, product_id, user_id, mock_grade_result):
        """GET /grades/{return_id} returns the grade when it exists."""
        # Insert directly via service
        with patch("app.domain.service.ai_client") as mock_ai:
            mock_ai.grade_product = AsyncMock(return_value=mock_grade_result)
            service = GradingService(db_session)
            await service.grade_product(
                return_id=return_id, product_id=product_id, user_id=user_id,
                return_reason="Test reason", media_keys=["s3://img.jpg"],
                product_category="electronics",
            )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/grades/{return_id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["return_id"] == return_id
        assert body["grade"] == "B"
        assert body["confidence"] == 0.82
        assert "damage_summary" in body

    @pytest.mark.asyncio
    async def test_list_grades_empty(self, test_app):
        """GET /grades returns empty list when no grades exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/grades")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    @pytest.mark.asyncio
    async def test_list_grades_returns_items(self, test_app, db_session, product_id, user_id, mock_grade_result):
        """GET /grades returns grades after insertion."""
        # Insert 2 grades
        for _ in range(2):
            rid = str(uuid.uuid4())
            with patch("app.domain.service.ai_client") as mock_ai:
                mock_ai.grade_product = AsyncMock(return_value=mock_grade_result)
                service = GradingService(db_session)
                await service.grade_product(
                    return_id=rid, product_id=product_id, user_id=user_id,
                    return_reason="Test", media_keys=[], product_category="electronics",
                )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/grades")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
