import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Expense_Tracker.db.base import Base

if TYPE_CHECKING:
    from Expense_Tracker.db.models.base_models import UserBase


class ExpenseCategory(Base):
    """Model for expense categories."""

    __tablename__ = "expense_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )

    # Relationships
    user: Mapped["UserBase"] = relationship(
        "Expense_Tracker.db.models.base_models.UserBase",
        back_populates="categories",
    )

    @classmethod
    def get_default_categories(cls) -> list[dict[str, str]]:
        """Get list of default categories for new users."""
        return [
            {"name": "Groceries", "description": "Food and household items"},
            {"name": "Transport", "description": "Public transport, fuel, parking"},
            {"name": "Utilities", "description": "Electricity, water, internet"},
            {"name": "Entertainment", "description": "Movies, dining out, hobbies"},
            {"name": "Healthcare", "description": "Medical expenses and insurance"},
        ]
