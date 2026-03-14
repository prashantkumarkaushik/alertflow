import os
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base

# Import all models so Alembic can detect them
from app.models import Team, User, SLAPolicy  # noqa: F401

# Alembic Config object
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic compares against your DB to find changes
target_metadata = Base.metadata


def get_url() -> str:
    # Read directly from env — bypasses pydantic-settings caching
    # Alembic runs from host machine so we always use localhost
    user = os.getenv("POSTGRES_USER", "alertflow")
    password = os.getenv("POSTGRES_PASSWORD", "alertflow")
    db = os.getenv("POSTGRES_DB", "alertflow")

    # If running inside Docker, POSTGRES_SERVER=db, otherwise localhost
    server = os.getenv("POSTGRES_SERVER", "localhost")
    if server == "db":
        server = "localhost"

    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"


# def get_url() -> str:
#     return "postgresql+asyncpg://alertflow:alertflow@localhost:5432/alertflow"


def run_migrations_offline() -> None:
    """Run migrations without a database connection — just generates SQL."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # detects column type changes
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    engine = create_async_engine(get_url())

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
