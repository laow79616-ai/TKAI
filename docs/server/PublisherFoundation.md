# Marketplace Server Publisher Foundation

## Purpose

`server.publisher` is the Marketplace Server V6 Publisher domain foundation.
It supplies immutable contracts and a pure-memory reference implementation for
local tests and examples. It is **Reference Only** and **Offline Only**.

## Architecture and module boundary

```
ReferencePublisherService
        ↓
 PublisherStorage protocol
        ↓
ReferencePublisherStorage
```

This Server domain is independent of `marketplace.publisher`. It has no hidden
singleton, does not modify `server.registry`, and accepts storage dependencies
explicitly.

## Models

Immutable models include `PublisherId`, `PublisherRecord`,
`PublisherDescriptor`, `PublisherProfile`, `PublisherOrganization`,
`PublisherMetadata`, `PublisherCapability`, `PublisherEvent`,
`PublisherStatistics`, and `PublisherSnapshot`. Metadata is defensively copied;
snapshots use tuples and stable Publisher-id ordering. `to_dict()` produces
JSON-ready representations.

Levels are descriptive: `community`, `verified`, `official`, and `enterprise`.
Statuses are descriptive lifecycle states: `active`, `suspended`,
`deprecated`, and `deleted`. They do not grant permissions or alter external
accounts, packages, Registry records, or releases.

## Capabilities and storage

Capabilities such as `publish_package`, `manage_versions`, `manage_releases`,
`access_statistics`, and `enterprise_distribution` are caller-supplied labels.
They are not authorization, verification, or Trust decisions.

`PublisherStorage` is a protocol for create, update, lifecycle changes,
capability changes, lookup, deterministic search, snapshots, statistics, clear,
and close. `ReferencePublisherStorage` is thread-safe, in-memory, isolated per
instance, and has no database or filesystem implementation.

## Lifecycle, search, and events

The reference service allows `active → suspended/deprecated/deleted`,
`suspended → active/deprecated/deleted`, and `deprecated → active/deleted`.
Repeated operations at their target state are idempotent and add no duplicate
event. Deleted records cannot be restored or modified.

Search uses `PublisherQuery`, `PublisherFilter`, and `PublisherSort` for local
deterministic filters by identifier, name, organization, level, status,
capability, and keyword. An empty query lists all current local records.

Events are immutable and sequence-ordered without timestamps: `created`,
`updated`, `suspended`, `restored`, `deprecated`, `deleted`,
`capability_added`, `capability_removed`, `cleared`, and `closed`. No EventBus
or consumer is started.

Statistics are computed fresh from current records. Snapshots contain records,
events, statistics, and the closed state. Closing is idempotent: write and clear
operations fail afterwards, while final snapshots, statistics, and events stay
readable.

## Thread safety and failure isolation

Each reference storage and service has its own lock and memory state. A rejected
operation leaves prior records and historical snapshots unchanged. The
implementation creates no background thread, task, or network connection.

## Compatibility and explicit non-goals

The foundation leaves Server Architecture and Server Registry foundations
unchanged. It does not modify `marketplace.publisher`, Marketplace public APIs,
Runtime, SDK, Studio, Enterprise, or Cloud.

Non-goals: HTTP, databases, Redis, authentication, authorization, real
verification, account management, Registry mutation, artifact upload/download,
filesystem storage, message queues, and background workers.

## Known limitations and next boundary

This is a local reference domain, not a remote Publisher account service. The
next planned boundary is the Server Package Foundation; it must remain separate
from this Publisher domain.
