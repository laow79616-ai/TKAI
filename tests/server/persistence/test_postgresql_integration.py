"""Optional PostgreSQL integration test for an explicitly supplied test database."""

from __future__ import annotations

import os
from collections.abc import Mapping

import pytest
from pydantic import SecretStr

test_url = os.environ.get("TKAI_POSTGRESQL_TEST_URL")
if not test_url:
    pytest.skip(
        "Set TKAI_POSTGRESQL_TEST_URL to run PostgreSQL integration tests.",
        allow_module_level=True,
    )

pytest.importorskip("sqlalchemy")

from server.persistence.postgresql import (  # noqa: E402
    PostgreSQLConfiguration,
    PostgreSQLStorage,
    orm_models,
)


def _serialize(value: str) -> Mapping[str, object]:
    return {"value": value}


def _deserialize(payload: Mapping[str, object]) -> str:
    value = payload["value"]
    assert isinstance(value, str)
    return value


def test_postgresql_storage_round_trip_in_explicit_test_database() -> None:
    """Round-trip a document and remove only the explicitly test-owned table."""
    storage = PostgreSQLStorage.from_configuration(
        "integration",
        PostgreSQLConfiguration(database_url=SecretStr(test_url)),
        serialize=_serialize,
        deserialize=_deserialize,
    )
    models = orm_models()
    repository = storage._repository
    sessions = repository._sessions
    models.metadata.create_all(sessions.engine)
    try:
        storage.put("record", "value")
        assert storage.get("record") == "value"
        assert storage.remove("record") == "value"
    finally:
        models.metadata.drop_all(sessions.engine)
        storage.close()
