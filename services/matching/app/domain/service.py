"""
Hyperlocal Matching business logic — pure Python, no FastAPI imports.

Pipeline (triggered by HyperlocalMatchRequested event):
  1. Fetch buyer candidates from User Service via REST
  2. Score each candidate using Haversine distance + interest overlap
  3. Call AI for match rationale on top candidates
  4. If best score > threshold → persist Match, emit MatchFound
  5. Else → emit NoMatchFound
  6. In both cases → create Listing (HYPERLOCAL or MARKETPLACE), emit ProductListed
"""

import math
import uuid
from typing import Optional

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared_py.ai import ai_client
from shared_py.config import get_logger
from shared_py.schemas.enums import ListingChannel, ListingStatus

from app.domain.models import Listing, Match, MatchRequest
from app.domain.schemas import UserCandidate, UserCandidatesListResponse

logger = get_logger(__name__)

# Maximum number of candidates to request from User Service
_CANDIDATES_LIMIT = 100

# Number of top-scoring candidates that get an AI rationale
_TOP_N_FOR_AI = 3


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Return the great-circle distance in kilometres between two lat/lng points.

    Uses the Haversine formula.  Inputs are in decimal degrees.
    """
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_score(
    distance_km: float,
    radius_km: float,
    buyer_interests: list[str],
    product_category: str,
) -> float:
    """
    Compute a match score in [0, 100].

    Components:
      - Proximity score (70 %): linear decay from 100 at distance=0 to 0 at distance=radius_km
      - Interest score  (30 %): 100 if product_category appears in buyer_interests, else 0
    """
    if distance_km > radius_km:
        return 0.0

    proximity = max(0.0, 100.0 * (1.0 - distance_km / radius_km))
    interest = 100.0 if product_category.lower() in [i.lower() for i in buyer_interests] else 0.0
    return round(0.70 * proximity + 0.30 * interest, 2)


def _estimated_savings(distance_km: float) -> float:
    """
    Estimate logistics / CO₂ savings in USD based on distance.

    Simple model: every 10 km of avoided shipping saves ~$2.
    """
    return round(max(0.0, (50.0 - distance_km) * 0.4), 2)


class MatchingService:
    """Business logic for the hyperlocal buyer-matching pipeline."""

    def __init__(
        self,
        db: AsyncSession,
        user_service_url: str,
        radius_km: float,
        score_threshold: float,
    ):
        self.db = db
        self.user_service_url = user_service_url.rstrip("/")
        self.radius_km = radius_km
        self.score_threshold = score_threshold

    # ─────────────────────────────────────────────────────────────────────────
    # Main pipeline entry-point
    # ─────────────────────────────────────────────────────────────────────────

    async def run_matching(
        self,
        *,
        return_id: str,
        product_id: str,
        category: str,
        lat: float,
        lng: float,
        passport_id: str,
        price: float,
        correlation_id: Optional[str] = None,
    ) -> tuple[Optional[Match], Listing]:
        """
        Execute the full matching pipeline for a newly passported product.

        Idempotent: if a MatchRequest already exists for return_id the method
        returns the existing best match + listing without re-running the pipeline.

        Returns:
            (best_match_or_None, listing)
        """
        corr = correlation_id or return_id

        # ── Idempotency check ────────────────────────────────────────────────
        existing_req = await self._get_request_by_return_id(return_id)
        if existing_req is not None:
            logger.info(
                "match_request_already_exists_skipping",
                extra={"return_id": return_id, "correlation_id": corr},
            )
            best_match = await self._get_best_match(existing_req.id)
            listing = await self._get_listing_by_product(product_id)
            return best_match, listing  # type: ignore[return-value]

        # ── Create MatchRequest ──────────────────────────────────────────────
        match_request = MatchRequest(
            id=str(uuid.uuid4()),
            return_id=return_id,
            product_id=product_id,
            category=category,
            lat=lat,
            lng=lng,
            status="PENDING",
        )
        self.db.add(match_request)
        await self.db.flush()

        # ── Fetch candidates from User Service ────────────────────────────────
        candidates = await self._fetch_candidates(category, lat, lng, corr)

        # ── Score candidates ──────────────────────────────────────────────────
        scored: list[tuple[UserCandidate, float, float]] = []
        for candidate in candidates:
            dist = _haversine_km(lat, lng, candidate.lat, candidate.lng)
            score = _compute_score(dist, self.radius_km, candidate.interests, category)
            if score > 0:
                scored.append((candidate, score, dist))

        scored.sort(key=lambda t: t[1], reverse=True)
        top_candidates = scored[:_TOP_N_FOR_AI]

        # ── Determine best match ──────────────────────────────────────────────
        best_match: Optional[Match] = None

        if top_candidates and top_candidates[0][1] > self.score_threshold * 100:
            best_candidate, best_score, best_dist = top_candidates[0]

            # AI rationale
            rationale_result = await ai_client.match_rationale(
                buyer_distance_km=best_dist,
                buyer_interests=best_candidate.interests,
                product_category=category,
                match_score=best_score / 100.0,
                correlation_id=corr,
            )

            best_match = Match(
                id=str(uuid.uuid4()),
                match_request_id=match_request.id,
                buyer_user_id=best_candidate.id,
                score=best_score,
                estimated_savings=_estimated_savings(best_dist),
                distance_km=round(best_dist, 3),
                rationale=rationale_result.text,
            )
            self.db.add(best_match)
            match_request.status = "MATCHED"
            channel = ListingChannel.HYPERLOCAL
        else:
            match_request.status = "UNMATCHED"
            channel = ListingChannel.MARKETPLACE

        # ── Create Listing ────────────────────────────────────────────────────
        listing = Listing(
            id=str(uuid.uuid4()),
            product_id=product_id,
            passport_id=passport_id,
            price=price,
            channel=channel.value,
            status=ListingStatus.ACTIVE.value,
        )
        self.db.add(listing)
        await self.db.commit()

        if best_match:
            await self.db.refresh(best_match)
        await self.db.refresh(listing)
        await self.db.refresh(match_request)

        logger.info(
            "matching_complete",
            extra={
                "return_id": return_id,
                "match_found": best_match is not None,
                "channel": channel.value,
                "listing_id": listing.id,
                "correlation_id": corr,
            },
        )

        return best_match, listing

    # ─────────────────────────────────────────────────────────────────────────
    # REST helper — User Service candidate fetch
    # ─────────────────────────────────────────────────────────────────────────

    async def _fetch_candidates(
        self,
        category: str,
        lat: float,
        lng: float,
        correlation_id: str,
    ) -> list[UserCandidate]:
        """
        Call GET /users/candidates on the User Service.

        Returns an empty list on any error so the pipeline degrades gracefully
        and routes to MARKETPLACE instead of hard-failing.
        """
        url = f"{self.user_service_url}/users/candidates"
        params = {
            "category": category,
            "lat": lat,
            "lng": lng,
            "radius_km": self.radius_km,
            "limit": _CANDIDATES_LIMIT,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = UserCandidatesListResponse.model_validate(response.json())
                logger.info(
                    "candidates_fetched",
                    extra={
                        "count": payload.total,
                        "correlation_id": correlation_id,
                    },
                )
                return payload.items
        except Exception as exc:
            logger.warning(
                "candidates_fetch_failed_fallback_to_marketplace",
                extra={"error": str(exc), "correlation_id": correlation_id},
            )
            return []

    # ─────────────────────────────────────────────────────────────────────────
    # Query helpers
    # ─────────────────────────────────────────────────────────────────────────

    async def _get_request_by_return_id(
        self, return_id: str
    ) -> Optional[MatchRequest]:
        result = await self.db.execute(
            select(MatchRequest).where(MatchRequest.return_id == return_id)
        )
        return result.scalar_one_or_none()

    async def _get_best_match(
        self, match_request_id: str
    ) -> Optional[Match]:
        result = await self.db.execute(
            select(Match)
            .where(Match.match_request_id == match_request_id)
            .order_by(Match.score.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_listing_by_product(self, product_id: str) -> Optional[Listing]:
        result = await self.db.execute(
            select(Listing)
            .where(Listing.product_id == product_id)
            .order_by(Listing.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ─────────────────────────────────────────────────────────────────────────
    # Read methods (used by REST routes)
    # ─────────────────────────────────────────────────────────────────────────

    async def get_matches_for_return(
        self,
        return_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Match], int]:
        """Return (matches, total) for a given return_id."""
        req_result = await self.db.execute(
            select(MatchRequest).where(MatchRequest.return_id == return_id)
        )
        req = req_result.scalar_one_or_none()
        if req is None:
            return [], 0

        count_result = await self.db.execute(
            select(func.count(Match.id)).where(
                Match.match_request_id == req.id
            )
        )
        total = count_result.scalar_one()

        matches_result = await self.db.execute(
            select(Match)
            .where(Match.match_request_id == req.id)
            .order_by(Match.score.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(matches_result.scalars().all()), total

    async def get_match_by_id(self, match_id: str) -> Optional[Match]:
        result = await self.db.execute(
            select(Match).where(Match.id == match_id)
        )
        return result.scalar_one_or_none()

    async def list_listings(
        self,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Listing], int]:
        """Return (listings, total) with optional filters."""
        filters = []
        if channel:
            filters.append(Listing.channel == channel)
        if status:
            filters.append(Listing.status == status)
        # NOTE: category is not stored on Listing; filter via joined MatchRequest
        # For now, category filtering is deferred (the field is not on Listing).
        # Clients can filter by channel/status; full category search is P2-B3 scope.

        count_stmt = select(func.count(Listing.id))
        list_stmt = select(Listing).order_by(Listing.created_at.desc())
        for f in filters:
            count_stmt = count_stmt.where(f)
            list_stmt = list_stmt.where(f)

        total = (await self.db.execute(count_stmt)).scalar_one()
        items = (
            await self.db.execute(list_stmt.limit(limit).offset(offset))
        ).scalars().all()

        return list(items), total

    async def get_listing_by_id(self, listing_id: str) -> Optional[Listing]:
        result = await self.db.execute(
            select(Listing).where(Listing.id == listing_id)
        )
        return result.scalar_one_or_none()
