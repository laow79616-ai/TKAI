"""Optional persistence adapters for Marketplace Server deployments."""

from .postgresql import (
    DocumentRepository,
    PersistedDocument,
    PostgreSQLConfiguration,
    PostgreSQLConfigurationError,
    PostgreSQLDependencyError,
    PostgreSQLPersistenceError,
    PostgreSQLSessionManager,
    PostgreSQLStorage,
    SQLAlchemyDocumentRepository,
)

__all__ = (
    "DocumentRepository",
    "PersistedDocument",
    "PostgreSQLConfiguration",
    "PostgreSQLConfigurationError",
    "PostgreSQLDependencyError",
    "PostgreSQLPersistenceError",
    "PostgreSQLSessionManager",
    "PostgreSQLStorage",
    "SQLAlchemyDocumentRepository",
)
