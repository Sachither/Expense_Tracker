from contextlib import suppress
from typing import Any, AsyncGenerator
from uuid import UUID, uuid4

import pytest
from fakeredis import FakeServer
from fakeredis.aioredis import FakeConnection
from fastapi import FastAPI
from fastapi_users.password import PasswordHelper
from httpx import AsyncClient
from redis.asyncio import ConnectionPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from Expense_Tracker.db.dependencies import get_db_session
from Expense_Tracker.db.meta import meta
from Expense_Tracker.db.utils import create_database, drop_database
from Expense_Tracker.services.redis.dependency import get_redis_pool
from Expense_Tracker.settings import settings
from Expense_Tracker.web.api.auth.schemas import UserCreate
from Expense_Tracker.web.application import get_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend for anyio pytest plugin.

    :return: backend name.
    """
    return "asyncio"


@pytest.fixture(scope="session")
async def _engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create engine and databases.

    :yield: new engine.
    """
    from Expense_Tracker.db.models import load_all_models

    load_all_models()  # Make sure we start with a fresh database
    with suppress(Exception):
        await drop_database()

    await create_database()

    # Create engine with specific test database settings
    engine = create_async_engine(
        str(settings.db_url),
        isolation_level="AUTOCOMMIT",
        echo=True,  # Set to False in production tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()
        await drop_database()


@pytest.fixture
async def dbsession(
    _engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get session to database.

    Fixture that returns a SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.

    :param _engine: current engine.
    :yields: async session.
    """
    connection = await _engine.connect()
    trans = await connection.begin()

    session_maker = async_sessionmaker(
        connection,
        expire_on_commit=False,
    )
    session = session_maker()

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest.fixture
async def fake_redis_pool() -> AsyncGenerator[ConnectionPool, None]:
    """
    Get instance of a fake redis.

    :yield: FakeRedis instance.
    """
    server = FakeServer()
    server.connected = True
    pool = ConnectionPool(connection_class=FakeConnection, server=server)

    yield pool

    await pool.disconnect()


@pytest.fixture
def fastapi_app(
    dbsession: AsyncSession,
    fake_redis_pool: ConnectionPool,
) -> FastAPI:
    """
    Fixture for creating FastAPI app.

    :return: fastapi app with mocked dependencies.
    """
    application = get_app()
    application.dependency_overrides[get_db_session] = lambda: dbsession
    application.dependency_overrides[get_redis_pool] = lambda: fake_redis_pool
    return application


@pytest.fixture
async def client(
    fastapi_app: FastAPI,
    anyio_backend: Any,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates client for requesting server.

    :param fastapi_app: the application.
    :yield: client for the app.
    """
    async with AsyncClient(app=fastapi_app, base_url="http://test", timeout=2.0) as ac:
        yield ac


@pytest.fixture
async def test_user_id(dbsession: AsyncSession) -> UUID:
    """Get a test user ID.

    Args:
        dbsession: Database session

    Returns:
        Test user ID
    """

    password_helper = PasswordHelper()
    test_id = uuid4()
    user_create = UserCreate(
        email=f"test_{test_id}@example.com",
        password="testPass123",
        first_name="Test",
        last_name="User",
    )

    user_dict = {
        "id": uuid4(),
        "email": user_create.email,
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "hashed_password": password_helper.hash(user_create.password),
        "first_name": user_create.first_name,
        "last_name": user_create.last_name,
    }

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
        RETURNING id
        """,
    )
    result = await dbsession.execute(query, user_dict)
    await dbsession.commit()
    return result.scalar_one()


@pytest.fixture
async def auth_header(
    client: AsyncClient,
    test_user_id: UUID,
    dbsession: AsyncSession,
) -> dict[str, str]:
    """Get authentication headers.

    Args:
        client: Test client
        test_user_id: Test user ID

    Returns:
        Headers dict with authentication
    """
    # Get the user's email
    result = await dbsession.execute(
        text('SELECT email FROM "user" WHERE id = :user_id'),
        {"user_id": test_user_id},
    )
    user_email = result.scalar_one()

    response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": user_email,
            "password": "testPass123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
