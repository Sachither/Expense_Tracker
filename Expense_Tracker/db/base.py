from sqlalchemy.orm import DeclarativeBase

from Expense_Tracker.db.meta import meta


class Base(DeclarativeBase):
    """Base for all models."""

    metadata = meta
