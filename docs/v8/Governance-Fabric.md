# V8 Governance Fabric

A governance profile identifies an owner and version and references frameworks,
policies, constraints, runtime boundaries, reviews, approvals, compatibility,
health, metrics, audit entries, and arbitrary secret-filtered metadata.

The policy fabric accepts three explicit sources: `v6_governance`,
`v7_frameworks`, and `v8_frameworks`. Aggregation copies identifiers and
metadata into a local immutable projection. It never imports, starts, changes,
or stops a referenced module.

Supported runtime boundary metadata covers tenant, workspace, capability,
framework, module, extension, and configuration isolation. Boundaries are
descriptive and are not enforcement mechanisms.
