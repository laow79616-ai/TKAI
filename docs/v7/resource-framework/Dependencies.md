# Dependencies

Dependencies identify another registered resource, an optional exact version,
and whether the edge is optional. Validation checks missing resources, version
compatibility, constraints, tenant/workspace isolation, and circular graphs.

Planning produces a deterministic dependency-first ordering. The ordering is
advisory metadata and does not initialize any dependency.
