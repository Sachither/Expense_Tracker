from typing import Callable, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from .limiter import RateLimitConfig, RateLimiter, RateLimitExceeded


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for applying rate limiting to FastAPI routes."""

    def __init__(
        self,
        app: ASGIApp,
        requests_limit: int = 100,
        window_size: int = 60,
        key_func: Optional[Callable[[Request], str]] = None,
        exclude_paths: Optional[list[str]] = None,
    ) -> None:
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests_limit: Maximum number of requests allowed within window
            window_size: Time window in seconds
            key_func: Optional function to generate cache key from request
            exclude_paths: Optional list of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(
            RateLimitConfig(
                requests_limit=requests_limit,
                window_size=window_size,
                key_func=key_func,
            ),
        )
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request through rate limiting.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            Response from next middleware
        """
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        try:
            await self.limiter.is_allowed(request)
            return await call_next(request)
        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers,
            )


def rate_limit_middleware(
    app: ASGIApp,
    requests_limit: int = 100,
    window_size: int = 60,
    exclude_paths: Optional[list[str]] = None,
) -> RateLimitMiddleware:
    """Factory function for RateLimitMiddleware.

    Args:
        app: FastAPI application
        requests_limit: Maximum number of requests allowed within window
        window_size: Time window in seconds
        exclude_paths: List of paths to exclude from rate limiting

    Returns:
        RateLimitMiddleware: Configured middleware instance
    """
    return RateLimitMiddleware(
        app=app,
        requests_limit=requests_limit,
        window_size=window_size,
        exclude_paths=exclude_paths or [],
    )
