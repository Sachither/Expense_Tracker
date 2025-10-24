"""Base models with relationships."""

from typing import TYPE_CHECKING, List

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Expense_Tracker.db.base import Base

if TYPE_CHECKING:
    from Expense_Tracker.db.models.categories import ExpenseCategory


class UserBase(SQLAlchemyBaseUserTableUUID, Base):
    """Base user model with common fields."""

    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # Define relationship using string reference
    categories: Mapped[List["ExpenseCategory"]] = relationship(
        "Expense_Tracker.db.models.categories.ExpenseCategory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
