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

    @staticmethod
    async def get_cache_key(request: Request) -> str:
        """Default function to generate cache key from request.

        Uses user ID if available, falls back to IP address.

        Args:
            request: FastAPI request object

        Returns:
            str: Cache key for rate limiting
        """
        # Try to get user ID first
        user_id = await RateLimitConfig.get_user(request)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        endpoint = request.url.path
        return f"ip:{ip}:path:{endpoint}"

    @staticmethod
    async def get_user(request: Request) -> Optional[str]:
        """Try to get current user from request state."""
        try:
            user = request.state.user
            return str(user.id) if user else None
        except AttributeError:
            return None

    def __init__(
        self,
        requests_limit: int = 100,
        window_size: int = 60,
        auth_requests_limit: Optional[int] = None,
        key_func: Optional[Callable[[Request], str]] = None,
    ) -> None:
        """Initialize rate limit configuration.

        Args:
            requests_limit: Max requests per window for anonymous users
            window_size: Time window in seconds
            auth_requests_limit: Optional different limit for authenticated users
            key_func: Optional function to generate cache key from request
        """
        self.requests_limit = requests_limit
        self.window_size = window_size
        self.auth_requests_limit = (
            auth_requests_limit or requests_limit * 2
        )  # Double limit for auth users
        self.key_func = key_func or self.get_cache_key


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
        key = await self.config.get_cache_key(request)
        is_authenticated = await self.config.get_user(request) is not None
        limit = (
            self.config.auth_requests_limit
            if is_authenticated
            else self.config.requests_limit
        )

        now = datetime.now()
        self._clean_old_requests()

        if key in self._cache:
            timestamp, count = self._cache[key]
            time_passed = (now - timestamp).total_seconds()

            if time_passed >= self.config.window_size:
                # Window expired, reset counter
                self._cache[key] = (now, 1)
            else:
                # Update counter
                if count >= limit:
                    retry_after = int(self.config.window_size - time_passed)
                    raise RateLimitExceeded(
                        detail=(
                            f"Rate limit exceeded. "
                            f"Try again in {retry_after} seconds"
                        ),
                        retry_after=retry_after,
                    )
                self._cache[key] = (timestamp, count + 1)
        else:
            # First request for this key
            self._cache[key] = (now, 1)

        return True
