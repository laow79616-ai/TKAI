# Registry

`CapabilityRegistry` provides registration, lookup, discovery, filtering, and
indexes for category, owner, status, and tag. Duplicate IDs are rejected.
Dependency edges are exposed by `DependencyGraph`, which detects cycles and
returns deterministic dependency-first load order.

`GLOBAL_REGISTRY` is available for application-wide use. Tests and isolated
runtimes should construct their own registry.
