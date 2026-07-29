# Security

All scoped artifacts use exact tenant, workspace, and namespace isolation.
Existing RBAC remains authoritative at the server boundary. Metadata rejects
secret-like keys and nested or unbounded values. Audit records are structured
and secret-filtered. The feature adds no credentials, network clients, or new
write API.
