"""
Tests for Gateway aggregation, proxy, purchase, and marketplace routes.

Covers:
- GET /returns/{id}     (BFF aggregation — all four upstreams)
- GET /passports/{id}   (strict proxy)
- GET /matches          (strict proxy)
- POST /purchase        (PurchaseCompleted event)
- GET /marketplace      (retry proxy)

Sections:
  9.1  Happy-path examples
  9.2  Error-path examples
  9.3  X-User-Id header forwarding examples
  10.x Property-based tests (hypothesis)
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.middleware import get_current_user_id
from app.db.session import get_db
from app.domain.models import Return
from app.main import app

# ─── helpers ──────────────────────────────────────────────────────────────────

# A fake JWT that the test auth mock will accept
FAKE_TOKEN = "Bearer test-token"
TEST_USER_ID = "user-test-123"


def _auth_mock(user_id: str = TEST_USER_ID):
    """
    Register a FastAPI dependency override for get_current_user_id and return
    the override callable.

    NOTE: FastAPI resolves dependencies by the function object captured in
    Depends() at route-definition time, so monkeypatching the module attribute
    has no effect. We must use app.dependency_overrides. Registering the
    override as a side-effect here keeps every existing call site working
    unchanged. The autouse fixture in conftest.py clears overrides after each test.
    """

    async def _mock(authorization=None):
        return user_id

    app.dependency_overrides[get_current_user_id] = _mock
    return _mock


def _mock_db(session):
    """
    Register a FastAPI dependency override for get_db that yields the test
    session, and return the override callable.
    """

    async def _gen():
        yield session

    app.dependency_overrides[get_db] = _gen
    return _gen


# ═════════════════════════════════════════════════════════════════════════════
# 9.1 Happy-path examples
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_return_detail_aggregated_success(test_db, monkeypatch):
    """All four upstreams return valid data → 200 with all fields present."""
    # Seed a Return
    ret = Return(
        id="return-agg-1",
        product_id="product-1",
        user_id=TEST_USER_ID,
        reason="Broken screen",
        media=[],
        status="SUBMITTED",
    )
    test_db.add(ret)
    await test_db.commit()

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())
    monkeypatch.setattr("app.api.routes.get_db", _mock_db(test_db))

    # Mock all four upstream calls
    mock_client = MagicMock()
    mock_client.get_grade = AsyncMock(return_value={"grade": "A", "confidence": 0.9})
    mock_client.get_decision = AsyncMock(return_value={"action": "RESELL"})
    mock_client.get_passport_by_return = AsyncMock(return_value={"passport_id": "pp-1"})
    mock_client.get_matches = AsyncMock(return_value=[{"buyer_user_id": "buyer-1"}])
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/returns/return-agg-1",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert "return_data" in data
    assert data["return_data"]["return_id"] == "return-agg-1"
    assert data["grade"] == {"grade": "A", "confidence": 0.9}
    assert data["decision"] == {"action": "RESELL"}
    assert data["passport"] == {"passport_id": "pp-1"}
    assert data["matches"] == [{"buyer_user_id": "buyer-1"}]


@pytest.mark.asyncio
async def test_get_passport_success(monkeypatch):
    """Passport Service returns 200 → 200, body unchanged."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    mock_client = MagicMock()
    mock_client.get_passport = AsyncMock(return_value={"passport_id": "pp-42", "status": "ACTIVE"})
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/passports/pp-42",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 200
    assert response.json() == {"passport_id": "pp-42", "status": "ACTIVE"}


