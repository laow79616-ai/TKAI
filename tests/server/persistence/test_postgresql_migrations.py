"""Static migration checks that do not require Alembic or a database."""

from __future__ import annotations

from pathlib import Path


def test_initial_migration_defines_namespace_scoped_jsonb_documents() -> None:
    migration = (
        Path(__file__).parents[3]
        / "server"
        / "persistence"
        / "migrations"
        / "versions"
        / "0001_create_marketplace_documents.py"
    )
    contents = migration.read_text(encoding="utf-8")

    assert 'revision = "0001_marketplace_documents"' in contents
    assert '"marketplace_documents"' in contents
    assert "postgresql.JSONB" in contents
    assert 'PrimaryKeyConstraint("namespace", "identifier")' in contents
