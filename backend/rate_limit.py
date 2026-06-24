"""Rate limiting for Unweb API."""

import os
from typing import Callable, Optional

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.auth import limiter as auth_limiter


class FreeTierLimiter:
    """Enforces a 100‑request‑per‑minute rate limit.

    Returns 429 with a ``Retry-After`` header when exceeded.
    """

    def __init__(self, requests_per_minute: int = 100, enabled: bool = True) -> None:
        self._requests_per_minute = requests_per_minute
        self._enabled = enabled
        self._limiter = Limiter(key_func=get_remote_address)

    def limit(self, limit_value: Optional[str] = None) -> Callable:
        """Decorator to apply this rate limit to a route handler."""
        if not self._enabled:
            return lambda func: func
        if limit_value is None:
            limit_value = f"{self._requests_per_minute}/minute"
        return self._limiter.limit(limit_value)


local_dev_limiter = FreeTierLimiter(
    enabled=os.environ.get("UNWEB_DEV") != "true",
)
