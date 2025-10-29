from datetime import date
from typing import Any, Dict, List
from uuid import UUID, uuid4

import pytest
from fastapi_users.password import PasswordHelper
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from Expense_Tracker.db.models.categories import ExpenseCategory
from Expense_Tracker.db.models.expenses import Expense


@pytest.fixture
async def test_category(dbsession: AsyncSession, test_user_id: UUID) -> ExpenseCategory:
    """Create a test category.

    Args:
        dbsession: Database session
        test_user_id: Test user ID

    Returns:
        Test category
    """
    category = ExpenseCategory(
        id=uuid4(),
        name="Test Category",
        description="Test category description",
        user_id=test_user_id,
    )
    dbsession.add(category)
    await dbsession.commit()
    await dbsession.refresh(category)
    return category


@pytest.fixture
async def test_expenses(
    dbsession: AsyncSession,
    test_user_id: UUID,
    test_category: ExpenseCategory,
    other_user: Dict[str, Any],
) -> List[Expense]:
    """Create test expenses.

    Args:
        dbsession: Database session
        test_user_id: Test user ID
        test_category: Test category
        other_user: Other user fixture for testing authorization

    Returns:
        List of test expenses
    """
    # Create multiple expenses for test user
    expenses = [
        Expense(
            id=uuid4(),
            name=f"Test Expense {i}",
            amount=50.00 + i,
            expense_date=date.today(),
            description=f"Test description {i}",
            is_recurring=False,
            category_id=test_category.id,
            user_id=test_user_id,
        )
        for i in range(3)
    ]

    # Create one expense for other user
    other_category = ExpenseCategory(
        id=uuid4(),
        name="Other User Category",
        description="Other user's category",
        user_id=other_user["user"].id,
    )
    dbsession.add(other_category)

    other_expense = Expense(
        id=uuid4(),
        name="Other User Expense",
        amount=100.00,
        expense_date=date.today(),
        category_id=other_category.id,
        user_id=other_user["user"].id,
    )
    expenses.append(other_expense)

    for expense in expenses:
        dbsession.add(expense)

    await dbsession.commit()
    for expense in expenses:
        await dbsession.refresh(expense)

    return expenses


@pytest.fixture
async def other_user(dbsession: AsyncSession, client: AsyncClient) -> Dict[str, Any]:
    """Create another test user.

    Args:
        dbsession: Database session
        client: Test client

    Returns:
        Dict with other user info and access token
    """
    password_helper = PasswordHelper()
    other_id = uuid4()
    user_dict = {
        "id": other_id,
        "email": f"other_{other_id}@example.com",
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "hashed_password": password_helper.hash("otherPass123"),
        "first_name": "Other",
        "last_name": "User",
    }

    # Create user
    query = text(
        """
        INSERT INTO "user" (
            id, email, is_active, is_superuser, is_verified,
            hashed_password, first_name, last_name
        )
        VALUES (
            :id, :email, :is_active, :is_superuser, :is_verified,
            :hashed_password, :first_name, :last_name
        )
        RETURNING id, email, first_name, last_name
        """,
    )
    result = await dbsession.execute(query, user_dict)
    user_data = result.mappings().one()
    await dbsession.commit()

    # Get access token
    response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": user_dict["email"],
            "password": "otherPass123",
        },
    )
    token = response.json()["access_token"]

    return {
        "user": user_data,
        "access_token": token,
    }


@pytest.fixture
async def authenticated_user(
    dbsession: AsyncSession,
    client: AsyncClient,
    test_user_id: UUID,
) -> Dict[str, Any]:
    """Get authenticated user with access token.

    Args:
        dbsession: Database session
        client: Test client
        test_user_id: Test user ID

    Returns:
        Dict with user info and access token
    """
    # Get user data
    query = text(
        """
        SELECT id, email, first_name, last_name
        FROM "user"
        WHERE id = :user_id
        """,
    )
    result = await dbsession.execute(query, {"user_id": test_user_id})
    user_data = result.mappings().one()

    # Get access token
    response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": user_data["email"],
            "password": "testPass123",
        },
    )
    token = response.json()["access_token"]

    return {
        "user": user_data,
        "access_token": token,
    }
