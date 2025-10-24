from datetime import datetime
from typing import Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request
from starlette.status import HTTP_429_TOO_MANY_REQUESTS


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: int = 0,
    ) -> None:
        """Initialize rate limit exception.

        Args:
            detail: Error detail message
            retry_after: Seconds until next request is allowed
        """
        super().__init__(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)} if retry_after else None,
        )


class RateLimitConfig:
    """Configuration for rate limiting."""

    def __init__(
        self,
        requests_limit: int = 100,
        window_size: int = 60,
        key_func: Optional[Callable[[Request], str]] = None,
    ) -> None:
        """Initialize rate limit configuration.

        Args:
            requests_limit: Maximum number of requests allowed within window
            window_size: Time window in seconds
            key_func: Optional function to generate cache key from request
        """
        self.requests_limit = requests_limit
        self.window_size = window_size
        self.key_func = key_func or self._default_key_func

    @staticmethod
    def _default_key_func(request: Request) -> str:
        """Default function to generate cache key from request.

        Uses client's IP address as the key.

        Args:
            request: FastAPI request object

        Returns:
            str: Cache key for rate limiting
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class RateLimiter:
    """Rate limiter implementation using in-memory storage."""

    def __init__(self, config: RateLimitConfig) -> None:
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self._cache: Dict[str, Tuple[datetime, int]] = {}

    def _clean_old_requests(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.now()
        expired = [
            key
            for key, (timestamp, _) in self._cache.items()
            if (now - timestamp).total_seconds() >= self.config.window_size
        ]
        for key in expired:
            del self._cache[key]

    async def is_allowed(self, request: Request) -> bool:
        """Check if request is allowed under current rate limit.

        Args:
            request: FastAPI request object

        Returns:
            bool: True if request is allowed, False otherwise

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        key = self.config.key_func(request)
        now = datetime.now()

        self._clean_old_requests()

        if key in self._cache:
            timestamp, count = self._cache[key]
            if (now - timestamp).total_seconds() < self.config.window_size:
                if count >= self.config.requests_limit:
                    retry_after = int(
                        self.config.window_size - (now - timestamp).total_seconds(),
                    )
                    raise RateLimitExceeded(retry_after=retry_after)
                self._cache[key] = (timestamp, count + 1)
            else:
                self._cache[key] = (now, 1)
        else:
            self._cache[key] = (now, 1)

        return True
