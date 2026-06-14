"""
HTTP client for calling upstream services.

Gateway proxies calls to User, Grading, Lifecycle, Passport, Matching, Sustainability services.
Uses httpx.AsyncClient for async HTTP calls.
"""

import asyncio
import logging
from typing import Any, Optional

import httpx

from shared_py.web.errors import AppError

from app.config import settings

logger = logging.getLogger(__name__)


class ServiceClient:
    """
    HTTP client for calling upstream microservices.

    Handles:
    - Async HTTP calls with httpx
    - Error handling and status code mapping
    - Header propagation (correlation_id, user_id)
    """

    def __init__(self):
        """Initialize HTTP client with explicit timeout configuration."""
        # Set explicit timeouts to prevent hanging requests
        # connect: 5s, read: 30s, write: 10s, pool: 5s
        timeout = httpx.Timeout(
            connect=5.0,
            read=30.0,
            write=10.0,
            pool=5.0,
        )
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def call_service(
        self,
        method: str,
        url: str,
        *,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Call an upstream service and return JSON response.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to call
            json: Request body (for POST/PATCH)
            params: Query parameters
            headers: Additional headers

        Returns:
            JSON response as dict

        Raises:
            AppError with appropriate status code if call fails
        """
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers or {},
            )

            # For 2xx responses, return JSON
            if 200 <= response.status_code < 300:
                return response.json()

            # For error responses, propagate the error
            error_data = response.json() if response.text else {}
            raise AppError(
                status_code=response.status_code,
                code=error_data.get("error", {}).get("code", "upstream_error"),
                message=error_data.get("error", {}).get(
                    "message", f"Upstream service error: {response.status_code}"
                ),
            )

        except httpx.RequestError as e:
            raise AppError(
                status_code=502,
                code="upstream_unreachable",
                message=f"Could not reach upstream service: {e}",
            ) from e

    async def proxy_to_user_service(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Proxy a request to the User Service.

        Args:
            method: HTTP method
            path: Path (e.g., "/auth/register")
            json: Request body
            headers: Headers to forward

        Returns:
            JSON response from User Service
        """
        url = f"{settings.user_service_url}{path}"
        return await self.call_service(method, url, json=json, headers=headers)

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    async def _safe_call(self, coro, *, default):
        """
        Await coro; return default on AppError(404) or httpx.RequestError.
        All other exceptions propagate.

        Used by the four partial-availability aggregation methods so that a
        single upstream failure degrades gracefully instead of cancelling
        the entire asyncio.gather.
        """
        try:
            return await coro
        except AppError as exc:
            if exc.status_code == 404:
                return default
            raise
        except httpx.RequestError:
            return default

    async def _marketplace_with_retry(self, params: dict[str, Any], user_id: str) -> dict[str, Any]:
        """
        Attempt GET /listings?channel=MARKETPLACE&status=ACTIVE up to 3 times.

        Back-off: attempt 1→0 s, attempt 2→1 s, attempt 3→2 s.
        Logs each failure at WARNING with correlation_id.
        Raises AppError(502, "upstream_unreachable") after all retries exhausted.
        """
        delays = [0, 1, 2]
        last_error: Exception | None = None
        correlation_id = str(params.get("correlation_id", ""))

        for attempt, delay in enumerate(delays, start=1):
            if delay > 0:
                await asyncio.sleep(delay)
            try:
                url = f"{settings.matching_service_url}/listings"
                headers = {
                    "X-User-Id": user_id,
                }
                if correlation_id:
                    headers["X-Correlation-Id"] = correlation_id

                response = await self.client.get(url, params=params, headers=headers)
                if 200 <= response.status_code < 300:
                    return response.json()

                error_data = response.json() if response.text else {}
                raise AppError(
                    status_code=response.status_code,
                    code=error_data.get("error", {}).get("code", "upstream_error"),
                    message=error_data.get("error", {}).get(
                        "message", f"Upstream service error: {response.status_code}"
                    ),
                )
            except (httpx.RequestError, AppError) as exc:
                last_error = exc
                logger.warning(
                    "marketplace_retry_failed",
                    extra={
                        "attempt": attempt,
                        "correlation_id": correlation_id,
                        "error": str(exc),
                    },
                )

        raise AppError(
            status_code=502,
            code="upstream_unreachable",
            message=f"Matching Service unreachable after {len(delays)} attempts: {last_error}",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Partial-availability methods (used in BFF aggregation — swallow 404/errors)
    # ─────────────────────────────────────────────────────────────────────────

    async def get_grade(self, return_id: str, user_id: str) -> dict[str, Any] | None:
        """
        Fetch grade for a return from Grading Service.

        Returns the first result or None on 404/ConnectError.
        """
        url = f"{settings.grading_service_url}/grades"
        headers = {
            "X-User-Id": user_id,
            "X-Correlation-Id": return_id,
        }
        coro = self.call_service("GET", url, params={"return_id": return_id}, headers=headers)
        result = await self._safe_call(coro, default=None)
        if result is None:
            return None
        # Grading service returns list or dict; normalise to first item
        if isinstance(result, list):
            return result[0] if result else None
        return result

    async def get_decision(self, return_id: str, user_id: str) -> dict[str, Any] | None:
        """
        Fetch lifecycle decision for a return from Lifecycle Service.

        Returns the first result or None on 404/ConnectError.
        """
        url = f"{settings.lifecycle_service_url}/decisions"
        headers = {
            "X-User-Id": user_id,
            "X-Correlation-Id": return_id,
        }
        coro = self.call_service("GET", url, params={"return_id": return_id}, headers=headers)
        result = await self._safe_call(coro, default=None)
        if result is None:
            return None
        if isinstance(result, list):
            return result[0] if result else None
        return result

    async def get_passport_by_return(self, return_id: str, user_id: str) -> dict[str, Any] | None:
        """
        Fetch passport by return_id from Passport Service.

        Returns passport dict or None on 404/ConnectError.
        """
        url = f"{settings.passport_service_url}/passports/by-return/{return_id}"
        headers = {
            "X-User-Id": user_id,
            "X-Correlation-Id": return_id,
        }
        coro = self.call_service("GET", url, headers=headers)
        return await self._safe_call(coro, default=None)

    async def get_matches(self, return_id: str, user_id: str) -> list[dict[str, Any]]:
        """
        Fetch matches for a return from Matching Service.

        Returns list of matches or [] on 404/ConnectError.
        """
        url = f"{settings.matching_service_url}/matches"
        headers = {
            "X-User-Id": user_id,
            "X-Correlation-Id": return_id,
        }
        coro = self.call_service("GET", url, params={"return_id": return_id}, headers=headers)
        result = await self._safe_call(coro, default=[])
        if result is None:
            return []
        if isinstance(result, list):
            return result
        # Might be a paginated response {"items": [...]}
        if isinstance(result, dict) and "items" in result:
            return result["items"]
        return []

    # ─────────────────────────────────────────────────────────────────────────
    # Strict-proxy methods (raise on error — used for direct proxy routes)
    # ─────────────────────────────────────────────────────────────────────────

    async def get_passport(self, passport_id: str, user_id: str) -> dict[str, Any]:
        """
        Fetch passport by passport_id from Passport Service (strict proxy).

        Raises AppError(404) on 404, AppError(502) on ConnectError.
        """
        url = f"{settings.passport_service_url}/passports/{passport_id}"
        headers = {
            "X-User-Id": user_id,
            "X-Correlation-Id": passport_id,
        }
        try:
            return await self.call_service("GET", url, headers=headers)
        except AppError:
            raise
        except httpx.RequestError as e:
            raise AppError(
                status_code=502,
                code="upstream_unreachable",
                message=f"Passport Service unreachable: {e}",
            ) from e

    async def get_matches_for_return(self, return_id: str, user_id: str) -> dict[str, Any]:
        """
        Fetch matches for a return from Matching Service (strict proxy).

        Raises AppError on errors.
        """
        url = f"{settings.matching_service_url}/matches"
        headers = {
            "X-User-Id": user_id,
            "X-Correlation-Id": return_id,
        }
        try:
            return await self.call_service(
                "GET", url, params={"return_id": return_id}, headers=headers
            )
        except AppError:
            raise
        except httpx.RequestError as e:
            raise AppError(
                status_code=502,
                code="upstream_unreachable",
                message=f"Matching Service unreachable: {e}",
            ) from e

    async def get_listing(self, listing_id: str, user_id: str) -> dict[str, Any]:
        """
        Fetch a listing by listing_id from Matching Service (strict proxy).

        Raises AppError(404) on 404, AppError(502) on ConnectError.
        """
        url = f"{settings.matching_service_url}/listings/{listing_id}"
        headers = {
            "X-User-Id": user_id,
            "X-Correlation-Id": listing_id,
        }
        try:
            return await self.call_service("GET", url, headers=headers)
        except AppError:
            raise
        except httpx.RequestError as e:
            raise AppError(
                status_code=502,
                code="upstream_unreachable",
                message=f"Matching Service unreachable: {e}",
            ) from e

    # ─────────────────────────────────────────────────────────────────────────
    # Sustainability Dashboard methods (BFF read-model for dashboard)
    # ─────────────────────────────────────────────────────────────────────────

    async def get_sustainability_metrics(
        self,
        user_id: Optional[str],
        requesting_user_id: str,
    ) -> dict[str, Any]:
        """
        Fetch aggregated sustainability metrics from Sustainability Service.

        Args:
            user_id: Optional filter by user_id
            requesting_user_id: User making the request (for auth)

        Returns:
            Metrics dict with co2_avoided_kg, waste_diverted_kg, value_recovered, green_credits

        Raises:
            AppError(502) on ConnectError
        """
        url = f"{settings.sustainability_service_url}/sustainability/metrics"
        headers = {
            "X-User-Id": requesting_user_id,
        }
        params = {}
        if user_id is not None:
            params["user_id"] = user_id

        try:
            return await self.call_service("GET", url, params=params, headers=headers)
        except AppError:
            raise
        except httpx.RequestError as e:
            raise AppError(
                status_code=502,
                code="upstream_unreachable",
                message=f"Sustainability Service unreachable: {e}",
            ) from e

    async def list_sustainability_records(
        self,
        user_id: Optional[str],
        return_id: Optional[str],
        limit: int,
        offset: int,
        requesting_user_id: str,
    ) -> dict[str, Any]:
        """
        Fetch sustainability records list from Sustainability Service.

        Args:
            user_id: Optional filter by user_id
            return_id: Optional filter by return_id
            limit: Items per page
            offset: Offset from start
            requesting_user_id: User making the request (for auth)

        Returns:
            Paginated response with items[] and total

        Raises:
            AppError(502) on ConnectError
        """
        url = f"{settings.sustainability_service_url}/sustainability"
        headers = {
            "X-User-Id": requesting_user_id,
        }
        params = {
            "limit": limit,
            "offset": offset,
        }
        if user_id is not None:
            params["user_id"] = user_id
        if return_id is not None:
            params["return_id"] = return_id

        try:
            return await self.call_service("GET", url, params=params, headers=headers)
        except AppError:
            raise
        except httpx.RequestError as e:
            raise AppError(
                status_code=502,
                code="upstream_unreachable",
                message=f"Sustainability Service unreachable: {e}",
            ) from e


# Singleton instance
service_client = ServiceClient()
