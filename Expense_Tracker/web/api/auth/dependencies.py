"""Authentication dependencies."""

from typing import TYPE_CHECKING, AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from Expense_Tracker.db.dependencies import get_db_session

if TYPE_CHECKING:
    from Expense_Tracker.db.models.users import User, UserManager
    from Expense_Tracker.web.api.auth.schemas import UserCreate


async def get_user_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, UserCreate], None]:
    """Get SQLAlchemy user database instance."""
    from Expense_Tracker.db.models.users import User

    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, UserCreate] = Depends(get_user_db),
) -> AsyncGenerator["UserManager", None]:
    """Get user manager instance."""
    from Expense_Tracker.db.models.users import UserManager

    yield UserManager(user_db)
