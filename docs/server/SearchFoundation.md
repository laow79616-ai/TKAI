# Marketplace Server Search Foundation

## Purpose

`server.search` provides a unified query model for caller-supplied local Search
entries. It is **Reference Only**, **Offline Only**, and purely in memory. It
is not a search engine, database, or HTTP service.

## Architecture and boundary

```
ReferenceSearchService
        ↓
   SearchStorage protocol
        ↓
ReferenceSearchStorage
```

The domain is independent of `marketplace.search`. It neither imports nor
mutates Registry, Publisher, Package, or Version foundations. Reference entries
are supplied explicitly to `ReferenceSearchStorage`.

## Models and semantics

Immutable models include `SearchQuery`, `SearchFilter`, `SearchSort`,
`SearchResult`, `SearchEntry`, `SearchPage`, `SearchStatistics`,
`SearchSnapshot`, and `SearchEvent`. Targets are descriptive values:
registry, publisher, package, and version. Metadata is defensively copied;
entries, pages, results, and snapshots are deterministic and JSON-ready.

Unified local filtering supports target, keyword, publisher, package, category,
tag, version, and status. Sorts are relevance (a descriptive lexical score),
name, and identifier. Empty keywords select every matching injected entry.

## Storage, service, and events

`SearchStorage` exposes search, suggest, snapshot, statistics, clear, and close.
`ReferenceSearchStorage` is thread-safe, isolated per instance, and uses only
the supplied in-memory entries. It starts no worker and builds no index.

`ReferenceSearchService` works only through the storage protocol. It records
immutable sequence events for searched, suggested, cleared, and closed actions.
Events have no timestamp or EventBus publication. Statistics count queries,
suggestions, current target kinds, accumulated returned results, and closed
state. Snapshots preserve the most recent result entries, events, statistics,
and close state.

## Lifecycle and failure isolation

Clear removes entries only from that storage instance and resets its latest
result snapshot. Close is idempotent; final snapshots and statistics remain
readable, while new searches, suggestions, and clears fail. Rejected or closed
operations do not affect another instance.

## Explicit non-goals and limitations

There is no HTTP, GraphQL, Elasticsearch, OpenSearch, Solr, Lucene, database,
Redis, network, authentication, authorization, filesystem storage, queue, or
background worker. This foundation cannot discover, crawl, index, or mutate
other Server domains.

The next planned boundary is the Server Statistics Foundation.
