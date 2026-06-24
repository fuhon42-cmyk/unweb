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
    # Dev mode: return the dev user UUID
    if os.environ.get("UNWEB_DEV", "").lower() == "true":
        return os.environ.get("DEV_USER_ID", "062b5af1-9058-44dd-b2e2-6d60b90cda15")

    user_id = _verify_key(x_api_key)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
