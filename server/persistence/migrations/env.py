"""Alembic environment for the optional Marketplace Server PostgreSQL store."""

from __future__ import annotations

from importlib import import_module

from server.persistence.postgresql import orm_models

context = import_module("alembic.context")
sqlalchemy = import_module("sqlalchemy")

config = context.config
target_metadata = orm_models().metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the explicitly supplied PostgreSQL URL."""
    connectable = sqlalchemy.engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=sqlalchemy.pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
