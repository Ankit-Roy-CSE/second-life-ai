"""
HTTP client for calling upstream services.

Gateway proxies calls to User, Grading, Lifecycle, Passport, Matching, Sustainability services.
Uses httpx.AsyncClient for async HTTP calls.
"""

from typing import Any, Optional

import httpx

from shared_py.web.errors import AppError

from app.config import settings


class ServiceClient:
    """
    HTTP client for calling upstream microservices.
    
    Handles:
    - Async HTTP calls with httpx
    - Error handling and status code mapping
    - Header propagation (correlation_id, user_id)
    """

    def __init__(self):
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient(timeout=30.0)

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
                message=error_data.get("error", {}).get("message", f"Upstream service error: {response.status_code}"),
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


# Singleton instance
service_client = ServiceClient()
