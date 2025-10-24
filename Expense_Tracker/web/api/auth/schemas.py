import uuid
from typing import Any, ClassVar

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Represents a read command for a user."""

    first_name: str | None = None
    last_name: str | None = None

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    """Represents a create command for a user."""

    first_name: str | None = None
    last_name: str | None = None

    class Config:
        """Pydantic model configuration."""

        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword123",
                "first_name": "John",
                "last_name": "Doe",
            },
        }


class UserUpdate(schemas.BaseUserUpdate):
    """Represents an update command for a user."""

    first_name: str | None = None
    last_name: str | None = None
