# Enterprise AI Governance Architecture

The governance platform is a dependency-light domain package integrated with
the existing optional FastAPI host, React dashboard, packaging, metrics, and
release validation. `EnterpriseAIGovernancePlatform` owns in-memory scoped
stores for policies, risks, framework mappings, approvals, controls, governed
resources, incidents, exceptions, and immutable evidence references.

Every operation receives an explicit tenant, workspace, and actor scope.
Authorization is checked before reads or mutations, and fetched objects are
validated against tenant and workspace boundaries. The API adapter exposes
`/governance/*`; it does not make FastAPI a core dependency.

The initial storage implementation is process-local and intended as a stable
service contract. Durable adapters can implement equivalent behavior while
preserving scope validation, immutable evidence references, redaction, and
bounded exports.
