from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base schema for category data."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""


class CategoryUpdate(CategoryBase):
    """Schema for updating a category."""

    name: str = Field(..., min_length=1, max_length=100)


class CategoryRead(CategoryBase):
    """Schema for reading a category."""

    id: UUID
    user_id: UUID
