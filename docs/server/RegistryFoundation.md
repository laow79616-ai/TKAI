# Marketplace Server Registry Foundation

## Scope

`server.registry` is the Marketplace Server V6 Registry domain reference
implementation. It is offline-only and pure memory: it does not start an HTTP
server, access a network, use a database, write a filesystem, manage artifacts,
or run background workers.

## Architecture

```
ReferenceRegistryService
        ↓
 RegistryStorage protocol
        ↓
ReferenceRegistryStorage
```

Dependencies are explicit. A service may receive a caller-provided
`RegistryStorage`; otherwise it creates only its own local
`ReferenceRegistryStorage`.

## Immutable models

The domain exposes `RegistryId`, `RegistryCoordinate`, `RegistryMetadata`,
`RegistryDescriptor`, `RegistryEntry`, `RegistryEvent`, `RegistryStatistics`,
and `RegistrySnapshot`. They are frozen dataclasses. Metadata is defensively
copied and snapshots use tuples in stable identifier order. The `to_dict()`
helpers produce JSON-ready representations.

Registry entries use descriptive states only: `active`, `deprecated`,
`withdrawn`, and `deleted`. Deletion never removes an artifact or modifies an
external installation.

## Reference service

`ReferenceRegistryService` supports local `create`, `update`, `deprecate`,
`withdraw`, `restore`, `delete`, `get`, `list`, `search`, `snapshot`,
`statistics`, `events`, `clear`, and idempotent `close` operations.

Events are local immutable records with monotonically increasing sequences:
`created`, `updated`, `deprecated`, `withdrawn`, `deleted`, `restored`,
`snapshot`, and `closed`. They do not use timestamps for ordering and are not
published through an event bus.

## Search

The reference service offers deterministic in-memory filtering and sorting only.
It is not a remote Registry, indexing service, or search engine.

## Limitations

This foundation intentionally excludes HTTP APIs, remote Registry access,
authentication, artifact upload/download, database persistence, filesystem
storage, package installation, message queues, and background processing.
