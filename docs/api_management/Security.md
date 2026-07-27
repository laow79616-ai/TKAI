# Security

Tenant/workspace isolation and RBAC are mandatory. Credentials are references,
support rotation and revocation, and are never resolved or logged. Gateway
payloads and policy values are bounded. Transformations are declarative only,
and audit metadata strips secret-named fields.
