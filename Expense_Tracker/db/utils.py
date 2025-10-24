from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from Expense_Tracker.settings import settings


async def create_database() -> None:
    """Create a database."""
    db_url = make_url(str(settings.db_url.with_path("/postgres")))
    engine = create_async_engine(db_url, isolation_level="AUTOCOMMIT")

    try:
        # Convert database name to lowercase for PostgreSQL compatibility
        db_name = settings.db_base.lower()
        async with engine.connect() as conn:
            database_existence = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name},
            )
            database_exists = database_existence.scalar() == 1

        if database_exists:
            await drop_database()

        async with engine.connect() as conn:
            await conn.execute(
                text(
                    f'CREATE DATABASE "{db_name}" ENCODING "utf8" TEMPLATE template1',
                ),
            )
    finally:
        await engine.dispose()


async def drop_database() -> None:
    """Drop current database."""
    db_url = make_url(str(settings.db_url.with_path("/postgres")))
    engine = create_async_engine(db_url, isolation_level="AUTOCOMMIT")

    try:
        # Convert database name to lowercase for PostgreSQL compatibility
        db_name = settings.db_base.lower()
        async with engine.connect() as conn:
            # Terminate existing connections
            disc_users = (
                "SELECT pg_terminate_backend(pg_stat_activity.pid) "
                "FROM pg_stat_activity "
                "WHERE pg_stat_activity.datname = :db_name AND "
                "pid <> pg_backend_pid();"
            )
            await conn.execute(text(disc_users), {"db_name": db_name})

            # Drop database
            await conn.execute(
                text(
                    f'DROP DATABASE IF EXISTS "{db_name}"',
                ),
            )
    finally:
        await engine.dispose()
