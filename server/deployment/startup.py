"""Bounded PostgreSQL readiness and Alembic startup support for Compose."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib import import_module, resources
from os import environ
from time import sleep
from typing import Protocol, cast
from urllib.parse import quote_plus


class DeploymentStartupError(RuntimeError):
    """Raised when an explicitly configured deployment database never becomes ready."""


class DatabaseConnection(Protocol):
    """Small connection boundary needed by the bounded deployment probe."""

    def close(self) -> None: ...


def database_url(environment: Mapping[str, str] | None = None) -> str:
    """Build the explicit PostgreSQL URL from the provided deployment environment."""
    values = environ if environment is None else environment
    explicit = values.get("DATABASE_URL")
    if explicit:
        return explicit
    required = (
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    )
    missing = tuple(key for key in required if not values.get(key))
    if missing:
        raise DeploymentStartupError(
            "Missing PostgreSQL deployment configuration: " + ", ".join(missing)
        )
    return (
        "postgresql+psycopg://"
        f"{quote_plus(values['POSTGRES_USER'])}:{quote_plus(values['POSTGRES_PASSWORD'])}"
        f"@{values['POSTGRES_HOST']}:{values['POSTGRES_PORT']}/{values['POSTGRES_DB']}"
    )


def wait_for_database(
    url: str,
    *,
    attempts: int,
    interval_seconds: float,
    connect: Callable[[str], DatabaseConnection] | None = None,
) -> None:
    """Perform a bounded readiness probe without a background worker or endless loop."""
    if attempts < 1 or interval_seconds < 0:
        raise ValueError(
            "attempts must be positive and interval_seconds cannot be negative."
        )
    connector = connect if connect is not None else _connect
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            connection = connector(url)
            try:
                return
            finally:
                connection.close()
        except Exception as error:
            last_error = error
            if attempt + 1 < attempts:
                sleep(interval_seconds)
    raise DeploymentStartupError(
        f"PostgreSQL did not become ready after {attempts} attempts."
    ) from last_error


def run_migrations(url: str) -> None:
    """Run the packaged Alembic migration chain for one explicitly selected database."""
    alembic_config = import_module("alembic.config")
    command = import_module("alembic.command")
    persistence_resources = resources.files("server.persistence")
    configuration_path = persistence_resources.joinpath("alembic.ini")
    migration_path = persistence_resources.joinpath("migrations")
    configuration = alembic_config.Config(str(configuration_path))
    configuration.set_main_option("script_location", str(migration_path))
    configuration.set_main_option("sqlalchemy.url", url)
    command.upgrade(configuration, "head")


def main() -> None:
    """Optionally migrate before Uvicorn is started by the container command."""
    if environ.get("POSTGRES_MIGRATE", "true").lower() not in {"1", "true", "yes"}:
        return
    url = database_url()
    wait_for_database(
        url,
        attempts=int(environ.get("POSTGRES_WAIT_ATTEMPTS", "30")),
        interval_seconds=float(environ.get("POSTGRES_WAIT_INTERVAL_SECONDS", "1")),
    )
    run_migrations(url)


def _connect(url: str) -> DatabaseConnection:
    psycopg = import_module("psycopg")
    dsn = url.replace("postgresql+psycopg://", "postgresql://", 1)
    return cast(DatabaseConnection, psycopg.connect(dsn))


if __name__ == "__main__":
    main()
