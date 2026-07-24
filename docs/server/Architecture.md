# Marketplace Server V6 Architecture

Marketplace Server is a separate, reference-only product layer. Its planned
boundaries are Server → REST API contracts → application services → domain
models → storage protocols → infrastructure. Sprint-1 implements only
immutable contracts and local reference services; it starts no server, network,
database, or background worker.

## Registry Foundation

Sprint-2 adds an isolated, reference-only Registry domain under
`server.registry`. It layers immutable Registry models over a `RegistryStorage`
protocol, a thread-safe `ReferenceRegistryStorage`, and an explicitly injected
`ReferenceRegistryService`. The foundation records deterministic sequence-based
events and performs no HTTP, network, filesystem, database, artifact, or
background-worker activity.

## Publisher Foundation

Sprint-3 adds an isolated, reference-only Publisher domain under
`server.publisher`. It uses immutable Publisher contracts, an explicit
`PublisherStorage` protocol, thread-safe `ReferencePublisherStorage`, and an
injected `ReferencePublisherService`. It is independent of both
`server.registry` and `marketplace.publisher`, and introduces no account,
authentication, authorization, HTTP, network, database, artifact, or worker
behavior.

## Package Foundation

Sprint-4 adds an isolated, reference-only Package domain under
`server.package`. It uses immutable Package contracts, an explicit
`PackageStorage` protocol, thread-safe `ReferencePackageStorage`, and an
injected `ReferencePackageService`. It is independent of Server Registry,
Server Publisher, and `marketplace.package_catalog`, with no HTTP, network,
database, artifact, account, or worker behavior.

## Version Foundation

Sprint-5 adds an isolated, reference-only Version domain under
`server.version`. It uses immutable Version contracts, an explicit
`VersionStorage` protocol, thread-safe `ReferenceVersionStorage`, and an
injected `ReferenceVersionService`. It retains Package and Publisher references
as explicit strings and does not import or access Registry, Publisher, or
Package services.

## Search Foundation

Sprint-6 adds an isolated, reference-only unified query domain under
`server.search`. It layers immutable Search models over an explicit
`SearchStorage` protocol and a thread-safe `ReferenceSearchStorage`. It accepts
only caller-supplied local entries and never builds an index, uses a search
engine, accesses a database, network, or HTTP service, or mutates other domains.

## Statistics Foundation

Sprint-7 adds an isolated, reference-only Statistics domain under
`server.statistics`. It uses immutable caller-supplied sources, metrics, and
records with an explicit `StatisticsStorage` protocol and a thread-safe
`ReferenceStatisticsStorage`. Source types are descriptive only: the service
does not discover, query, or collect from Registry, Publisher, Package,
Version, Search, Release, or Health. It provides deterministic local queries,
on-demand aggregation, immutable events, counters, and snapshots without an
exporter, collector, HTTP service, database, network, background worker, or
global state.
