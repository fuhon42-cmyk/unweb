"""API key authentication and rate limiting for Unweb."""

import os

from fastapi import Header, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .supabase import verify_api_key as _verify_key

limiter = Limiter(key_func=get_remote_address)


async def verify_api_key(
    request: Request,
    x_api_key: str = Header(...),
) -> str:
    """Validate an API key against Supabase, or bypass in dev mode."""
    if os.environ.get("UNWEB_DEV", "").lower() == "true":
        return "dev_user"

    user_id = _verify_key(x_api_key)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
