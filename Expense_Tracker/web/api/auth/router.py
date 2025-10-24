from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi_users import FastAPIUsers

from .dependencies import get_user_manager
from .jwt import auth_jwt
from .schemas import UserCreate, UserRead

if TYPE_CHECKING:
    from Expense_Tracker.db.models.users import User

router = APIRouter()

fastapi_users = FastAPIUsers[User, UserCreate](
    get_user_manager,
    [auth_jwt],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_auth_router(auth_jwt),
    prefix="/auth/jwt",
    tags=["auth"],
)
