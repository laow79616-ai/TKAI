# Marketplace Server Version Foundation

## Purpose

`server.version` is the Marketplace Server V6 Version domain foundation. It
contains immutable contracts and a pure-memory reference service for local
tests and examples. It is **Reference Only** and **Offline Only**.

## Architecture and boundary

```
ReferenceVersionService
        ↓
  VersionStorage protocol
        ↓
ReferenceVersionStorage
```

Version records keep Package and Publisher relationships as explicit strings.
The domain does not import, read, or mutate Server Package, Publisher, or
Registry services and therefore introduces no dependency cycle.

## Models and lifecycle

`VersionId`, `VersionDescriptor`, `VersionManifest`, `VersionMetadata`,
`VersionRecord`, `VersionEvent`, `VersionStatistics`, and `VersionSnapshot` are
frozen and JSON-ready. Metadata is defensively copied and snapshots use stable
Version-id ordering.

Version labels are descriptive: stable, prerelease, beta, and alpha. Lifecycle
statuses are active, deprecated, withdrawn, and deleted. These fields do not
execute a release pipeline, inspect a package, or operate on an artifact.

`VersionStorage` defines explicit create, update, lifecycle, lookup, search,
snapshot, statistics, events, clear, and close operations.
`ReferenceVersionStorage` is thread-safe, pure memory, and isolated per
instance. `ReferenceVersionService` uses only that explicit protocol.

The reference lifecycle permits active to withdrawn/deprecated/deleted,
withdrawn to active/deprecated/deleted, and deprecated to active/deleted.
Repeated calls at the target state are idempotent and produce no duplicate
event. Deleted Version records cannot be restored or updated.

## Search, events, statistics, and snapshots

`VersionQuery`, `VersionFilter`, and `VersionSort` provide deterministic local
filtering by package, publisher, semantic version, status, label, and keyword.
An empty query lists all local Version records.

Events are immutable and sequence-ordered: created, updated, deprecated,
withdrawn, deleted, restored, and closed. No timestamp determines their order;
no EventBus or background consumer is created.

Statistics are calculated from current local records and count versions, status
states, and labels. Snapshots include immutable records, events, statistics,
and close state. Closing is idempotent; final snapshots, statistics, and events
remain readable while new operations fail.

## Explicit non-goals and limitations

This foundation has no HTTP, network, database, authentication, authorization,
signature verification, artifact upload/download, release pipeline, filesystem
storage, message queue, or background worker. It is a local reference model,
not a production release or artifact system.

The next planned boundary is the Server Search Foundation.
