# Health Service

The top-level `server.ReferenceHealthService` remains the original passive
architecture reference. The concrete Sprint-8 foundation is
`server.health.ReferenceHealthService`, backed by the explicit
`server.health.HealthStorage` protocol and `ReferenceHealthStorage`.

The concrete service stores only caller-provided checks and results. It does
not probe Registry, Publisher, Package, Version, Search, Statistics, network,
database, filesystem, process, or any external dependency. See
[HealthFoundation.md](HealthFoundation.md) for its immutable models,
lifecycle, events, snapshots, statistics, and strict offline-only boundaries.
