from importlib import metadata

from fastapi import FastAPI
from fastapi.responses import UJSONResponse

from Expense_Tracker.log import configure_logging
from Expense_Tracker.web.api.router import api_router
from Expense_Tracker.web.lifespan import lifespan_setup
from Expense_Tracker.web.middleware.ratelimiter.middleware import rate_limit_middleware


def get_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    app = FastAPI(
        title="Expense_Tracker",
        version=metadata.version("Expense_Tracker"),
        lifespan=lifespan_setup,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        default_response_class=UJSONResponse,
    )

    # Add authentication rate limiter middleware
    app.add_middleware(
        rate_limit_middleware,
        requests_limit=5,  # 5 requests
        window_size=60,  # per minute
        exclude_paths=[
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/categories",
            "/api/users",
            "/api/echo",
            "/api/dummy",
            "/api/monitoring",
            "/api/redis",
        ],
    )

    # Add general rate limiter middleware for other endpoints
    app.add_middleware(
        rate_limit_middleware,
        requests_limit=100,  # 100 requests
        window_size=60,  # per minute
        exclude_paths=[
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ],  # Exclude API docs
    )

    # Main router for the API.
    app.include_router(router=api_router, prefix="/api")

    return app
