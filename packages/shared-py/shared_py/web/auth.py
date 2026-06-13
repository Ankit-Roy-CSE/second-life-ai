"""
JWT helpers shared between the User Service (issue) and Gateway (verify).

Usage — issuing a token (User Service):
    from shared_py.web.auth import create_access_token
    token = create_access_token(subject=str(user.id), secret=settings.jwt_secret)

Usage — verifying a token (Gateway):
    from shared_py.web.auth import decode_access_token
    payload = decode_access_token(token, secret=settings.jwt_secret)
    user_id = payload["sub"]

The Gateway extracts the user id and forwards it as X-User-Id to downstream
services; those services trust the header without re-verifying the JWT.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from shared_py.web.errors import AppError

_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_MINUTES = 1440  # 24 h — generous for a hackathon


def create_access_token(
    subject: str,
    secret: str,
    *,
    algorithm: str = _ALGORITHM,
    expire_minutes: int = _DEFAULT_EXPIRE_MINUTES,
    extra_claims: dict | None = None,
) -> str:
    """
    Encode a signed JWT access token.

    Args:
        subject:       User ID (stored in the "sub" claim).
        secret:        HS256 signing secret (JWT_SECRET env var).
        algorithm:     Signing algorithm; default HS256.
        expire_minutes: Token lifetime in minutes.
        extra_claims:  Additional claims merged into the payload.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    payload: dict = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(
    token: str,
    secret: str,
    *,
    algorithm: str = _ALGORITHM,
) -> dict:
    """
    Decode and validate a JWT access token.

    Raises:
        AppError(401) if the token is invalid, expired, or missing "sub".

    Returns:
        Decoded payload dict.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError as exc:
        raise AppError(
            status_code=401,
            code="unauthenticated",
            message=f"Invalid or expired token: {exc}",
        ) from exc

    if not payload.get("sub"):
        raise AppError(
            status_code=401,
            code="unauthenticated",
            message="Token missing subject claim",
        )

    return payload
