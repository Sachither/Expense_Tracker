import re
import uuid
from typing import Optional

from fastapi import HTTPException, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.schemas import BaseUserCreate
from starlette.responses import Response
from starlette.status import HTTP_400_BAD_REQUEST

from Expense_Tracker.db.models.base_models import UserBase
from Expense_Tracker.settings import settings


class User(UserBase):
    """Represents a user entity."""


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """Manages a user session and its tokens."""

    reset_password_token_secret = settings.users_secret
    verification_token_secret = settings.users_secret

    async def validate_password(
        self,
        password: str,
        user: BaseUserCreate | User,
    ) -> None:
        """Validate password strength.

        Args:
            password: The password to validate
            user: The user object (unused in this implementation)

        Raises:
            HTTPException: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )

        if not re.search(r"[A-Z]", password):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter",
            )

        if not re.search(r"[a-z]", password):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter",
            )

        if not re.search(r"\d", password):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number",
            )

        special_chars = '!@#$%^&*(),.?":{}|<>'
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one special character "
                f"({special_chars})",
            )

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        """Called after successful login.

        Args:
            user: The user who logged in
            request: The request object
            response: The response object from FastAPI-Users
        """
        from Expense_Tracker.web.api.auth.logging import log_auth_event

        ip = request.client.host if request and request.client else None
        log_auth_event(
            event_type="login",
            email=user.email,
            success=True,
            ip=ip,
        )

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ) -> None:
        """Called after forgot password request.

        Args:
            user: The user who requested password reset
            token: The reset token
            request: The request object
        """
        from Expense_Tracker.web.api.auth.logging import log_auth_event

        ip = request.client.host if request and request.client else None
        log_auth_event(
            event_type="password_reset_request",
            email=user.email,
            success=True,
            ip=ip,
        )

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        """Called after successful registration.

        Args:
            user: New user.
            request: Request client.
        """
        from Expense_Tracker.web.api.auth.logging import log_auth_event

        ip = request.client.host if request and request.client else None
        log_auth_event(
            event_type="register",
            email=user.email,
            success=True,
            ip=ip,
        )
