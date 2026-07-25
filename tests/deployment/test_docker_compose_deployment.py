"""Static and offline tests for the Docker Compose development deployment."""

from __future__ import annotations

from pathlib import Path

import pytest

from server.deployment.startup import (
    DeploymentStartupError,
    database_url,
    wait_for_database,
)

ROOT = Path(__file__).parents[2]


def test_compose_declares_decoupled_services_health_checks_and_named_volume() -> None:
    contents = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    for service in ("postgres:", "api:", "dashboard:"):
        assert service in contents
    assert "marketplace-postgres-data" in contents
    assert "condition: service_healthy" in contents
    assert "healthcheck:" in contents
    assert "POSTGRES_HOST: postgres" in contents
    assert "VITE_API_BASE_URL" in contents


def test_dockerfiles_use_minimal_runtime_images_and_ignore_development_outputs() -> (
    None
):
    api = (ROOT / "Dockerfile.api").read_text(encoding="utf-8")
    dashboard = (ROOT / "Dockerfile.dashboard").read_text(encoding="utf-8")
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert "AS builder" in api
    assert "uvicorn --factory server.api.app:create_app" in api
    assert "python:3.12-slim" in api
    assert "AS build" in dashboard
    assert "npm run build" in dashboard
    for value in (".git", ".pytest_cache", "node_modules", "tests", ".env"):
        assert value in ignored


def test_example_environment_has_required_names_without_real_credentials() -> None:
    contents = (ROOT / ".env.example").read_text(encoding="utf-8")

    for variable in (
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "API_HOST",
        "API_PORT",
        "DASHBOARD_PORT",
    ):
        assert f"{variable}=" in contents
    assert "change-me-before-use" in contents
    assert "postgresql://" not in contents


def test_packaged_migration_configuration_and_make_targets_exist() -> None:
    migration = ROOT / "server" / "persistence" / "alembic.ini"
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert migration.is_file()
    for target in ("dev-up:", "dev-down:", "dev-logs:", "dev-reset:"):
        assert target in makefile


def test_startup_url_is_explicit_and_readiness_is_bounded() -> None:
    values = {
        "POSTGRES_HOST": "postgres",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "tkai",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password",
    }
    assert (
        database_url(values) == "postgresql+psycopg://user:password@postgres:5432/tkai"
    )

    class Connection:
        closed = False

        def close(self) -> None:
            self.closed = True

    connection = Connection()
    wait_for_database(
        "postgresql+psycopg://example",
        attempts=1,
        interval_seconds=0,
        connect=lambda _: connection,
    )
    assert connection.closed is True

    with pytest.raises(DeploymentStartupError, match="Missing PostgreSQL"):
        database_url({})

    with pytest.raises(DeploymentStartupError, match="did not become ready"):
        wait_for_database(
            "postgresql+psycopg://example",
            attempts=2,
            interval_seconds=0,
            connect=lambda _: (_ for _ in ()).throw(ConnectionError("offline")),
        )
