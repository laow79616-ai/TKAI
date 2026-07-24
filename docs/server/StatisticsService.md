# Statistics Service

The Sprint-1 top-level `server.ReferenceStatisticsService` remains the generic
architecture reference. The concrete Statistics Foundation is
`server.statistics.ReferenceStatisticsService`, backed by the explicit
`server.statistics.StatisticsStorage` protocol and
`ReferenceStatisticsStorage`.

The concrete service accepts only explicit local sources and records. It does
not collect from Registry, Publisher, Package, Version, Search, Release, or
Health automatically; source types are descriptive labels only. See
[StatisticsFoundation.md](StatisticsFoundation.md) for lifecycle, query,
aggregation, event, snapshot, and offline-only limitations.
