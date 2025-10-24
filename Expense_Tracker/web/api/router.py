from fastapi.routing import APIRouter

from Expense_Tracker.web.api import dummy, echo, monitoring, redis, users
from Expense_Tracker.web.api.auth import auth_router
from Expense_Tracker.web.api.categories import views as categories

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)  # Add proper prefix for auth
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)  # Add proper prefix for users
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])
api_router.include_router(dummy.router, prefix="/dummy", tags=["dummy"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
