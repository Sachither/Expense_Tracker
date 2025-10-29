"""Tests for expense endpoints."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Expense_Tracker.db.models.categories import ExpenseCategory
from Expense_Tracker.db.models.expenses import Expense


@pytest.mark.anyio
async def test_create_expense(
    client: AsyncClient,
    dbsession: AsyncSession,
    authenticated_user: Dict[str, Any],
    test_category: ExpenseCategory,
) -> None:
    """Test creating a new expense."""
    # Test data
    expense_data = {
        "name": "Test Expense",
        "amount": "50.25",
        "description": "Test description",
        "expense_date": str(date.today()),
        "is_recurring": False,
        "category_id": str(test_category.id),
    }

    response = await client.post(
        "/api/expenses/",
        json=expense_data,
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == expense_data["name"]
    assert data["amount"] == expense_data["amount"]
    assert data["description"] == expense_data["description"]
    assert data["user_id"] == str(authenticated_user["user"].id)
    assert data["category_id"] == expense_data["category_id"]

    # Verify in database
    result = await dbsession.execute(
        select(Expense).where(Expense.id == data["id"]),
    )
    db_expense = result.scalar_one()
    assert db_expense is not None
    assert str(db_expense.id) == data["id"]


@pytest.mark.anyio
async def test_list_expenses(
    client: AsyncClient,
    authenticated_user: Dict[str, Any],
    test_expenses: List[Expense],
) -> None:
    """Test listing expenses."""
    response = await client.get(
        "/api/expenses/",
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 200

    data = response.json()
    # Count only the expenses that belong to the authenticated user
    user_expenses = [
        expense
        for expense in test_expenses
        if str(expense.user_id) == str(authenticated_user["user"].id)
    ]
    assert len(data) == len(user_expenses)
    # Verify expenses belong to authenticated user
    assert all(
        expense["user_id"] == str(authenticated_user["user"].id) for expense in data
    )


@pytest.mark.anyio
async def test_get_expense(
    client: AsyncClient,
    authenticated_user: Dict[str, Any],
    test_expenses: List[Expense],
) -> None:
    """Test getting a specific expense."""
    test_expense = test_expenses[0]
    response = await client.get(
        f"/api/expenses/{test_expense.id}",
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(test_expense.id)
    assert data["name"] == test_expense.name
    assert data["user_id"] == str(authenticated_user["user"].id)


@pytest.mark.anyio
async def test_update_expense(
    client: AsyncClient,
    authenticated_user: Dict[str, Any],
    test_expenses: List[Expense],
    test_category: ExpenseCategory,
) -> None:
    """Test updating an expense."""
    test_expense = test_expenses[0]
    update_data = {
        "name": "Updated Expense Name",
        "amount": "75.50",
        "category_id": str(test_category.id),
    }

    response = await client.patch(
        f"/api/expenses/{test_expense.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == update_data["name"]
    # Compare amount values as Decimal to handle different string formats

    assert Decimal(data["amount"]) == Decimal(update_data["amount"])
    assert data["category_id"] == update_data["category_id"]


@pytest.mark.anyio
async def test_delete_expense(
    client: AsyncClient,
    dbsession: AsyncSession,
    authenticated_user: Dict[str, Any],
    test_expenses: List[Expense],
) -> None:
    """Test deleting an expense."""
    test_expense = test_expenses[0]
    response = await client.delete(
        f"/api/expenses/{test_expense.id}",
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 204

    # Verify expense is deleted
    result = await dbsession.execute(
        select(Expense).where(Expense.id == test_expense.id),
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.anyio
async def test_expense_validation(
    client: AsyncClient,
    authenticated_user: Dict[str, Any],
    test_category: ExpenseCategory,
) -> None:
    """Test expense validation rules."""
    # Test invalid amount
    response = await client.post(
        "/api/expenses/",
        json={
            "name": "Test Expense",
            "amount": "0",  # Too small
            "category_id": str(test_category.id),
        },
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 422

    # Test invalid date (too far in future)
    future_date = date.today() + timedelta(days=400)  # > 1 year
    response = await client.post(
        "/api/expenses/",
        json={
            "name": "Test Expense",
            "amount": "50.25",
            "expense_date": str(future_date),
            "category_id": str(test_category.id),
        },
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 422

    # Test invalid category
    response = await client.post(
        "/api/expenses/",
        json={
            "name": "Test Expense",
            "amount": "50.25",
            "category_id": str(uuid4()),  # Non-existent category
        },
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_expense_authorization(
    client: AsyncClient,
    authenticated_user: Dict[str, Any],
    other_user: Dict[str, Any],
    test_expenses: List[Expense],
) -> None:
    """Test expense authorization rules."""
    # Try to access other user's expense
    other_expense = test_expenses[-1]  # Assuming last expense belongs to other user
    response = await client.get(
        f"/api/expenses/{other_expense.id}",
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 404  # Should return not found instead of forbidden

    # Try to update other user's expense
    response = await client.patch(
        f"/api/expenses/{other_expense.id}",
        json={"name": "Hacked Expense"},
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 404

    # Try to delete other user's expense
    response = await client.delete(
        f"/api/expenses/{other_expense.id}",
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"},
    )
    assert response.status_code == 404
