# import asyncio
# from logging.config import fileConfig
# from sqlalchemy import pool
# from sqlalchemy.engine import Connection
# from sqlalchemy.ext.asyncio import async_engine_from_config
# from alembic import context
#
# from src.core.config import TestDbSettings, DbSettings, settings
#
# # Access Alembic Config object
# config = context.config
#
# # Interpret the config file for Python logging.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)
#
# # Import your model's Base metadata
# from src.core.models import Base
#
#
# # Metadata for autogenerate support
# target_metadata = Base.metadata
#
#
# # Dynamic database URL configuration
# def get_database_url():
#     """Determine the database URL based on the Alembic command."""
#     x_args = context.get_x_argument(as_dictionary=True)
#     print(x_args)
#     if "db_url" in x_args:
#         print("db_url")
#         print(x_args["db_url"])
#         return x_args["db_url"]  # Use passed `db_url` if available
#     elif context.is_offline_mode():
#         # In offline mode, fall back to test settings
#         print("test db")
#         return settings.test_db.db_url
#     else:
#         # Default to production settings
#         url = settings.db.db_url
#         print(f"Prod db url: {url}")
#         return url
#
#
# # Set the SQLAlchemy URL dynamically
# config.set_main_option("sqlalchemy.url", get_database_url())
#
#
# # Offline migrations
# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode."""
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#     )
#
#     with context.begin_transaction():
#         context.run_migrations()
#
#
# # Online migrations
# def do_run_migrations(connection: Connection) -> None:
#     context.configure(connection=connection, target_metadata=target_metadata)
#
#     with context.begin_transaction():
#         context.run_migrations()
#
#
# async def run_async_migrations() -> None:
#     """Run migrations in 'online' mode asynchronously."""
#     connectable = async_engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )
#
#     async with connectable.connect() as connection:
#         await connection.run_sync(do_run_migrations)
#
#     await connectable.dispose()
#
#
# def run_migrations_online() -> None:
#     asyncio.run(run_async_migrations())
#
#
# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()
#
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from src.core.models import Base
from src.core.config import settings

target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
config.set_main_option("sqlalchemy.url", settings.db.db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
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
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

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
