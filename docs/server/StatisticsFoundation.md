# Marketplace Server Statistics Foundation

## Purpose

`server.statistics` is a **Reference Only**, **Offline Only** Statistics
foundation for caller-supplied numeric records. It is isolated from every
other Server domain: Registry, Publisher, Package, Version, Search, Release,
and Health are represented only by the descriptive `StatisticsSourceType`
value selected by the caller. No service is discovered or queried
automatically.

## Architecture

```
ReferenceStatisticsService
        ↓
 StatisticsStorage protocol
        ↓
ReferenceStatisticsStorage
```

All dependencies are explicit. The pure-memory storage is per instance,
thread-safe, deterministic, and starts no worker.

## Models and validation

`StatisticsSource`, `StatisticsMetric`, `StatisticsRecord`,
`StatisticsDimensions`, and `StatisticsValue` are immutable and JSON-safe.
Supported source types are registry, publisher, package, version, search,
release, health, and custom. Metrics are descriptive counter, gauge,
distribution, or summary types.

Values accept only finite `int` and `float` scalars, or a non-empty tuple of
such values. Booleans, NaN, infinity, mappings, strings, and arbitrary values
are rejected. Dimensions are immutable string-to-string mappings. Metadata is
defensively copied and must never contain credentials.

## Storage and lifecycle

`StatisticsStorage` supports source registration, update, archive, restore,
lookup, listing, source existence checks, single and batch record writes,
record lookup, query, on-demand summary, counters, events, snapshots, clear,
and close.

Source identifiers and record identifiers are unique. A record is accepted
only for an active source. Archive and restore are idempotent at the service
boundary. `record_many` validates the entire batch before mutation, so a
duplicate, missing source, or archived source cannot create a partial batch.
Clear removes sources and records while preserving the monotonic event
sequence. Close is idempotent; final counters, events, and snapshots remain
readable, while mutations and normal queries fail explicitly.

## Query and aggregation

`StatisticsQuery` provides deterministic filters for source, source type,
metric name/type, dimensions, source status, and record identifier. Sorting is
record id, source id, metric name, scalar value, or explicit record sequence;
pagination is bounded and caller-controlled.

`summarize` calculates count, sum, minimum, maximum, and average on demand.
It can group compatible scalar records by source, source type, metric, or a
dimension key. Mixed metric names or types, distributions, and invalid
dimension grouping raise `StatisticsAggregationError`; an empty match returns
an empty summary.

## Events, snapshots, and isolation

Events use stable increasing sequence numbers rather than timestamps. They
cover registration, update, archive, restore, writes, clear, and close. A
`StatisticsSnapshot` contains immutable ordered sources, records, events,
fresh counters, and closed state. Failed writes do not alter sources, records,
events, counters, or other service instances.

## Explicit non-goals

This foundation has no HTTP server, database, Redis, Prometheus,
OpenTelemetry, exporter, collector, automatic cross-domain collection,
background worker, scheduler, network, authentication, authorization,
filesystem storage, queue, or global singleton. It does not collect system
metrics and does not implement a Server Sprint-8 feature.
