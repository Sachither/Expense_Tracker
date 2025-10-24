from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import CookieTransport

from Expense_Tracker.db.models.users import User
from Expense_Tracker.web.api.auth.dependencies import get_user_manager
from Expense_Tracker.web.api.auth.jwt import auth_jwt
from Expense_Tracker.web.api.auth.schemas import UserCreate, UserRead, UserUpdate

cookie_transport = CookieTransport(
    cookie_name="expense_tracker_auth",
    cookie_max_age=3600,
)

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
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

router.include_router(
    fastapi_users.get_auth_router(auth_jwt),
    prefix="/auth/jwt",
    tags=["auth"],
)
