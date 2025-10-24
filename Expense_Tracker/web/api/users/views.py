"""User management views and router configuration."""

from fastapi import APIRouter, Depends

from Expense_Tracker.web.api.auth import current_user, fastapi_users
from Expense_Tracker.web.api.auth.schemas import UserRead, UserUpdate

router = APIRouter()


# Add current user route
@router.get("/me", response_model=UserRead, tags=["users"])
async def get_current_user(
    user: UserRead = Depends(current_user(active=True)),
) -> UserRead:
    """Get information about the currently authenticated user."""
    return user


# Include user management routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="",  # No prefix as this is already under /users from main router
    tags=["users"],
)
