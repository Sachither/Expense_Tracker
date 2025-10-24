"""User management views and router configuration."""

from fastapi import APIRouter

from Expense_Tracker.web.api.auth import fastapi_users
from Expense_Tracker.web.api.auth.schemas import UserRead, UserUpdate

router = APIRouter()

# Include user management routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="",  # No prefix as this is already under /users from main router
    tags=["users"],
)
