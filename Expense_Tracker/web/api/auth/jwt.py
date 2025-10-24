from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from Expense_Tracker.db.models.users import User
from Expense_Tracker.settings import settings
from Expense_Tracker.web.api.auth.schemas import UserCreate

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[User, UserCreate]:
    """Return a JWTStrategy in order to instantiate it dynamically."""
    return JWTStrategy(
        secret=settings.users_secret,
        lifetime_seconds=60 * 30,  # 30 minutes
    )


auth_jwt = AuthenticationBackend[User, UserCreate](
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
