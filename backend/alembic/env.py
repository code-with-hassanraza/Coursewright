from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.base import Base
from app.models import *  # noqa: F401, F403 — loads all models so Alembic detects them
from app.core.config import settings

# Alembic Config object — gives access to alembic.ini values
config = context.config

# Override the placeholder sqlalchemy.url with our real one from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from alembic.ini config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic diffs against to generate migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Offline mode: generate SQL script without connecting to DB.
    Useful when you want to review SQL before applying it.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online mode: connect to DB and apply migrations directly.
    This is what runs when you do: alembic upgrade head
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
    