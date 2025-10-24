"""Authentication router configuration."""

from uuid import UUID

from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from Expense_Tracker.db.models.users import User
from Expense_Tracker.web.api.auth.schemas import UserCreate, UserRead

from .dependencies import get_user_manager
from .jwt import auth_jwt

# Initialize FastAPIUsers instance with proper typing
fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,  # type: ignore
    [auth_jwt],  # type: ignore
)

# Initialize authentication router
auth_router = APIRouter()

# Include authentication routes
auth_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",  # Prefix is added in main router
    tags=["auth"],
)

auth_router.include_router(
    fastapi_users.get_auth_router(auth_jwt),
    prefix="/jwt",  # This becomes /auth/jwt when mounted in main router
    tags=["auth"],
)

# Export the instance for use in other routes that need authentication
current_user = fastapi_users.current_user

__all__ = ["auth_router", "fastapi_users", "current_user"]
