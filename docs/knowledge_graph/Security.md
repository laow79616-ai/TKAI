# Security

Every read and mutation requires an immutable tenant/workspace/actor scope and
an RBAC permission. Cross-scope access is denied. Metadata and structured
properties reject secret-like keys recursively. Schema validation precedes
writes, provenance requires evidence, and security-relevant operations produce
an audit entry.
