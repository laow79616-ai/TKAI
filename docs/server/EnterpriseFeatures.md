# Enterprise Features Foundation

Enterprise features are explicit, offline reference services: multi-user directory, organization/team relationships, deny-by-default RBAC, API key lifecycle, append-only audit, snapshots, and deterministic local storage. IDs and timestamps are caller supplied. Existing single-administrator authentication and all existing resource APIs remain compatible.

`ReferenceEnterpriseService` accepts injected storage, password hasher, and API-secret factory. It never accesses a database session. PostgreSQL document storage remains an optional adapter boundary; no existing migration or storage behavior changes.

## Security

Passwords use standard-library PBKDF2 hashes and are not included in models, snapshots, logs, errors, or audit records. API key plaintext is returned exactly once at creation; storage retains only a digest. Audit metadata is immutable and explicit.

## Limitations

This is a reference-only foundation. Enterprise HTTP resource routers and persistent PostgreSQL adapters remain deployment integrations; no OAuth, SAML, LDAP, SCIM, billing, cloud IAM, or automatic provisioning is included.
