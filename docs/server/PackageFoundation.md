# Marketplace Server Package Foundation

## Purpose

`server.package` is the Marketplace Server V6 Package domain foundation. It
contains immutable contracts and a pure-memory reference service for local
tests and examples. It is **Reference Only**, **Offline Only**, and has no
artifact behavior.

## Architecture and boundary

```
ReferencePackageService
        ↓
  PackageStorage protocol
        ↓
ReferencePackageStorage
```

The Server Package domain is distinct from `marketplace.package_catalog`. It
does not read or mutate Server Registry or Publisher domains; all dependencies
are explicit local storage contracts.

## Models

`PackageId`, `PackageDescriptor`, `PackageManifest`, `PackageMetadata`,
`PackageCategory`, `PackageTag`, `PackageVersionRef`, `PackageRecord`,
`PackageEvent`, `PackageStatistics`, and `PackageSnapshot` are frozen models.
Metadata is defensively copied; collections have stable order in snapshots and
JSON-ready `to_dict()` representations.

Categories are descriptive: provider, workflow, tool, plugin, memory, template,
and extension. Package states are descriptive only: active, deprecated,
withdrawn, and deleted. They do not download, install, remove, or resolve an
artifact.

## Storage, service, and lifecycle

`PackageStorage` defines explicit create, update, lifecycle, lookup, search,
snapshot, statistics, event, clear, and close operations.
`ReferencePackageStorage` is thread-safe, isolated per instance, and keeps data
only in memory. `ReferencePackageService` works solely through this protocol;
it does not access Registry or Publisher services.

The local lifecycle supports active to withdrawn/deprecated/deleted, withdrawn
to active/deprecated/deleted, and deprecated to active/deleted. Repeat calls at
the target state are idempotent and do not emit extra events. Deleted records
cannot be restored or updated.

## Search, events, statistics, and snapshots

`PackageQuery`, `PackageFilter`, and `PackageSort` offer deterministic local
filtering by publisher, category, tag, version, status, and keyword. An empty
query returns all local Package records in Package-id order.

Events are immutable, sequence-ordered records: created, updated, deprecated,
withdrawn, deleted, restored, and closed. No timestamps determine order, and no
EventBus or background consumer is used.

Statistics are calculated from current local records and count packages, states,
categories, versions, and tags. Snapshots contain immutable Package records,
events, statistics, and close state. Close is idempotent; final snapshots,
events, and statistics remain readable while new operations fail.

## Explicit non-goals and limitations

This foundation has no HTTP, database, network, authentication, authorization,
PKI, signature verification, billing, artifact upload/download, filesystem
storage, message queues, or background workers. It is a local reference model,
not a production package repository or installation mechanism.

The next planned boundary is the Server Version Foundation.