@pytest.mark.asyncio
async def test_get_matches_success(monkeypatch):
    """Matching Service returns 200 → 200, body unchanged."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    mock_client = MagicMock()
    mock_client.get_matches_for_return = AsyncMock(
        return_value={"items": [{"id": "match-1"}], "total": 1}
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/matches?return_id=return-xyz",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 200
    assert response.json() == {"items": [{"id": "match-1"}], "total": 1}


@pytest.mark.asyncio
async def test_post_purchase_success(monkeypatch):
    """Listing lookup + publish succeed → 201 with PurchaseResponse fields."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    listing_id = str(uuid4())
    return_id = str(uuid4())
    product_id = str(uuid4())
    event_id = str(uuid4())

    mock_client = MagicMock()
    mock_client.get_listing = AsyncMock(
        return_value={"return_id": return_id, "product_id": product_id}
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    mock_pub = AsyncMock(return_value=event_id)
    monkeypatch.setattr("app.api.routes.publish", mock_pub)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/purchase",
            json={
                "listing_id": listing_id,
                "buyer_user_id": TEST_USER_ID,
                "price": 49.99,
            },
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["listing_id"] == listing_id
    assert data["buyer_user_id"] == TEST_USER_ID
    assert data["price"] == 49.99
    assert data["event_id"] == event_id
    assert data["correlation_id"] == return_id

    # Verify publish was called with correct args
    mock_pub.assert_called_once()
    call_kwargs = mock_pub.call_args[1]
    assert call_kwargs["event_type"] == "PurchaseCompleted"
    assert call_kwargs["correlation_id"] == return_id
    assert call_kwargs["data"]["buyer_user_id"] == TEST_USER_ID


@pytest.mark.asyncio
async def test_get_marketplace_success(monkeypatch):
    """Matching Service returns paginated listings on first attempt → 200."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    expected_body = {"items": [{"id": "listing-1"}], "total": 1, "limit": 20, "offset": 0}
    mock_client = MagicMock()
    mock_client._marketplace_with_retry = AsyncMock(return_value=expected_body)
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/marketplace",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 200
    assert response.json() == expected_body


# ═════════════════════════════════════════════════════════════════════════════
# 9.2 Error-path examples
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_return_detail_not_found(test_db, monkeypatch):
    """Return not in DB → 404 + ErrorEnvelope."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())
    monkeypatch.setattr("app.api.routes.get_db", _mock_db(test_db))

    mock_client = MagicMock()
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/returns/does-not-exist",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_get_passport_not_found(monkeypatch):
    """Passport Service 404 → 404 + ErrorEnvelope."""
    from shared_py.web.errors import AppError

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    mock_client = MagicMock()
    mock_client.get_passport = AsyncMock(
        side_effect=AppError(status_code=404, code="not_found", message="Passport not found")
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/passports/nonexistent",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 404
    body = response.json()
    assert "error" in body


@pytest.mark.asyncio
async def test_get_passport_unreachable(monkeypatch):
    """Passport Service ConnectError → 502, code == upstream_unreachable."""
    from shared_py.web.errors import AppError

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    mock_client = MagicMock()
    mock_client.get_passport = AsyncMock(
        side_effect=AppError(
            status_code=502,
            code="upstream_unreachable",
            message="Passport Service unreachable",
        )
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/passports/pp-1",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "upstream_unreachable"


@pytest.mark.asyncio
async def test_get_matches_missing_param(monkeypatch):
    """No return_id query param → 422."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/matches",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_matches_unreachable(monkeypatch):
    """Matching Service ConnectError → 502, code == upstream_unreachable."""
    from shared_py.web.errors import AppError

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    mock_client = MagicMock()
    mock_client.get_matches_for_return = AsyncMock(
        side_effect=AppError(
            status_code=502,
            code="upstream_unreachable",
            message="Matching Service unreachable",
        )
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/matches?return_id=return-xyz",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "upstream_unreachable"


@pytest.mark.asyncio
async def test_post_purchase_listing_not_found(monkeypatch):
    """Listing 404 → 404, publish not called."""
    from shared_py.web.errors import AppError

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    mock_client = MagicMock()
    mock_client.get_listing = AsyncMock(
        side_effect=AppError(status_code=404, code="not_found", message="Listing not found")
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    mock_pub = AsyncMock()
    monkeypatch.setattr("app.api.routes.publish", mock_pub)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/purchase",
            json={
                "listing_id": str(uuid4()),
                "buyer_user_id": TEST_USER_ID,
                "price": 10.0,
            },
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 404
    mock_pub.assert_not_called()


@pytest.mark.asyncio
async def test_post_purchase_event_publish_fail(monkeypatch):
    """Publish raises → 503, code == event_publish_failed."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    return_id = str(uuid4())
    mock_client = MagicMock()
    mock_client.get_listing = AsyncMock(
        return_value={"return_id": return_id, "product_id": str(uuid4())}
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    mock_pub = AsyncMock(side_effect=Exception("Redis down"))
    monkeypatch.setattr("app.api.routes.publish", mock_pub)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/purchase",
            json={
                "listing_id": str(uuid4()),
                "buyer_user_id": TEST_USER_ID,
                "price": 25.0,
            },
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "event_publish_failed"


@pytest.mark.asyncio
async def test_post_purchase_buyer_mismatch(monkeypatch):
    """buyer_user_id ≠ JWT user → 403."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(TEST_USER_ID))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/purchase",
            json={
                "listing_id": str(uuid4()),
                "buyer_user_id": "different-user-id",
                "price": 10.0,
            },
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "forbidden"


@pytest.mark.asyncio
async def test_get_marketplace_all_retries_fail(monkeypatch):
    """Three ConnectErrors → 502, code == upstream_unreachable."""
    from shared_py.web.errors import AppError

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock())

    mock_client = MagicMock()
    mock_client._marketplace_with_retry = AsyncMock(
        side_effect=AppError(
            status_code=502,
            code="upstream_unreachable",
            message="Matching Service unreachable after 3 attempts",
        )
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/marketplace",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "upstream_unreachable"
    # Verify retry method was called exactly once (internal retry is inside the method)
    mock_client._marketplace_with_retry.assert_called_once()


# ═════════════════════════════════════════════════════════════════════════════
# 9.3 X-User-Id header forwarding example tests
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_x_user_id_forwarded_on_aggregation(test_db, monkeypatch):
    """All four gather calls receive the JWT user_id as their user_id argument."""
    ret = Return(
        id="return-xuid-1",
        product_id="product-1",
        user_id=TEST_USER_ID,
        reason="Test",
        media=[],
        status="SUBMITTED",
    )
    test_db.add(ret)
    await test_db.commit()

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(TEST_USER_ID))
    monkeypatch.setattr("app.api.routes.get_db", _mock_db(test_db))

    recorded_user_ids: list[str] = []

    async def capture_grade(return_id, user_id):
        recorded_user_ids.append(("grade", user_id))
        return {"grade": "B"}

    async def capture_decision(return_id, user_id):
        recorded_user_ids.append(("decision", user_id))
        return {"action": "RESELL"}

    async def capture_passport(return_id, user_id):
        recorded_user_ids.append(("passport", user_id))
        return None

    async def capture_matches(return_id, user_id):
        recorded_user_ids.append(("matches", user_id))
        return []

    mock_client = MagicMock()
    mock_client.get_grade = capture_grade
    mock_client.get_decision = capture_decision
    mock_client.get_passport_by_return = capture_passport
    mock_client.get_matches = capture_matches
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/returns/return-xuid-1",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 200
    # All four calls received the correct user_id
    assert len(recorded_user_ids) == 4
    for _service, uid in recorded_user_ids:
        assert uid == TEST_USER_ID


@pytest.mark.asyncio
async def test_x_user_id_forwarded_on_purchase(monkeypatch):
    """Listing lookup call carries the JWT user_id."""
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(TEST_USER_ID))

    listing_id = str(uuid4())
    return_id = str(uuid4())

    recorded: list[tuple[str, str]] = []

    async def capture_get_listing(lid, uid):
        recorded.append((lid, uid))
        return {"return_id": return_id, "product_id": str(uuid4())}

    mock_client = MagicMock()
    mock_client.get_listing = capture_get_listing
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    mock_pub = AsyncMock(return_value=str(uuid4()))
    monkeypatch.setattr("app.api.routes.publish", mock_pub)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/purchase",
            json={
                "listing_id": listing_id,
                "buyer_user_id": TEST_USER_ID,
                "price": 9.99,
            },
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 201
    assert len(recorded) == 1
    assert recorded[0] == (listing_id, TEST_USER_ID)


# ═════════════════════════════════════════════════════════════════════════════
# 10.x Property-based tests (hypothesis)
# ═════════════════════════════════════════════════════════════════════════════

from hypothesis import HealthCheck, given
from hypothesis import settings as h_settings
from hypothesis import strategies as st


# ──────────────────────────────────────────────────────────────────────────────
# Property 1: Partial upstream failure does not fail the aggregated response
# Validates: Requirements 1.3
# Feature: gateway-aggregation, Property 1: partial upstream failure returns 200
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@given(
    failing=st.frozensets(
        st.sampled_from(["grading", "lifecycle", "passport", "matching"]),
        min_size=1,
    )
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_partial_upstream_failure_returns_200(failing, test_db, monkeypatch):
    """
    Property 1: Partial upstream failure does not fail the aggregated response.

    For any non-empty subset of upstream services that fail, GET /returns/{id}
    still returns HTTP 200, with failed fields as null/[] and available fields non-null.
    """
    ret_id = str(uuid4())
    ret = Return(
        id=ret_id,
        product_id="product-pbt-1",
        user_id=TEST_USER_ID,
        reason="PBT test",
        media=[],
        status="SUBMITTED",
    )
    test_db.add(ret)
    await test_db.commit()

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(TEST_USER_ID))
    monkeypatch.setattr("app.api.routes.get_db", _mock_db(test_db))

    # The four ServiceClient methods already swallow 404/ConnectError internally
    # (via _safe_call) and return None/[]. Since we mock those methods directly,
    # we simulate that behavior: a "failing" service returns None/[] rather than
    # raising — exactly what the real method does after swallowing the error.
    async def grade_impl(return_id, user_id):
        if "grading" in failing:
            return None
        return {"grade": "A"}

    async def decision_impl(return_id, user_id):
        if "lifecycle" in failing:
            return None
        return {"action": "RESELL"}

    async def passport_impl(return_id, user_id):
        if "passport" in failing:
            return None
        return {"passport_id": "pp-1"}

    async def matches_impl(return_id, user_id):
        if "matching" in failing:
            return []
        return [{"buyer": "b1"}]

    mock_client = MagicMock()
    mock_client.get_grade = grade_impl
    mock_client.get_decision = decision_impl
    mock_client.get_passport_by_return = passport_impl
    mock_client.get_matches = matches_impl
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/returns/{ret_id}",
            headers={"Authorization": FAKE_TOKEN},
        )

    # The response must be 200 regardless of which services failed
    assert response.status_code == 200
    data = response.json()

    # Failed services → null or []
    if "grading" in failing:
        assert data["grade"] is None
    else:
        assert data["grade"] is not None

    if "lifecycle" in failing:
        assert data["decision"] is None
    else:
        assert data["decision"] is not None

    if "passport" in failing:
        assert data["passport"] is None
    else:
        assert data["passport"] is not None

    if "matching" in failing:
        assert data["matches"] == []
    else:
        assert data["matches"] != []

    # Clean up the seeded return for next iteration
    await test_db.delete(await test_db.get(Return, ret_id))
    await test_db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Property 2: X-User-Id is forwarded to every upstream call on authenticated routes
# Validates: Requirements 1.5, 2.4, 3.5, 6.3
# Feature: gateway-aggregation, Property 2: X-User-Id forwarded on all routes
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@given(
    user_id=st.text(
        min_size=1,
        max_size=64,
        alphabet=st.characters(whitelist_categories=("L", "N", "Nd")),
    )
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_x_user_id_forwarded_aggregation(user_id, test_db, monkeypatch):
    """
    Property 2: X-User-Id is forwarded to every upstream call.

    For any valid user_id string from a verified JWT, all four gather calls
    receive the same user_id argument.
    """
    ret_id = str(uuid4())
    ret = Return(
        id=ret_id,
        product_id="product-pbt-2",
        user_id=user_id,
        reason="PBT",
        media=[],
        status="SUBMITTED",
    )
    test_db.add(ret)
    await test_db.commit()

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(user_id))
    monkeypatch.setattr("app.api.routes.get_db", _mock_db(test_db))

    received: list[str] = []

    async def record(return_id, uid):
        received.append(uid)
        return None

    async def record_matches(return_id, uid):
        received.append(uid)
        return []

    mock_client = MagicMock()
    mock_client.get_grade = record
    mock_client.get_decision = record
    mock_client.get_passport_by_return = record
    mock_client.get_matches = record_matches
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/returns/{ret_id}",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 200
    assert len(received) == 4
    for uid in received:
        assert uid == user_id

    # Cleanup
    await test_db.delete(await test_db.get(Return, ret_id))
    await test_db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Property 3: Missing Return produces 404 for any unknown return_id
# Validates: Requirements 1.4
# Feature: gateway-aggregation, Property 3: unknown return_id always 404
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@given(return_id=st.uuids().map(str))
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_unknown_return_id_returns_404(return_id, test_db, monkeypatch):
    """
    Property 3: Missing Return produces 404 for any unknown return_id.

    The DB is always empty (fresh per invocation), so any UUID maps to a
    missing Return → 404 + ErrorEnvelope. No upstream calls are made.
    """
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(TEST_USER_ID))
    monkeypatch.setattr("app.api.routes.get_db", _mock_db(test_db))

    mock_client = MagicMock()
    mock_client.get_grade = AsyncMock()
    mock_client.get_decision = AsyncMock()
    mock_client.get_passport_by_return = AsyncMock()
    mock_client.get_matches = AsyncMock()
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/returns/{return_id}",
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 404

    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "correlation_id" in body["error"]

    # No upstream calls should have been made
    mock_client.get_grade.assert_not_called()
    mock_client.get_decision.assert_not_called()
    mock_client.get_passport_by_return.assert_not_called()
    mock_client.get_matches.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# Property 4: PurchaseCompleted event is a faithful round-trip of the request inputs
# Validates: Requirements 4.1, 4.5, 4.7, 8.5
# Feature: gateway-aggregation, Property 4: PurchaseCompleted round-trip
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@given(
    listing_id=st.uuids().map(str),
    price=st.floats(
        min_value=0.01,
        max_value=10_000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
    user_id=st.uuids().map(str),
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_purchase_completed_round_trip(listing_id, price, user_id, monkeypatch):
    """
    Property 4: PurchaseCompleted event is a faithful round-trip of the request inputs.

    For any valid (listing_id, price, user_id):
    - The published event has event_type == "PurchaseCompleted"
    - event data contains listing_id, buyer_user_id == user_id, price unchanged
    - HTTP 201 response body contains the same fields plus event_id, correlation_id
    """
    return_id = str(uuid4())
    product_id = str(uuid4())
    event_id = str(uuid4())

    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(user_id))

    mock_client = MagicMock()
    mock_client.get_listing = AsyncMock(
        return_value={"return_id": return_id, "product_id": product_id}
    )
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    captured_publish_kwargs: dict = {}

    async def capture_publish(**kwargs):
        captured_publish_kwargs.update(kwargs)
        return event_id

    monkeypatch.setattr("app.api.routes.publish", capture_publish)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/purchase",
            json={
                "listing_id": listing_id,
                "buyer_user_id": user_id,
                "price": price,
            },
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 201

    # Assert publish was called with correct event type and correlation_id
    assert captured_publish_kwargs["event_type"] == "PurchaseCompleted"
    assert captured_publish_kwargs["correlation_id"] == return_id

    # Assert event data fields are faithful round-trips
    pub_data = captured_publish_kwargs["data"]
    assert pub_data["listing_id"] == listing_id
    assert pub_data["buyer_user_id"] == user_id  # JWT-derived, not request body
    assert pub_data["price"] == price

    # Assert HTTP response body is also a faithful round-trip
    resp_data = response.json()
    assert resp_data["listing_id"] == listing_id
    assert resp_data["buyer_user_id"] == user_id
    assert resp_data["price"] == price
    assert resp_data["event_id"] == event_id
    assert resp_data["correlation_id"] == return_id
    assert resp_data["event_id"]  # non-empty


# ──────────────────────────────────────────────────────────────────────────────
# Property 5: Marketplace proxy always appends fixed channel and status filters
# Validates: Requirements 5.1, 5.2, 5.4
# Feature: gateway-aggregation, Property 5: marketplace fixed filters
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@given(
    category=st.one_of(st.none(), st.text(min_size=1, max_size=32)),
    limit=st.one_of(st.none(), st.integers(min_value=1, max_value=100)),
    offset=st.one_of(st.none(), st.integers(min_value=0, max_value=1000)),
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_marketplace_fixed_filters(category, limit, offset, monkeypatch):
    """
    Property 5: Marketplace proxy always appends fixed channel and status filters.

    For any combination of optional query params, the outbound params dict
    always contains channel=MARKETPLACE and status=ACTIVE, plus correct
    defaults for limit/offset when not provided.
    """
    monkeypatch.setattr("app.api.routes.get_current_user_id", _auth_mock(TEST_USER_ID))

    captured_params: dict = {}

    async def capture_marketplace(params, uid):
        captured_params.update(params)
        return {"items": [], "total": 0}

    mock_client = MagicMock()
    mock_client._marketplace_with_retry = capture_marketplace
    monkeypatch.setattr("app.api.routes.service_client", mock_client)

    query_params: dict = {}
    if category is not None:
        query_params["category"] = category
    if limit is not None:
        query_params["limit"] = limit
    if offset is not None:
        query_params["offset"] = offset

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/marketplace",
            params=query_params,
            headers={"Authorization": FAKE_TOKEN},
        )

    assert response.status_code == 200

    # Fixed filters always present
    assert captured_params["channel"] == "MARKETPLACE"
    assert captured_params["status"] == "ACTIVE"

    # Defaults applied when not provided
    assert captured_params["limit"] == (limit if limit is not None else 20)
    assert captured_params["offset"] == (offset if offset is not None else 0)

    # Category forwarded only when provided
    if category is not None:
        assert captured_params["category"] == category
    else:
        assert "category" not in captured_params
