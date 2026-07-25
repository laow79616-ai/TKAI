"""Offline release-validation checks for Marketplace Server V2."""

from __future__ import annotations

from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]


def test_release_package_declarations_include_server_dashboard_and_migrations() -> None:
    """Keep release content explicit without requiring build tooling in tests."""
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    data_files = configuration["tool"]["setuptools"]["data-files"]

    assert "recursive-include server/persistence *.ini *.py" in manifest
    assert "recursive-include dashboard/frontend" in manifest
    assert "include docs/ReleaseValidation.md" in manifest
    assert "share/tkai/dashboard/frontend" in data_files
    dashboard_files = data_files["share/tkai/dashboard/frontend"]
    assert "dashboard/frontend/src/App.tsx" in dashboard_files
    assert data_files["share/doc/tkai/release"] == ["docs/ReleaseValidation.md"]
    assert {"fastapi", "pydantic", "uvicorn"}.issubset(
        {
            dependency.split(">=")[0]
            for dependency in configuration["project"]["optional-dependencies"][
                "server"
            ]
        }
    )


def test_release_files_and_compatibility_imports_are_available() -> None:
    """Exercise the public product boundaries without external services."""
    for relative_path in (
        "Dockerfile.api",
        "Dockerfile.dashboard",
        "docker-compose.yml",
        ".env.example",
        "server/persistence/alembic.ini",
        "server/persistence/migrations/versions/0001_create_marketplace_documents.py",
        "docs/ReleaseValidation.md",
    ):
        assert (ROOT / relative_path).is_file()

    import cloud  # noqa: F401
    import enterprise  # noqa: F401
    import marketplace  # noqa: F401
    import server.api  # noqa: F401
    import server.enterprise  # noqa: F401
    import server.health  # noqa: F401
    import server.package  # noqa: F401
    import server.publisher  # noqa: F401
    import server.registry  # noqa: F401
    import server.search  # noqa: F401
    import server.statistics  # noqa: F401
    import server.version  # noqa: F401
    import studio  # noqa: F401
    import tkai  # noqa: F401
    import tkai.sdk  # noqa: F401


def test_release_document_does_not_claim_unavailable_deployment_validation() -> None:
    """Avoid representing static inspection as an executed deployment smoke test."""
    document = (ROOT / "docs/ReleaseValidation.md").read_text(encoding="utf-8")

    assert "/Users/" not in document
    assert "Not ready for an external GA declaration" in document
    assert "Docker, Node/npm" in document
    assert 'pip install "tkai[server]"' in document
