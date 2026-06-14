"""
Tests for the Lifecycle Decision Service.

Covers:
- Route: GET /decisions/{return_id} — happy path + 404
- Route: GET /decisions — list endpoint
- Domain: LifecycleService.decide_lifecycle idempotency
- Domain: decision stored correctly from AI result
- Events: handle_product_graded emits LifecycleDecisionCreated
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shared_py.ai.schemas import LifecycleDecision as LifecycleDecisionSchema
from shared_py.events.schemas import EventEnvelope, ProductGradedEventData
from shared_py.schemas.enums import LifecycleAction

from app.domain.models import Base
from app.domain.service import LifecycleService

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
def grade_id():
    return str(uuid.uuid4())


@pytest.fixture
def mock_lifecycle_decision():
    """A deterministic RESELL decision from the mock AI."""
    return LifecycleDecisionSchema(
        action=LifecycleAction.RESELL,
        rationale="Grade A electronics is in excellent condition and can be resold as-is.",
        value_recovery_estimate=75.0,
        sustainability_score=85.0,
        confidence=0.90,
    )


# ── Domain tests ─────────────────────────────────────────────────────────────


class TestLifecycleService:

    @pytest.mark.asyncio
    async def test_decide_lifecycle_persists_result(
        self, db_session, return_id, grade_id, mock_lifecycle_decision
    ):
        """LifecycleService.decide_lifecycle should persist a LifecycleDecision row."""
        with patch("app.domain.service.ai_client") as mock_ai:
            mock_ai.decide_lifecycle = AsyncMock(return_value=mock_lifecycle_decision)

            service = LifecycleService(db_session)
            decision = await service.decide_lifecycle(
                return_id=return_id,
                grade_id=grade_id,
                grade="A",
                product_category="electronics",
                value_estimate=100.0,
            )

        assert decision.return_id == return_id
        assert decision.grade_id == grade_id
        assert decision.action == "RESELL"
        assert decision.rationale == mock_lifecycle_decision.rationale
        assert decision.value_recovery_estimate == 75.0
        assert decision.sustainability_score == 85.0

    @pytest.mark.asyncio
    async def test_decide_lifecycle_idempotent(
        self, db_session, return_id, grade_id, mock_lifecycle_decision
    ):
        """Calling decide_lifecycle twice for the same return_id should not call AI twice."""
        with patch("app.domain.service.ai_client") as mock_ai:
            mock_ai.decide_lifecycle = AsyncMock(return_value=mock_lifecycle_decision)

            service = LifecycleService(db_session)
            decision1 = await service.decide_lifecycle(
                return_id=return_id,
                grade_id=grade_id,
                grade="A",
                product_category="electronics",
                value_estimate=100.0,
            )
            decision2 = await service.decide_lifecycle(
                return_id=return_id,
                grade_id=grade_id,
                grade="A",
                product_category="electronics",
                value_estimate=100.0,
            )

        # AI should only be called once
        assert mock_ai.decide_lifecycle.call_count == 1
        assert decision1.id == decision2.id

    @pytest.mark.asyncio
    async def test_get_decision_by_return_id_not_found(self, db_session):
        """get_decision_by_return_id returns None for unknown return_id."""
        service = LifecycleService(db_session)
        result = await service.get_decision_by_return_id("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_all_actions_storable(self, db_session, grade_id):
        """All five lifecycle actions should persist correctly."""
        action_to_grade = {
            LifecycleAction.RESELL: "A",
            LifecycleAction.REFURBISH: "C",
            LifecycleAction.DONATE: "C",
            LifecycleAction.RECYCLE: "D",
            LifecycleAction.HYPERLOCAL: "B",
        }
        for action, grade_val in action_to_grade.items():
            rid = str(uuid.uuid4())
            mock_result = LifecycleDecisionSchema(
                action=action,
                rationale=f"Test rationale for {action.value}",
                value_recovery_estimate=50.0,
                sustainability_score=70.0,
                confidence=0.85,
            )
            with patch("app.domain.service.ai_client") as mock_ai:
                mock_ai.decide_lifecycle = AsyncMock(return_value=mock_result)
                service = LifecycleService(db_session)
                decision = await service.decide_lifecycle(
                    return_id=rid,
                    grade_id=grade_id,
                    grade=grade_val,
                    product_category="electronics",
                    value_estimate=100.0,
                )
            assert decision.action == action.value


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


class TestDecisionsRoutes:

    @pytest.mark.asyncio
    async def test_get_decision_not_found(self, test_app):
        """GET /decisions/{return_id} returns 404 when decision doesn't exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/decisions/{uuid.uuid4()}")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_decision_success(
        self, test_app, db_session, return_id, grade_id, mock_lifecycle_decision
    ):
        """GET /decisions/{return_id} returns the decision when it exists."""
        with patch("app.domain.service.ai_client") as mock_ai:
            mock_ai.decide_lifecycle = AsyncMock(return_value=mock_lifecycle_decision)
            service = LifecycleService(db_session)
            await service.decide_lifecycle(
                return_id=return_id,
                grade_id=grade_id,
                grade="A",
                product_category="electronics",
                value_estimate=100.0,
            )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/decisions/{return_id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["return_id"] == return_id
        assert body["action"] == "RESELL"
        assert body["value_recovery_estimate"] == 75.0
        assert body["sustainability_score"] == 85.0
        assert "rationale" in body

    @pytest.mark.asyncio
    async def test_list_decisions_empty(self, test_app):
        """GET /decisions returns empty list when no decisions exist."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/decisions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    @pytest.mark.asyncio
    async def test_list_decisions_returns_items(
        self, test_app, db_session, grade_id, mock_lifecycle_decision
    ):
        """GET /decisions returns decisions after insertion."""
        for _ in range(2):
            rid = str(uuid.uuid4())
            with patch("app.domain.service.ai_client") as mock_ai:
                mock_ai.decide_lifecycle = AsyncMock(return_value=mock_lifecycle_decision)
                service = LifecycleService(db_session)
                await service.decide_lifecycle(
                    return_id=rid,
                    grade_id=grade_id,
                    grade="A",
                    product_category="electronics",
                    value_estimate=100.0,
                )

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/decisions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2


# ── Event handler tests ──────────────────────────────────────────────────────


class TestEventHandler:

    @pytest.mark.asyncio
    async def test_handle_product_graded_creates_decision(
        self, db_session, return_id, grade_id, mock_lifecycle_decision
    ):
        """handle_product_graded should create a decision and publish an event."""
        from app.events.handlers import handle_product_graded

        envelope = EventEnvelope(
            event_id=str(uuid.uuid4()),
            event_type="ProductGraded",
            event_version="1.0",
            occurred_at="2026-06-14T10:00:00Z",
            correlation_id=return_id,
            producer="grading",
            data=ProductGradedEventData(
                return_id=return_id,
                grade_id=grade_id,
                product_id=str(uuid.uuid4()),
                grade="A",
                confidence=0.90,
                damage_summary="Excellent condition",
                defects=[],
            ).model_dump(mode="json"),
        )

        # Patch session factory and publish
        session_factory = async_sessionmaker(
            bind=(await _make_test_engine()), expire_on_commit=False
        )

        with (
            patch("app.events.handlers._session_factory", session_factory),
            patch("app.domain.service.ai_client") as mock_ai,
            patch("app.events.handlers.publish", new_callable=AsyncMock) as mock_publish,
            patch("app.config.settings") as mock_settings,
        ):
            mock_ai.decide_lifecycle = AsyncMock(return_value=mock_lifecycle_decision)
            mock_settings.redis_url = "redis://localhost:6379/0"

            await handle_product_graded(envelope)

            # Verify publish was called with correct event type
            mock_publish.assert_called_once()
            call_kwargs = mock_publish.call_args[1]
            assert call_kwargs["event_type"] == "LifecycleDecisionCreated"
            assert call_kwargs["correlation_id"] == return_id
            assert call_kwargs["producer"] == "lifecycle"
            assert call_kwargs["data"]["action"] == "RESELL"
            assert call_kwargs["data"]["return_id"] == return_id
