<<<<<<< HEAD
"""Alembic environment configuration for Sales OS."""
=======
"""Alembic migration environment configuration."""

>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

<<<<<<< HEAD
# Import all models to ensure they're registered with Base
from app.db.base import Base
from app.models import (
    Call,
    CoachingReport,
    CoachingScore,
    Company,
    Content,
    ContentTemplate,
    HubSpotIntegration,
    Organization,
    Prospect,
    SPICEDAnalysis,
    Team,
    Transcript,
    User,
)

# Load settings
try:
    from app.core.config import settings
    DATABASE_URL = settings.database_url
except Exception:
    import os
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/sales_os"
    )

# Alembic Config object
config = context.config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", DATABASE_URL)

=======
# Import the Base and all models so Alembic can see them
from app.db.base import Base
from app.models import activity  # noqa: F401
from app.core.config import get_settings

# this is the Alembic Config object
config = context.config

>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

<<<<<<< HEAD
# Model's MetaData object for autogenerate support
target_metadata = Base.metadata

=======
# Set the target metadata for 'autogenerate' support
target_metadata = Base.metadata

# Get database URL from settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
<<<<<<< HEAD
        compare_type=True,
        compare_server_default=True,
=======
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
<<<<<<< HEAD
    """Run migrations with a connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
=======
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
<<<<<<< HEAD
    """Run migrations in 'online' mode with async engine."""
=======
    """Run migrations in 'online' mode using async engine."""
>>>>>>> origin/claude/activity-logging-system-01XwEaki97iEcvBSReHjaGCK
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
