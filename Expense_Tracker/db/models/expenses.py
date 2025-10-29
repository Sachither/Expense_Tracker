"""Models for expenses tracking."""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Expense_Tracker.db.base import Base

if TYPE_CHECKING:
    from Expense_Tracker.db.models.base_models import UserBase
    from Expense_Tracker.db.models.categories import ExpenseCategory


class Expense(Base):
    """Model for user expenses."""

    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expense_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["UserBase"] = relationship(
        "Expense_Tracker.db.models.base_models.UserBase",
        back_populates="expenses",
    )
    category: Mapped["ExpenseCategory"] = relationship(
        "Expense_Tracker.db.models.categories.ExpenseCategory",
        back_populates="expenses",
    )
