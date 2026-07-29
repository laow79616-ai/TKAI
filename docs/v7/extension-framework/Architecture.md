# V7 Unified Extension & Plugin Framework

The framework is an internal, bounded metadata control plane under
`tkai.v7.extension_framework`. Immutable contracts feed a local in-memory
registry, indexes, validators, compatibility checks, dependency resolution,
health, metrics, tracing hooks, audit records, GET-only API projections, and a
read-only dashboard.

Static discovery accepts already-constructed manifests. It does not scan
remote registries, import modules, call entry points, evaluate expressions,
download packages, install artifacts, or execute extension code. The sandbox
is descriptive metadata only. Existing V6 plugin and TikTok paths are not
replaced or modified.

Every lookup is bounded and exact-scope filtered. Extension and plugin records
are isolated by tenant, workspace, and namespace. Registry indexes support
metadata text search, capability lookup, dependency lookup, and ID lookup.
