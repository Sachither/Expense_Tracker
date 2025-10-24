from uuid import UUID

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from Expense_Tracker.db.models.users import User
from Expense_Tracker.settings import settings

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[User, UUID]:
    """Return a JWTStrategy in order to instantiate it dynamically."""
    return JWTStrategy(
        secret=settings.users_secret,
        lifetime_seconds=settings.jwt_token_lifetime,
        algorithm=settings.jwt_algorithm,
    )


auth_jwt = AuthenticationBackend[User, UUID](
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
