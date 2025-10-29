"""Schemas for expense-related operations."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, validator


class ExpenseBase(BaseModel):
    """Base schema for expense data."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the expense (1-100 characters)",
    )
    amount: Decimal = Field(
        ...,
        ge=Decimal("0.01"),
        le=Decimal("999999.99"),
        decimal_places=2,
        description="Amount of the expense (0.01-999,999.99)",
    )
    expense_date: date = Field(
        default_factory=lambda: date.today(),
        description="Date of the expense (defaults to today if not provided)",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description of the expense (max 500 characters)",
    )
    is_recurring: bool = Field(
        default=False,
        description="Whether this is a recurring expense",
    )

    @validator("expense_date")
    @classmethod
    def validate_expense_date(cls, v: date) -> date:
        """Validate that expense date is not too far in past or future."""
        today = date.today()
        min_date = date(today.year - 1, today.month, today.day)  # 1 year ago
        max_date = date(today.year + 1, today.month, today.day)  # 1 year ahead

        if v < min_date or v > max_date:
            raise ValueError(
                "Expense date must be within one year of current date",
            )
        return v

    @validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name contains valid characters."""
        if not v.strip():
            raise ValueError("Name cannot be empty or just whitespace")

        # Remove any potentially dangerous characters
        forbidden_chars = "<>{}[]\\/"
        if any(char in v for char in forbidden_chars):
            raise ValueError(
                f"Name cannot contain these characters: {forbidden_chars}",
            )
        return v.strip()

    model_config = ConfigDict(from_attributes=True)


class ExpenseCreate(ExpenseBase):
    """Schema for creating a new expense."""

    category_id: UUID = Field(
        ...,
        description="ID of the category this expense belongs to",
    )


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(None, description="New name of the expense")
    amount: Optional[float] = Field(None, ge=0, description="New amount of the expense")
    expense_date: Optional[date] = Field(None, description="New date of the expense")
    description: Optional[str] = Field(
        None,
        description="New description of the expense",
    )
    is_recurring: Optional[bool] = Field(
        None,
        description="Whether this is a recurring expense",
    )
    category_id: Optional[UUID] = Field(
        None,
        description="New category ID for the expense",
    )

    model_config = ConfigDict(from_attributes=True)


class ExpenseRead(ExpenseBase):
    """Schema for reading an expense."""

    id: UUID = Field(..., description="Unique identifier of the expense")
    user_id: UUID = Field(..., description="ID of the user who owns this expense")
    category_id: UUID = Field(
        ...,
        description="ID of the category this expense belongs to",
    )
