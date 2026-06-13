"""
Tests for shared_py.web — factory, health, errors.
These tests run without any DB or Redis (pure HTTP / in-process).
"""

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from shared_py.web import AppError, create_app
from shared_py.web.health import add_ready_check, _ready_checks


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """Minimal app built from create_app — no DB, no Redis."""
    # Clear any ready checks registered by previous tests
    _ready_checks.clear()
    return create_app(service_name="test-service")


@pytest.fixture()
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------

class TestHealth:
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "test-service"

    async def test_ready_no_checks_returns_200(self, client):
        resp = await client.get("/ready")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "ready"

    async def test_ready_all_checks_pass(self, app):
        _ready_checks.clear()
        add_ready_check("fake_db", lambda: _async_ok("ok"))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/ready")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["checks"]["fake_db"] == "ok"

    async def test_ready_failing_check_returns_503(self, app):
        _ready_checks.clear()
        add_ready_check("failing", lambda: _async_raise("connection refused"))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/ready")
        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "error" in resp.json()["checks"]["failing"]


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

class TestErrorHandlers:
    async def test_404_returns_error_envelope(self, client):
        resp = await client.get("/this-route-does-not-exist")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "not_found"

    async def test_app_error_returns_envelope(self, app):
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/boom")
        async def boom():
            raise AppError(status_code=409, code="conflict", message="already exists")

        app.include_router(router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/boom")
        assert resp.status_code == 409
        body = resp.json()
        assert body["error"]["code"] == "conflict"
        assert body["error"]["message"] == "already exists"

    async def test_validation_error_returns_envelope(self, app):
        from fastapi import APIRouter
        from pydantic import BaseModel

        class Body(BaseModel):
            name: str

        router = APIRouter()

        @router.post("/validate")
        async def validate(body: Body):
            return body

        app.include_router(router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            # Missing required field → 422
            resp = await c.post("/validate", json={})
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "validation_error"


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class TestMiddleware:
    async def test_correlation_id_set_on_response(self, app):
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/ping")
        async def ping():
            return {"pong": True}

        app.include_router(router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/ping")
        assert "x-correlation-id" in resp.headers

    async def test_correlation_id_forwarded(self, app):
        from fastapi import APIRouter
        router = APIRouter()

        @router.get("/echo-cid")
        async def echo_cid():
            return {"pong": True}

        app.include_router(router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/echo-cid", headers={"x-correlation-id": "my-cid-123"})
        assert resp.headers["x-correlation-id"] == "my-cid-123"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

class TestAuth:
    def test_create_and_decode_token(self):
        from shared_py.web.auth import create_access_token, decode_access_token
        secret = "test-secret"
        token = create_access_token(subject="user-42", secret=secret)
        payload = decode_access_token(token, secret=secret)
        assert payload["sub"] == "user-42"

    def test_invalid_token_raises_app_error(self):
        from shared_py.web.auth import decode_access_token
        with pytest.raises(AppError) as exc_info:
            decode_access_token("not.a.valid.jwt", secret="secret")
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises_app_error(self):
        from shared_py.web.auth import create_access_token, decode_access_token
        token = create_access_token(subject="u1", secret="correct-secret")
        with pytest.raises(AppError):
            decode_access_token(token, secret="wrong-secret")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _async_ok(value: str) -> str:
    return value


async def _async_raise(msg: str) -> str:
    raise RuntimeError(msg)
