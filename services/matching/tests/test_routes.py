"""
HTTP route tests for the Hyperlocal Matching Service.

Uses a test client with in-memory SQLite and pre-seeded records.
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.domain.models import Listing, Match, MatchRequest


def _utcnow():
    return datetime.now(timezone.utc)


async def _seed_match_request(db, return_id="ret-r1", product_id="prod-r1"):
    req = MatchRequest(
        id=str(uuid.uuid4()),
        return_id=return_id,
        product_id=product_id,
        category="electronics",
        lat=37.775,
        lng=-122.419,
        status="MATCHED",
        created_at=_utcnow(),
    )
    db.add(req)
    await db.flush()
    return req


async def _seed_match(db, match_request_id):
    m = Match(
        id=str(uuid.uuid4()),
        match_request_id=match_request_id,
        buyer_user_id="buyer-seed",
        score=85.0,
        estimated_savings=12.0,
        distance_km=5.2,
        rationale="Good match — nearby buyer interested in electronics.",
        created_at=_utcnow(),
    )
    db.add(m)
    await db.flush()
    return m


async def _seed_listing(db, product_id="prod-r1", channel="HYPERLOCAL"):
    lst = Listing(
        id=str(uuid.uuid4()),
        product_id=product_id,
        passport_id="pass-r1",
        price=79.99,
        channel=channel,
        status="ACTIVE",
        created_at=_utcnow(),
    )
    db.add(lst)
    await db.flush()
    return lst


@pytest.mark.asyncio
async def test_get_matches_by_return_id(client, db_session):
    req = await _seed_match_request(db_session)
    match = await _seed_match(db_session, req.id)
    await db_session.commit()

    resp = await client.get("/matches", params={"return_id": "ret-r1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == match.id


@pytest.mark.asyncio
async def test_get_match_by_id(client, db_session):
    req = await _seed_match_request(db_session, return_id="ret-r2", product_id="prod-r2")
    match = await _seed_match(db_session, req.id)
    await db_session.commit()

    resp = await client.get(f"/matches/{match.id}")
    assert resp.status_code == 200
    assert resp.json()["buyer_user_id"] == "buyer-seed"


@pytest.mark.asyncio
async def test_get_match_by_id_not_found(client):
    resp = await client.get("/matches/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_listings(client, db_session):
    listing = await _seed_listing(db_session)
    await db_session.commit()

    resp = await client.get("/listings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    ids = [item["id"] for item in data["items"]]
    assert listing.id in ids


@pytest.mark.asyncio
async def test_list_listings_filter_channel(client, db_session):
    await _seed_listing(db_session, product_id="p-hyper", channel="HYPERLOCAL")
    await _seed_listing(db_session, product_id="p-market", channel="MARKETPLACE")
    await db_session.commit()

    resp = await client.get("/listings", params={"channel": "HYPERLOCAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["channel"] == "HYPERLOCAL" for item in data["items"])


@pytest.mark.asyncio
async def test_get_listing_by_id(client, db_session):
    listing = await _seed_listing(db_session, product_id="prod-lid")
    await db_session.commit()

    resp = await client.get(f"/listings/{listing.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == listing.id


@pytest.mark.asyncio
async def test_get_listing_not_found(client):
    resp = await client.get("/listings/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_matches_empty_for_unknown_return(client):
    resp = await client.get("/matches", params={"return_id": "does-not-exist"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
