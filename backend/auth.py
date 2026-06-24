"""API key authentication and rate limiting for Unweb."""

import os
from typing import Optional

from fastapi import Header, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from supabase import create_client

_SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
_SUPABASE_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")
_supabase_client = None


def _get_supabase():
    """Return the cached Supabase client singleton."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if _SUPABASE_URL is None or _SUPABASE_KEY is None:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
    _supabase_client = create_client(_SUPABASE_URL, _SUPABASE_KEY)
    return _supabase_client


limiter = Limiter(key_func=get_remote_address)


async def verify_api_key(
    request: Request,
    x_api_key: str = Header(...),
) -> str:
    """Validate an API key against Supabase, or bypass in dev mode."""
    # Dev mode: accept any key and return a mock user_id
    if os.environ.get("UNWEB_DEV", "").lower() == "true":
        return "dev_user"

    supabase = _get_supabase()

    try:
        result = supabase.table("api_keys").select("user_id").eq("key", x_api_key).maybe_single().execute()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Authentication service unreachable",
        ) from exc

    if not result.data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = result.data["user_id"]
    return user_id
