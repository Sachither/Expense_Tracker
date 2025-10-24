"""Authentication dependencies."""

from typing import TYPE_CHECKING, AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi_users.db import BaseUserDatabase, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from Expense_Tracker.db.dependencies import get_db_session
from Expense_Tracker.db.models.users import User
from Expense_Tracker.web.api.auth.schemas import UserCreate

if TYPE_CHECKING:
    from Expense_Tracker.db.models.users import UserManager


async def get_user_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, UserCreate], None]:
    """Get SQLAlchemy user database instance."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: BaseUserDatabase[User, UUID] = Depends(get_user_db),
) -> AsyncGenerator["UserManager", None]:
    """Get user manager instance."""
    from Expense_Tracker.db.models.users import UserManager

    yield UserManager(user_db)
