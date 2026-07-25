# PostgreSQL Persistence

## Scope

Marketplace Server can use an optional SQLAlchemy 2.x PostgreSQL document
repository when a deployment explicitly selects it. The existing reference
stores remain the default for tests and local examples. This module does not
change Marketplace Server Foundation services, HTTP contracts, or Dashboard
behavior.

## Architecture

`PostgreSQLStorage` implements the stable generic `ServerStorage` shape. It
receives a namespace plus explicit serializer and deserializer callables, then
stores JSON-safe payloads through `SQLAlchemyDocumentRepository`. The session
manager owns a lazily-created SQLAlchemy engine and closes it deterministically.

Configuration is explicit:

```python
from pydantic import SecretStr

from server.persistence.postgresql import PostgreSQLConfiguration, PostgreSQLStorage

configuration = PostgreSQLConfiguration(
    database_url=SecretStr("postgresql+psycopg://user:password@host/database")
)
storage = PostgreSQLStorage.from_configuration(
    "example",
    configuration,
    serialize=lambda value: {"value": value},
    deserialize=lambda payload: str(payload["value"]),
)
```

The module never reads database URLs or credentials from environment variables.
Applications select and inject storage explicitly. The current Foundation
services keep their existing domain-specific storage protocols unchanged;
deployments add a narrow adapter for a specific protocol rather than changing a
public service or API contract.

## Dependencies and Migration

Install the optional production dependencies with `pip install '.[postgres]'`.
They are not required for reference-only imports or tests.

The Alembic configuration is at `server/persistence/alembic.ini`; replace its
placeholder URL through secure deployment configuration before running:

```text
alembic -c server/persistence/alembic.ini upgrade head
```

Migration `0001_marketplace_documents` creates a namespace-scoped JSONB table
with a composite `(namespace, identifier)` primary key.

## Test Strategy

Repository contract tests use an offline in-memory fake. The optional live
PostgreSQL integration test runs only when `TKAI_POSTGRESQL_TEST_URL` is
provided and SQLAlchemy plus a PostgreSQL driver are installed. No development
test connects to a database by default.

## Limitations

- PostgreSQL is the only production storage target in this Sprint.
- No automatic environment configuration, database provisioning, or connection
  retries are provided.
- No API, dashboard, authentication, or Foundation contract is changed.
- This module persists JSON-safe document payloads only; no artifacts,
  downloads, queues, or background workers are introduced.
