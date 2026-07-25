"""Optional PostgreSQL document storage compatible with ServerStorage.

SQLAlchemy and a PostgreSQL driver are loaded only when a production storage is
explicitly created. Importing Marketplace Server reference services stays fully
offline and dependency-free.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

T = TypeVar("T")


class PostgreSQLPersistenceError(RuntimeError):
    """Base persistence error that does not expose connection secrets."""


class PostgreSQLDependencyError(PostgreSQLPersistenceError):
    """Raised when optional SQLAlchemy or PostgreSQL driver dependencies are absent."""


class PostgreSQLConfigurationError(PostgreSQLPersistenceError):
    """Raised for an invalid explicit PostgreSQL configuration."""


class PostgreSQLConfiguration(BaseModel):
    """Explicit PostgreSQL configuration; it never reads an environment variable."""

    model_config = ConfigDict(frozen=True)

    database_url: SecretStr
    pool_size: int = Field(default=5, ge=1, le=32)
    echo: bool = False

    @field_validator("database_url")
    @classmethod
    def validate_postgresql_url(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(("postgresql://", "postgresql+")):
            raise ValueError("database_url must use a PostgreSQL SQLAlchemy URL.")
        return value

    def url(self) -> str:
        """Return the URL only to the session manager that opens a connection."""
        return self.database_url.get_secret_value()


@dataclass(frozen=True, slots=True)
class PersistedDocument:
    """Immutable JSON-safe record used by the PostgreSQL repository layer."""

    namespace: str
    identifier: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.namespace or not self.identifier:
            raise PostgreSQLConfigurationError(
                "Document namespace and identifier are required."
            )
        object.__setattr__(self, "payload", dict(self.payload))


class DocumentRepository(Protocol):
    """Repository boundary implemented by SQLAlchemy and test doubles."""

    def create(self, document: PersistedDocument) -> PersistedDocument: ...

    def get(self, namespace: str, identifier: str) -> PersistedDocument: ...

    def list(self, namespace: str) -> tuple[PersistedDocument, ...]: ...

    def remove(self, namespace: str, identifier: str) -> PersistedDocument: ...

    def close(self) -> None: ...


class PostgreSQLSessionManager:
    """Create SQLAlchemy engine and sessions only after explicit production setup."""

    def __init__(self, configuration: PostgreSQLConfiguration) -> None:
        self._configuration = configuration
        self._engine: Any | None = None
        self._session_factory: Any | None = None

    @property
    def engine(self) -> Any:
        """Lazily create a SQLAlchemy 2.x engine for the configured PostgreSQL URL."""
        if self._engine is None:
            sqlalchemy = _sqlalchemy()
            self._engine = sqlalchemy.create_engine(
                self._configuration.url(),
                echo=self._configuration.echo,
                pool_size=self._configuration.pool_size,
                future=True,
            )
        return self._engine

    @contextmanager
    def session(self) -> Iterator[Any]:
        """Yield one transactional session and ensure rollback on an exception."""
        if self._session_factory is None:
            orm = _sqlalchemy_orm()
            self._session_factory = orm.sessionmaker(bind=self.engine, future=True)
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Dispose opened connection resources idempotently."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


class SQLAlchemyDocumentRepository:
    """SQLAlchemy 2.x repository for namespace-scoped JSONB documents."""

    def __init__(self, sessions: PostgreSQLSessionManager) -> None:
        self._sessions = sessions
        self._model = orm_models().document

    def create(self, document: PersistedDocument) -> PersistedDocument:
        with self._sessions.session() as session:
            if (
                session.get(self._model, (document.namespace, document.identifier))
                is not None
            ):
                raise ValueError("Duplicate PostgreSQL storage key.")
            session.add(
                self._model(
                    namespace=document.namespace,
                    identifier=document.identifier,
                    payload=dict(document.payload),
                )
            )
        return document

    def get(self, namespace: str, identifier: str) -> PersistedDocument:
        with self._sessions.session() as session:
            row = session.get(self._model, (namespace, identifier))
            if row is None:
                raise KeyError(identifier)
            return PersistedDocument(row.namespace, row.identifier, row.payload)

    def list(self, namespace: str) -> tuple[PersistedDocument, ...]:
        sqlalchemy = _sqlalchemy()
        with self._sessions.session() as session:
            rows = session.scalars(
                sqlalchemy.select(self._model)
                .where(self._model.namespace == namespace)
                .order_by(self._model.identifier)
            ).all()
            return tuple(
                PersistedDocument(row.namespace, row.identifier, row.payload)
                for row in rows
            )

    def remove(self, namespace: str, identifier: str) -> PersistedDocument:
        with self._sessions.session() as session:
            row = session.get(self._model, (namespace, identifier))
            if row is None:
                raise KeyError(identifier)
            document = PersistedDocument(row.namespace, row.identifier, row.payload)
            session.delete(row)
            return document

    def close(self) -> None:
        self._sessions.close()


class PostgreSQLStorage(Generic[T]):
    """Production document storage with injected JSON conversion callables.

    The class satisfies the generic ``server.storage.ServerStorage`` shape and
    can therefore be selected through constructor injection without changing a
    service contract. Domain-specific adapters can compose this stable document
    repository without changing existing ReferenceStorage behavior.
    """

    def __init__(
        self,
        namespace: str,
        repository: DocumentRepository,
        *,
        serialize: Callable[[T], Mapping[str, object]],
        deserialize: Callable[[Mapping[str, object]], T],
    ) -> None:
        if not namespace:
            raise PostgreSQLConfigurationError("Storage namespace is required.")
        self._namespace = namespace
        self._repository = repository
        self._serialize = serialize
        self._deserialize = deserialize
        self._closed = False

    @classmethod
    def from_configuration(
        cls,
        namespace: str,
        configuration: PostgreSQLConfiguration,
        *,
        serialize: Callable[[T], Mapping[str, object]],
        deserialize: Callable[[Mapping[str, object]], T],
    ) -> PostgreSQLStorage[T]:
        """Build a production repository only when PostgreSQL is explicitly selected."""
        sessions = PostgreSQLSessionManager(configuration)
        return cls(
            namespace,
            SQLAlchemyDocumentRepository(sessions),
            serialize=serialize,
            deserialize=deserialize,
        )

    def get(self, identifier: str) -> T:
        self._ensure_open()
        return self._deserialize(
            self._repository.get(self._namespace, identifier).payload
        )

    def list(self) -> tuple[T, ...]:
        self._ensure_open()
        return tuple(
            self._deserialize(document.payload)
            for document in self._repository.list(self._namespace)
        )

    def put(self, identifier: str, item: T) -> T:
        self._ensure_open()
        self._repository.create(
            PersistedDocument(self._namespace, identifier, self._serialize(item))
        )
        return item

    def remove(self, identifier: str) -> T:
        self._ensure_open()
        return self._deserialize(
            self._repository.remove(self._namespace, identifier).payload
        )

    def close(self) -> None:
        if not self._closed:
            self._repository.close()
            self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise PostgreSQLPersistenceError("PostgreSQL storage is closed.")


@dataclass(frozen=True, slots=True)
class ORMModels:
    """SQLAlchemy declarative metadata and document model created on demand."""

    metadata: Any
    document: Any


def orm_models() -> ORMModels:
    """Build SQLAlchemy 2.x declarative models only when persistence is enabled."""
    sqlalchemy = _sqlalchemy()
    orm = _sqlalchemy_orm()
    base = orm.declarative_base()
    postgresql = import_module("sqlalchemy.dialects.postgresql")
    document = type(
        "Document",
        (base,),
        {
            "__tablename__": "marketplace_documents",
            "namespace": sqlalchemy.Column(sqlalchemy.String(128), primary_key=True),
            "identifier": sqlalchemy.Column(sqlalchemy.String(256), primary_key=True),
            "payload": sqlalchemy.Column(postgresql.JSONB, nullable=False),
        },
    )
    return ORMModels(base.metadata, document)


def _sqlalchemy() -> Any:
    try:
        return import_module("sqlalchemy")
    except ModuleNotFoundError as error:
        raise PostgreSQLDependencyError(
            "SQLAlchemy 2.x is required for PostgreSQL persistence. "
            "Install tkai[postgres]."
        ) from error


def _sqlalchemy_orm() -> Any:
    try:
        return import_module("sqlalchemy.orm")
    except ModuleNotFoundError as error:
        raise PostgreSQLDependencyError(
            "SQLAlchemy 2.x is required for PostgreSQL persistence. "
            "Install tkai[postgres]."
        ) from error
