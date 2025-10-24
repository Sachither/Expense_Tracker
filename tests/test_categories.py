"""Category API tests."""

import uuid

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from Expense_Tracker.db.models.categories import ExpenseCategory

test_category_data = {
    "name": "Test Category",
    "description": "A test category",
}


async def create_test_category(
    dbsession: AsyncSession,
    user_id: uuid.UUID,
    name: str = "Test Category",
    description: str | None = "A test category",
) -> ExpenseCategory:
    """Create a test category.

    Args:
        dbsession: Database session
        user_id: User ID to associate with the category
        name: Category name
        description: Category description

    Returns:
        Created category
    """
    category = ExpenseCategory(
        id=uuid.uuid4(),
        name=name,
        description=description,
        user_id=user_id,
    )
    dbsession.add(category)
    await dbsession.commit()
    await dbsession.refresh(category)
    return category


@pytest.mark.anyio
async def test_list_categories(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
    auth_header: dict[str, str],
    test_user_id: uuid.UUID,
) -> None:
    """Test listing categories.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
        auth_header: Authentication header
        test_user_id: Test user ID
    """
    # Create some test categories
    await create_test_category(dbsession, test_user_id, "Category 1")
    await create_test_category(dbsession, test_user_id, "Category 2")

    # Get the categories
    response = await client.get("/api/categories/", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK

    categories = response.json()
    assert len(categories) == 2
    assert categories[0]["name"] == "Category 1"
    assert categories[1]["name"] == "Category 2"


@pytest.mark.anyio
async def test_create_category(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
    auth_header: dict[str, str],
    test_user_id: uuid.UUID,
) -> None:
    """Test creating a category.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
        auth_header: Authentication header
        test_user_id: Test user ID
    """
    response = await client.post(
        "/api/categories/",
        headers=auth_header,
        json=test_category_data,
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["name"] == test_category_data["name"]
    assert data["description"] == test_category_data["description"]
    assert "id" in data
    assert data["user_id"] == str(test_user_id)


@pytest.mark.anyio
async def test_get_category(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
    auth_header: dict[str, str],
    test_user_id: uuid.UUID,
) -> None:
    """Test getting a specific category.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
        auth_header: Authentication header
        test_user_id: Test user ID
    """
    # Create a test category
    category = await create_test_category(dbsession, test_user_id)

    # Get the category
    response = await client.get(
        f"/api/categories/{category.id}",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["name"] == category.name
    assert data["description"] == category.description
    assert data["id"] == str(category.id)
    assert data["user_id"] == str(test_user_id)


@pytest.mark.anyio
async def test_update_category(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
    auth_header: dict[str, str],
    test_user_id: uuid.UUID,
) -> None:
    """Test updating a category.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
        auth_header: Authentication header
        test_user_id: Test user ID
    """
    # Create a test category
    category = await create_test_category(dbsession, test_user_id)

    # Update the category
    update_data = {
        "name": "Updated Category",
        "description": "Updated description",
    }
    response = await client.patch(
        f"/api/categories/{category.id}",
        headers=auth_header,
        json=update_data,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["id"] == str(category.id)
    assert data["user_id"] == str(test_user_id)


@pytest.mark.anyio
async def test_delete_category(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
    auth_header: dict[str, str],
    test_user_id: uuid.UUID,
) -> None:
    """Test deleting a category.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
        auth_header: Authentication header
        test_user_id: Test user ID
    """
    # Create a test category
    category = await create_test_category(dbsession, test_user_id)

    # Delete the category
    response = await client.delete(
        f"/api/categories/{category.id}",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's gone
    response = await client.get(
        f"/api/categories/{category.id}",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
