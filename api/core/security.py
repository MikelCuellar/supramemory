"""API key auth via header Authorization: Bearer <key>."""
from fastapi import Header, HTTPException, status

from api.core.config import settings


async def require_api_key(authorization: str | None = Header(default=None)) -> str:
    """Valida que el header Authorization coincida con settings.api_key."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    # Formato: "Bearer <key>"
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format. Expected: Bearer <api_key>",
        )
    key = parts[1].strip()
    if key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return key