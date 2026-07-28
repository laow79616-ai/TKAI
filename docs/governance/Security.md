# Security

All governance access validates RBAC permission plus explicit tenant and
workspace isolation. Evidence is append-only by identifier and carries a
checksum and external audit reference. API responses and reports redact
recognized secret, token, password, API-key, and credential fields.

Exports are size-bounded. Runtime integrations must validate permissions at
the execution boundary and must store secret references rather than secret
values. Persistent implementations should use append-only audit storage and
database-level tenant filters in addition to service checks.
