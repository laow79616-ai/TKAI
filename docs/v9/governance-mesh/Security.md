# Security

Governance reads are compatible with RBAC roles and enforce tenant and
workspace scope equality. Secret-like metadata keys, including tokens,
passwords, API keys, and credentials, are redacted from projections and
structured observability metadata.

The mesh grants no runtime capability and cannot authorize execution.
