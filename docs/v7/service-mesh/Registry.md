# Registry and Discovery

`ServiceRegistry` provides thread-safe registration, lookup, sorted listing,
filtered discovery, metadata indexes, dependency graphs, validation, health,
metrics, and audit projections.

Indexes cover category, owner, lifecycle status, and interface. Registration is
explicit and rejects duplicate service IDs. Dependency resolution validates
required services, semantic version ranges, required interfaces, capability
grants, and circular dependencies before startup.
