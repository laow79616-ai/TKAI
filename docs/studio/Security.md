# Studio Security

Studio stores model profile identifiers and non-secret parameters only.
Credentials stay in the Enterprise secret provider. APIs must apply existing
authentication, tenant isolation, RBAC, audit, rate-limit, and validation
middleware. Imported bundles receive new local identities and are validated
before use. Attachments are metadata references; scanning and binary access are
storage-policy responsibilities.
