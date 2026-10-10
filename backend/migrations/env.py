import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the application settings and metadata
from app.config.settings import settings
from app.models.base import Base
# Import all models so they are registered on the metadata.
# FIX: previously only user and property were imported here. unit, lease,
# payment, and maintenance were being created by hand-written migrations
# (0009-0012) that happened to match the models exactly, but Alembic's
# target_metadata never knew those tables were "supposed" to exist — so the
# next `alembic revision --autogenerate` would have seen them as unknown
# tables and generated a migration to DROP them. platform_settings is new
# and needs to be registered from the start.
from app.models import user, property, property_source, unit, lease, payment, maintenance, notification, favorite, inquiry, platform_settings  # noqa: F401

# set sqlalchemy.url from settings
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()