# V7 Unified Resource Management Framework

The framework is an advisory metadata plane under
`tkai.v7.resource_framework`. Immutable contracts describe resources while the
registry, catalog, discovery, planner, capacity, reservation, dependency,
lifecycle, recovery, security, observability, dashboard, and API projections
coordinate metadata in memory.

It deliberately contains no runtime allocator or executor. A plan never starts
a browser, account, proxy, device, worker, workflow, TikTok action, or other
resource. Existing V6 services are not imported or changed.

The catalog includes TKAI's built-in resource types and accepts additional
`ResourceTypeContract` instances. The framework is deterministic, bounded, and
reference-only at reservation and recovery boundaries.
