"""Expense_Tracker models."""

from Expense_Tracker.db.models.base_models import UserBase
from Expense_Tracker.db.models.categories import ExpenseCategory
from Expense_Tracker.db.models.expenses import Expense
from Expense_Tracker.db.models.users import User

__all__ = ["UserBase", "User", "ExpenseCategory", "Expense"]


def load_all_models() -> None:
    """Load all models."""
    # Models are already imported above
