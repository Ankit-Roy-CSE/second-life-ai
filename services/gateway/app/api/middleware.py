"""
Middleware for Gateway Service.

JWT verification middleware:
- Extracts JWT from Authorization header
- Verifies JWT signature and expiry
- Forwards user_id as X-User-Id header to downstream services
"""

from typing import Optional

from fastapi import Header, HTTPException

from shared_py.web.auth import decode_access_token

from app.config import settings


async def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extract and verify JWT from Authorization header.
    
    Returns user_id if token is valid, None if no token provided.
    Raises HTTPException(401) if token is invalid.
    
    Usage in routes:
        @router.get("/protected")
        async def protected_route(
            user_id: str = Depends(get_current_user_id)
        ):
            # user_id is verified
            ...
    
    For optional auth (public endpoints):
        @router.get("/public")
        async def public_route(
            user_id: Optional[str] = Depends(get_current_user_id)
        ):
            # user_id is None if not authenticated
            ...
    """
    if not authorization:
        return None

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        )

    token = parts[1]

    # Verify JWT
    try:
        payload = decode_access_token(token, settings.jwt_secret)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Token missing user ID (sub claim)",
            )
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {e}",
        ) from e


def require_auth(user_id: Optional[str]) -> str:
    """
    Helper to make user_id required (raise 401 if None).
    
    Usage:
        @router.post("/returns")
        async def create_return(
            user_id: Optional[str] = Depends(get_current_user_id)
        ):
            user_id = require_auth(user_id)  # Raises 401 if None
            ...
    """
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide a valid JWT in Authorization header.",
        )
    return user_id
