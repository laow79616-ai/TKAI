# Security

The service mesh reuses V7 deny-by-default RBAC and capability isolation. It
adds explicit service-to-service grants. Registration and observability
projections recursively redact keys that indicate secrets, passwords, tokens,
API keys, or credentials.

The API is read-only. Providers and extensions are registered explicitly.
Audit records capture registration, validation, lifecycle, and route-selection
events without recording secret values.
