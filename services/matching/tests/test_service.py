"""
Integration-level tests for MatchingService using an in-memory SQLite DB
and a mocked User Service HTTP call.
"""

import pytest
import respx
from httpx import Response

from app.domain.service import MatchingService

_USER_SERVICE_URL = "http://user-mock:8001"

# A candidate very close to origin → will match
_NEARBY_CANDIDATE = {
    "id": "buyer-001",
    "display_name": "Alice",
    "lat": 37.7750,
    "lng": -122.4195,
    "interests": ["electronics"],
}

# A candidate far away → won't match
_FAR_CANDIDATE = {
    "id": "buyer-002",
    "display_name": "Bob",
    "lat": 51.507,
    "lng": -0.128,
    "interests": ["clothing"],
}

_CANDIDATES_RESPONSE = {
    "items": [_NEARBY_CANDIDATE],
    "total": 1,
}

_NO_CANDIDATES_RESPONSE = {"items": [], "total": 0}


def _make_service(db, radius_km=50.0, threshold=0.4):
    return MatchingService(
        db=db,
        user_service_url=_USER_SERVICE_URL,
        radius_km=radius_km,
        score_threshold=threshold,
    )


@pytest.mark.asyncio
@respx.mock
async def test_match_found_creates_match_and_hyperlocal_listing(db_session):
    """When a nearby buyer exists, run_matching creates a Match and HYPERLOCAL listing."""
    respx.get(f"{_USER_SERVICE_URL}/users/candidates").mock(
        return_value=Response(200, json=_CANDIDATES_RESPONSE)
    )

    service = _make_service(db_session)
    best_match, listing = await service.run_matching(
        return_id="ret-001",
        product_id="prod-001",
        category="electronics",
        lat=37.775,
        lng=-122.419,
        passport_id="pass-001",
        price=99.99,
        correlation_id="ret-001",
    )

    assert best_match is not None
    assert best_match.buyer_user_id == "buyer-001"
    assert best_match.score > 0
    assert listing.channel == "HYPERLOCAL"
    assert listing.status == "ACTIVE"


@pytest.mark.asyncio
@respx.mock
async def test_no_candidates_creates_marketplace_listing(db_session):
    """When no candidates are returned, listing channel is MARKETPLACE."""
    respx.get(f"{_USER_SERVICE_URL}/users/candidates").mock(
        return_value=Response(200, json=_NO_CANDIDATES_RESPONSE)
    )

    service = _make_service(db_session)
    best_match, listing = await service.run_matching(
        return_id="ret-002",
        product_id="prod-002",
        category="electronics",
        lat=37.775,
        lng=-122.419,
        passport_id="pass-002",
        price=49.99,
        correlation_id="ret-002",
    )

    assert best_match is None
    assert listing.channel == "MARKETPLACE"


@pytest.mark.asyncio
@respx.mock
async def test_idempotency_skips_reprocessing(db_session):
    """Calling run_matching twice for the same return_id returns existing records."""
    respx.get(f"{_USER_SERVICE_URL}/users/candidates").mock(
        return_value=Response(200, json=_CANDIDATES_RESPONSE)
    )

    service = _make_service(db_session)

    match1, listing1 = await service.run_matching(
        return_id="ret-003",
        product_id="prod-003",
        category="electronics",
        lat=37.775,
        lng=-122.419,
        passport_id="pass-003",
        price=75.0,
        correlation_id="ret-003",
    )

    # Second call — User Service should NOT be called again
    respx.get(f"{_USER_SERVICE_URL}/users/candidates").mock(
        side_effect=Exception("should not be called")
    )
    match2, listing2 = await service.run_matching(
        return_id="ret-003",
        product_id="prod-003",
        category="electronics",
        lat=37.775,
        lng=-122.419,
        passport_id="pass-003",
        price=75.0,
        correlation_id="ret-003",
    )

    assert listing1.id == listing2.id


@pytest.mark.asyncio
@respx.mock
async def test_user_service_error_falls_back_to_marketplace(db_session):
    """If User Service is unavailable, matching falls back to MARKETPLACE gracefully."""
    respx.get(f"{_USER_SERVICE_URL}/users/candidates").mock(
        return_value=Response(503, json={"detail": "service unavailable"})
    )

    service = _make_service(db_session)
    best_match, listing = await service.run_matching(
        return_id="ret-004",
        product_id="prod-004",
        category="electronics",
        lat=37.775,
        lng=-122.419,
        passport_id="pass-004",
        price=30.0,
        correlation_id="ret-004",
    )

    assert best_match is None
    assert listing.channel == "MARKETPLACE"


@pytest.mark.asyncio
@respx.mock
async def test_get_matches_for_return(db_session):
    """get_matches_for_return returns the match we created."""
    respx.get(f"{_USER_SERVICE_URL}/users/candidates").mock(
        return_value=Response(200, json=_CANDIDATES_RESPONSE)
    )

    service = _make_service(db_session)
    await service.run_matching(
        return_id="ret-005",
        product_id="prod-005",
        category="electronics",
        lat=37.775,
        lng=-122.419,
        passport_id="pass-005",
        price=60.0,
        correlation_id="ret-005",
    )

    items, total = await service.get_matches_for_return("ret-005")
    assert total == 1
    assert items[0].buyer_user_id == "buyer-001"


@pytest.mark.asyncio
@respx.mock
async def test_list_listings_filter_by_channel(db_session):
    """list_listings correctly filters by channel."""
    respx.get(f"{_USER_SERVICE_URL}/users/candidates").mock(
        return_value=Response(200, json=_NO_CANDIDATES_RESPONSE)
    )

    service = _make_service(db_session)
    await service.run_matching(
        return_id="ret-006",
        product_id="prod-006",
        category="electronics",
        lat=0.0,
        lng=0.0,
        passport_id="pass-006",
        price=20.0,
    )

    marketplace_items, total = await service.list_listings(channel="MARKETPLACE")
    assert total >= 1

    hyperlocal_items, h_total = await service.list_listings(channel="HYPERLOCAL")
    assert h_total == 0
