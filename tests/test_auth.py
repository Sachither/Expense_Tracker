"""Authentication tests."""

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

test_user_data = {
    "email": "test@example.com",
    "password": "testPass123",
    "first_name": "Test",
    "last_name": "User",
}


@pytest.mark.anyio
async def test_register_user(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test user registration.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    url = fastapi_app.url_path_for("register:register")
    response = await client.post(
        url,
        json=test_user_data,
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["first_name"] == test_user_data["first_name"]
    assert data["last_name"] == test_user_data["last_name"]
    assert "id" in data
    assert "password" not in data


@pytest.mark.anyio
async def test_register_existing_user(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test registering a user with existing email.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    # First registration
    url = fastapi_app.url_path_for("register:register")
    await client.post(url, json=test_user_data)

    # Try registering again with same email
    response = await client.post(url, json=test_user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "REGISTER_USER_ALREADY_EXISTS" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_success(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test successful login.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    # First register the user
    register_url = fastapi_app.url_path_for("register:register")
    await client.post(register_url, json=test_user_data)

    # Then try to login
    login_url = fastapi_app.url_path_for("auth:jwt.login")
    response = await client.post(
        login_url,
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_password(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test login with wrong password.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    # First register the user
    register_url = fastapi_app.url_path_for("register:register")
    await client.post(register_url, json=test_user_data)

    # Try to login with wrong password
    login_url = fastapi_app.url_path_for("auth:jwt.login")
    response = await client.post(
        login_url,
        data={
            "username": test_user_data["email"],
            "password": "wrongpass123",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "LOGIN_BAD_CREDENTIALS" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_nonexistent_user(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test login with non-existent user.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    login_url = fastapi_app.url_path_for("auth:jwt.login")
    response = await client.post(
        login_url,
        data={
            "username": "nonexistent@example.com",
            "password": "somepass123",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "LOGIN_BAD_CREDENTIALS" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_current_user(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test getting current user profile with JWT token.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    # Register user
    register_url = fastapi_app.url_path_for("register:register")
    await client.post(register_url, json=test_user_data)

    # Login to get token
    login_url = fastapi_app.url_path_for("auth:jwt.login")
    login_response = await client.post(
        login_url,
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )

    token = login_response.json()["access_token"]

    # Get user profile with token
    me_url = fastapi_app.url_path_for("users:current_user")
    response = await client.get(
        me_url,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["first_name"] == test_user_data["first_name"]
    assert data["last_name"] == test_user_data["last_name"]


@pytest.mark.anyio
async def test_password_validation(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test password validation rules.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    url = fastapi_app.url_path_for("register:register")

    # Test too short password
    response = await client.post(
        url,
        json={
            **test_user_data,
            "password": "short12",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "at least 8 characters" in response.json()["detail"]

    # Test password without numbers
    response = await client.post(
        url,
        json={
            **test_user_data,
            "password": "passwordonly",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "both letters and numbers" in response.json()["detail"]


@pytest.mark.anyio
async def test_default_categories_creation(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Test that default categories are created for new users.

    Args:
        fastapi_app: FastAPI app instance
        client: Test client
        dbsession: Database session
    """
    # Register user
    register_url = fastapi_app.url_path_for("register:register")
    register_response = await client.post(register_url, json=test_user_data)
    response_data = register_response.json()
    user_id = response_data["id"]

    # Login to get token
    login_url = fastapi_app.url_path_for("auth:jwt.login")
    login_response = await client.post(
        login_url,
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_response.json()["access_token"]

    # Get user's categories
    categories_url = (
        f"/api/categories/user/{user_id}"  # Assuming you have this endpoint
    )
    response = await client.get(
        categories_url,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    categories = response.json()
    # Check if default categories exist
    default_names = {
        "Groceries",
        "Transport",
        "Utilities",
        "Entertainment",
        "Healthcare",
    }
    received_names = {cat["name"] for cat in categories}
    assert default_names.issubset(received_names)
