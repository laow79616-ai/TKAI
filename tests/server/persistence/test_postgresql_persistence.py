"""Offline contract tests for optional PostgreSQL document storage."""

from __future__ import annotations

from collections.abc import Mapping

import pytest
from pydantic import SecretStr, ValidationError

from server.persistence.postgresql import (
    DocumentRepository,
    PersistedDocument,
    PostgreSQLConfiguration,
    PostgreSQLDependencyError,
    PostgreSQLPersistenceError,
    PostgreSQLStorage,
)


class FakeDocumentRepository(DocumentRepository):
    """Offline repository double retaining deterministic document order."""

    def __init__(self) -> None:
        self._documents: dict[tuple[str, str], PersistedDocument] = {}
        self.closed = False

    def create(self, document: PersistedDocument) -> PersistedDocument:
        key = (document.namespace, document.identifier)
        if key in self._documents:
            raise ValueError("Duplicate PostgreSQL storage key.")
        self._documents[key] = document
        return document

    def get(self, namespace: str, identifier: str) -> PersistedDocument:
        return self._documents[(namespace, identifier)]

    def list(self, namespace: str) -> tuple[PersistedDocument, ...]:
        return tuple(
            document
            for key, document in sorted(self._documents.items())
            if key[0] == namespace
        )

    def remove(self, namespace: str, identifier: str) -> PersistedDocument:
        return self._documents.pop((namespace, identifier))

    def close(self) -> None:
        self.closed = True


def _serialize(value: str) -> Mapping[str, object]:
    return {"value": value}


def _deserialize(payload: Mapping[str, object]) -> str:
    value = payload["value"]
    assert isinstance(value, str)
    return value


def test_configuration_is_explicit_and_validates_postgresql_url() -> None:
    configuration = PostgreSQLConfiguration(
        database_url=SecretStr("postgresql+psycopg://user:password@host/database")
    )

    assert configuration.url().startswith("postgresql+")
    assert "password" not in str(configuration)
    with pytest.raises(ValidationError):
        PostgreSQLConfiguration(database_url=SecretStr("sqlite:///local.db"))


def test_storage_uses_injected_repository_without_sqlalchemy() -> None:
    repository = FakeDocumentRepository()
    storage = PostgreSQLStorage(
        "registry", repository, serialize=_serialize, deserialize=_deserialize
    )

    storage.put("two", "second")
    storage.put("one", "first")

    assert storage.get("one") == "first"
    assert storage.list() == ("first", "second")
    assert storage.remove("two") == "second"
    with pytest.raises(ValueError, match="Duplicate"):
        storage.put("one", "duplicate")

    storage.close()
    storage.close()
    assert repository.closed is True
    with pytest.raises(PostgreSQLPersistenceError, match="closed"):
        storage.list()


def test_production_factory_reports_missing_optional_dependency() -> None:
    configuration = PostgreSQLConfiguration(
        database_url=SecretStr("postgresql+psycopg://user:password@host/database")
    )

    with pytest.raises(PostgreSQLDependencyError, match="SQLAlchemy"):
        PostgreSQLStorage.from_configuration(
            "registry", configuration, serialize=_serialize, deserialize=_deserialize
        )
