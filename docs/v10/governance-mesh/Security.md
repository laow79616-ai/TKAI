# Security

Reads use existing scope authorization for tenant and workspace isolation plus
reader, auditor, or governance-metadata-reader RBAC roles. Safe metadata is
validated at registration and secret-like fields are redacted during
serialization. Registration activity is audit logged locally.
