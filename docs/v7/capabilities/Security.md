# Security

Capability authorization integrates with the V7 deny-by-default RBAC and
isolation policies. Validation rejects permissions absent from the supplied
grant set. Providers are explicit and do not receive registry internals.

Public projections omit configuration entirely. Metadata, health diagnostics,
and audit details recursively redact secret, password, token, API-key, and
credential-shaped fields. Lifecycle actions are appended to the audit log.
